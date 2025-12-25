from __future__ import annotations
from enum import Enum

import json
from typing import Union, Optional, Iterable, Iterator, List, Dict, Callable, Any, Tuple

import logging
import threading
import time
import os
import concurrent.futures

import grpc

import deephaven_enterprise.client.util
import deephaven_enterprise.proto.auth_pb2
import deephaven_enterprise.proto.controller_service_pb2_grpc
import deephaven_enterprise.proto.controller_common_pb2
import deephaven_enterprise.proto.controller_pb2
import deephaven_enterprise.proto.persistent_query_pb2
from deephaven_enterprise.client.generate_scheduling import GenerateScheduling

from deephaven_enterprise.client.auth import AuthClient

class SubState(Enum):
    NOT_SUBSCRIBED = 1
    SUBSCRIBING = 2
    SUBSCRIBED = 3

class RefreshThread(threading.Thread):
    def __init__(self,
                 controller_client: "ControllerClient",
                 period_millis: int = 10000):
        """
        This thread pings the controller every 10 seconds (default) to ensure that our cookie is valid and that we stay authenticated.
        :param controller_client:the controller client
        :param period_millis:how often to refresh in milliseconds
        """
        threading.Thread.__init__(self)
        self.stop = False
        self.daemon = True
        self.controller_client = controller_client
        self.period_millis = period_millis

    def run(self):
        while not self.stop and self.controller_client.cookie is not None:
            time.sleep(self.period_millis / 1000)
            try:
                self.controller_client.ping()
            except grpc.RpcError as e:
                if self.controller_client._should_retry_auth(e):
                    self.controller_client.log.info(
                        f'{self.controller_client.me}: Retryable Authentication Error in ping: {str(e)}')
                    self.controller_client._reauthenticate(
                        self.controller_client.rpc_timeout_secs)
                    continue
                if self.controller_client._should_retry(e):
                    self.controller_client.log.info(
                        f'{self.controller_client.me}: Retryable gRPC Error in ping: {str(e)}')
                    continue
                self.controller_client.log.error(f'{self.controller_client.me}: {e}')
                raise e


class ResponseThread(threading.Thread):
    def __init__(self,
                 controller_client: "ControllerClient",
                 iterator: Iterator[deephaven_enterprise.proto.controller_pb2.SubscribeResponse]):
        """
        This thread processes responses from the controller client's subscription method and calls the client's process method.

        :param controller_client: the controller client
        :param iterator: the result of the subscription
        """
        threading.Thread.__init__(self)
        self.daemon = True
        self.controller_client = controller_client
        self.iterator = iterator

    def run(self):
        try:
            for x in self.iterator:
                if self.controller_client.cookie is None:
                    return
                self.controller_client._process_one_event(x)
            self.controller_client.log.info(
                f'{self.controller_client.me}: Controller subscription completed.')
        except grpc.RpcError as e:
            if self.controller_client.cookie is None:
                # If we are logged out, we should not bother
                return
            if not self.controller_client._should_retry(e) and not self.controller_client._should_retry_auth(e):
                self.controller_client.log.error(f'{self.controller_client.me}: {e}')
                raise e
            self.controller_client.log.info(
                f'{self.controller_client.me}: Retryable Error in controller subscription handling: {str(e)}')

        # After our subscription ends, we should re-establish a subscription, unless we are closed
        # (meaning there is no cookie anymore)
        if self.controller_client.cookie is None:
            return

        self.controller_client.log.info(
            f'{self.controller_client.me}: restablishing subscription.')
        self.controller_client.subscribe()


class ControllerClient:
    """
    The ControllerClient connects to the Deephaven PersistentQueryController process.

    You may subscribe to the state of Persistent Queries as well as create and modify them.

    This class operates on the deephaven_enterprise.proto.persistent_query_pb2 structures.
    """

    rpc_timeout_secs: int
    subscription_timeout_secs: int
    query_map: Dict[int,
                    deephaven_enterprise.proto.persistent_query_pb2.PersistentQueryInfoMessage]
    query_map_version: int  # increases when query_map changes
    query_map_condition: threading.Condition  # protects and signals updates to query_map and query_map_version
    effective_user: str
    server_config: deephaven_enterprise.proto.controller_pb2.ControllerConfigurationMessage
    refresh_thread: RefreshThread
    response_thread: ResponseThread
    sub_state_cond: threading.Condition
    sub_state: SubState
    channel: grpc.Channel
    opened_channel: bool
    auth_client: AuthClient
    log: logging.Logger

    def __init__(self, host: str = None, port: int = None, rpc_timeout_seconds: int = 120, channel: grpc.Channel = None, client_name = None):
        """
        Connect to the persistent query controller.

        :param host: the host to connect to, requires port
        :param port: the port to connect to, requires host
        :param rpc_timeout_seconds: the timeout period in seconds for RPCs. Defaults to 120 if not provided.
        :param channel: an already configured gRPC channel (exclusive with host and port), it will not be closed by this client
        """
        self.cookie = None
        self.rpc_timeout_secs = rpc_timeout_seconds
        self.subscription_timeout_secs = rpc_timeout_seconds
        self.query_map = {}
        self.query_map_condition = threading.Condition()
        self.query_map_version = 0
        self.effective_user = None
        self.server_config = None
        self.refresh_thread = None
        self.sub_state_cond = threading.Condition()
        self.sub_state = SubState.NOT_SUBSCRIBED
        self.response_thread = None
        self.auth_client = None
        self.log = logging.getLogger("deephaven_enterprise.controller")
        (self.channel, self.me) = deephaven_enterprise.client.util.get_grpc_channel(
            channel, host, port)
        if client_name is not None:
            self.me += '_' + client_name
        self.opened_channel = channel is None
        self.clientID = deephaven_enterprise.client.util.make_client_id(
            self.me)

        self.stub = deephaven_enterprise.proto.controller_service_pb2_grpc.ControllerApiStub(
            self.channel)
        pingreq = deephaven_enterprise.proto.controller_common_pb2.PingRequest()
        self.stub.ping(pingreq, timeout=self.rpc_timeout_secs,
                       wait_for_ready=True)

    def set_auth_client(self, auth_client: AuthClient):
        """
        Authenticate using the given authentication client, which is stored as a local variable.  If a controller
        operation fails with a gRPC unauthenticated exception; then we attempt to use the authentication client to
        create a new controller session.  If the authentication client cannot produce tokens, then we cannot proceed.
        """
        self.auth_client = auth_client
        self._reauthenticate(self.rpc_timeout_secs)

    def _should_retry_auth(self, e: grpc.RpcError):
        """
        Is this gRPC Error something that should be retried after attempting to reauthenticate to the controller?
        """
        code = e.code()
        return self.auth_client is not None and code.name == "UNAUTHENTICATED"

    def _should_retry(self, e: grpc.RpcError):
        """
        Is this a transient error that we should retry?
        """
        code = e.code()
        if code.name == "UNAVAILABLE":
            return True
        if code.name == "INTERNAL":
            return "RST_STREAM" in e.details()
        return False

    def _reauthenticate(self, timeout: float):
        """
        Request a new token from our authentication client, and then uses it to authenticate to the controller
        """
        if self.auth_client is None:
            raise Exception("Cannot reauthenticate without an auth_client.")
        deadline = time.time() + timeout
        token = self.auth_client.get_token(
            "PersistentQueryController", timeout)
        timeout = deadline - time.time()
        self.authenticate(token, timeout)

    def authenticate(self, token: deephaven_enterprise.proto.auth_pb2.Token, timeout: float = None) -> None:
        """
        Authenticate to the controller using a token obtained from the AuthClient get_token method.

        :param token: the token to use for authentication, must have a service of "PersistentQueryController"
        """
        auth_request: deephaven_enterprise.proto.controller_pb2.AuthenticationRequest = deephaven_enterprise.proto.controller_pb2.AuthenticationRequest()
        auth_request.token.CopyFrom(token)
        auth_request.clientId.CopyFrom(self.clientID)
        auth_request.getConfiguration = True
        use_timeout: float = timeout if timeout is not None else self.rpc_timeout_secs
        auth_response: deephaven_enterprise.proto.controller_pb2.AuthenticationResponse = self.stub.authenticate(
            auth_request, timeout=use_timeout, wait_for_ready=True)
        if not auth_response.authenticated:
            msg = "Could not authenticate to controller."
            self.log.error(f'{self.me}: {msg}')
            raise Exception(msg)
        self.cookie = auth_response.cookie
        if self.refresh_thread is not None:
            self.refresh_thread.stop = True
        self.refresh_thread = RefreshThread(self)
        self.refresh_thread.start()
        self.effective_user = token.user_context.effectiveUser
        if auth_response.config:
            self.server_config = auth_response.config
        else:
            config_request = deephaven_enterprise.proto.controller_pb2.GetConfigurationRequest()
            config_request.cookie = self.cookie
            config_response = self.stub.getConfiguration(config_request,
                                                         timeout=self.rpc_timeout_secs, wait_for_ready=True)
            self.server_config = config_response.config

    def close(self) -> None:
        """
        Invalidate the clients cookie so that further operations do not take place with this client.
        """
        if self.cookie is not None:
            ivcr = deephaven_enterprise.proto.auth_pb2.InvalidateCookieRequest()
            ivcr.cookie = self.cookie
            self.cookie = None
            self.stub.invalidateCookie(
                ivcr, timeout=self.rpc_timeout_secs, wait_for_ready=True)
        if self.opened_channel:
            self.channel.close()

    def _do_subscription(self):
        if self.cookie is None:
            raise Exception("Should authenticate first.")

        self.log.info(f'{self.me}: Starting subscription.')
        subscription_request = deephaven_enterprise.proto.controller_pb2.SubscribeRequest()

        # We have no timeout, because the subscription must last "forever", we use a future executor to handle the
        # actual timeout of the gRPC call
        def _grpc_call():
            subscription = self.stub.subscribe(
                subscription_request, wait_for_ready=True, timeout=None)
            first_value = next(subscription)
            return (subscription, first_value)

        return self._req_with_authentication_retry_no_timeout(subscription_request, _grpc_call)

    def subscribe(self) -> None:
        """
        Subscribe to persistent query state, and wait for the initial query state snapshot to be populated.
        A successful call to authenticate should have happened before this call.

        After the subscription is complete, you may call the map method to retrieve the complete map or the get method
        to fetch a specific query by serial number.
        """

        snap_tstart = time.time()
        snap_nevents = 0
        with self.sub_state_cond:
            self.sub_state = SubState.SUBSCRIBING

        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        result_future: concurrent.futures.Future = executor.submit(
            self._do_subscription)
        snap_totsize = 0
        (subscription, first) = result_future.result(
            timeout=self.rpc_timeout_secs)
        snap_nevents += 1
        last: bool = self._process_one_event(first)
        snap_totsize += first.ByteSize()
        while not last:
            event = next(subscription)
            last = self._process_one_event(event)
            snap_totsize += event.ByteSize()
            snap_nevents += 1

        snap_tend = time.time()
        # Process response into our map
        self.response_thread = ResponseThread(self, subscription)
        self.response_thread.start()

        with self.sub_state_cond:
            self.sub_state = SubState.SUBSCRIBED
            self.sub_state_cond.notify_all()

        executor.shutdown()
        snap_dt = snap_tend - snap_tstart
        msg = f'Snapshot for initial subscription done, received {snap_nevents} events in {snap_dt:.2f} seconds'
        if snap_dt > 0:
            msg += f' ({snap_nevents/snap_dt:.2f} e/s), total size {snap_totsize:,} bytes'
            if snap_nevents > 0:
                msg += f' (average event size {snap_totsize/snap_nevents:.2f} bytes)'
        self.log.info(msg)

    def map(self) -> Dict[int, deephaven_enterprise.proto.persistent_query_pb2.PersistentQueryInfoMessage]:
        """
        Retrieve a copy of the current persistent query state.
        A successful call to subscribe should have happened before this call.

        :return: a map from serial number to persistent query info
        """
        deadline = time.time() + self.subscription_timeout_secs
        self._maybe_wait_for_subscription_secs(deadline)
        with self.query_map_condition:
            return self.query_map.copy()

    def map_and_version(self) -> Tuple[
            Dict[int, deephaven_enterprise.proto.persistent_query_pb2.PersistentQueryInfoMessage],
            int]:
        """
        Retrieve a copy of the current persistent query state alongside a version number for the overall map state.
        A successful call to subscribe should have happened before this call.
        Note the version number here has nothing to do with persistent query versions, but reflects instead
        a monotonically increasing version number for the current known state of all subscriptions.
        The version number will increase as update messages arriving from the controller make the map change.
        A successful call to subscribe should have happened before this call.

        :return: A tuple of two elements, a map from serial number to persistent query info, and a version number
        """
        deadline = time.time() + self.subscription_timeout_secs
        self._maybe_wait_for_subscription_secs(deadline)
        with self.query_map_condition:
            return (self.query_map.copy(), self.query_map_version)

    def maybe_wait_for_subscription(self, deadline_ns: int) -> None:
        self._maybe_wait_for_subscription_secs(deadline_ns / (1000.0 * 1000.0 * 1000.0))

    def _maybe_wait_for_subscription_secs(self, deadline: Optional[float] = None) -> None:
        with self.sub_state_cond:
            while True:
                if self.sub_state == SubState.NOT_SUBSCRIBED:
                    raise Exception("Should subscribe first.")
                if self.sub_state == SubState.SUBSCRIBED:
                    return
                if self.sub_state == SubState.SUBSCRIBING:
                    if deadline is not None:
                        now = time.time()
                        if now > deadline:
                            msg = "Deadline exceeded waiting for subscription to finish"
                            self.log.error(f'{self.me}: {msg}')
                            raise Exception(msg)
                        self.sub_state_cond.wait(deadline - now)
                    else:
                        self.sub_state_cond.wait()
                    continue
                # Should not happen unless code logic error
                msg = f'Internal error: sub_state={self.sub_state}'
                self.log.error(f'{self.me}: {msg}')
                raise Exception(msg)

    def get_serial_for_name(self, name: str, timeout_seconds: float = 0) -> int:
        """
        Retrieves the serial number for a given name.

        :param name:             a persistent query name
        :param timeout_seconds:  how long to wait for the query to appear if not already present in the subscription map
        """
        if self.response_thread is None:
            raise Exception("Should subscribe first.")
        deadline = time.time() + timeout_seconds
        with self.query_map_condition:
            while True:
                for serial in self.query_map:
                    qi: deephaven_enterprise.proto.persistent_query_pb2.PersistentQueryInfoMessage = self.query_map[
                        serial]
                    if qi.config.name == name:
                        return serial
                remaining = deadline - time.time()
                if remaining < 0:
                    raise Exception("No query found with name " + name)
                self.query_map_condition.wait(remaining)

    def wait_for_change(self, timeout_seconds: float):
        """
        Waits for a change in the query map to occur.
        See also wait_for_change_from_version.
        """
        with self.query_map_condition:
            self.query_map_condition.wait(timeout_seconds)

    def wait_for_change_from_version(self, map_version: int, timeout_seconds: float) -> bool:
        """
        Waits for a new version in the query map to occur

        :map_version: a version number reflecting the current known map version
        :param timeout_seconds: how long to wait in seconds
        :return: True if a newer version exists, False otherwise
        """
        deadline = time.time() + timeout_seconds
        with self.query_map_condition:
            while True:
                if self.query_map_version > map_version:
                    return True
                remaining = deadline - time.time()
                if remaining < 0:
                    return False
                self.query_map_condition.wait(remaining)

    def get(self, serial: int,
            timeout_seconds: float = 0) -> deephaven_enterprise.proto.persistent_query_pb2.PersistentQueryInfoMessage:
        """
        Get a query from the map.  If the query does not exist, throws a KeyError.
        A successful call to subscribe should have happened before this call.

        The timeout_seconds parameter can be specified to wait for the query to exist before failing with KeyError.
        This is useful when you have just created the query, know its serial, but the controller has not yet published
        the state to you.

        :param serial:
        :param timeout_seconds:
        :return: the PersistentQueryInfoMessage associated with the serial number
        """
        deadline = time.time() + timeout_seconds
        self._maybe_wait_for_subscription_secs(deadline)
        tries = 0
        last_error: Optional[KeyError] = None
        with self.query_map_condition:
            while True:
                try:
                    return self.query_map[serial]
                except KeyError as ke:
                    remaining = deadline - time.time()
                    if remaining < 0:
                        raise ke
                self.query_map_condition.wait(remaining)

    @staticmethod
    def status_name(status: deephaven_enterprise.proto.persistent_query_pb2.PersistentQueryStatusEnum):
        """
        Returns the name of the status enum from a PersistentQueryStateMessage.
        """
        return deephaven_enterprise.proto.persistent_query_pb2.PersistentQueryStatusEnum.Name(status)

    @staticmethod
    def is_running(status: deephaven_enterprise.proto.persistent_query_pb2.PersistentQueryStatusEnum) -> bool:
        """
        Is the status from the query info running?

        If not running and not terminal, then the query is in the initialization process.
        """
        return status == deephaven_enterprise.proto.persistent_query_pb2.PQS_RUNNING

    @staticmethod
    def is_completed(status: deephaven_enterprise.proto.persistent_query_pb2.PersistentQueryStatusEnum) -> bool:
        """
        Is the status from the query info Completed?

        If not running and not terminal, then the query is in the initialization process.
        """
        return status == deephaven_enterprise.proto.persistent_query_pb2.PQS_COMPLETED

    @staticmethod
    def is_terminal(status: deephaven_enterprise.proto.persistent_query_pb2.PersistentQueryStatusEnum) -> bool:
        """
        Is the status from the query info terminal?

        If not running and not terminal, then the query is in the initialization process.
        """
        return status == deephaven_enterprise.proto.persistent_query_pb2.PQS_ERROR or \
            status == deephaven_enterprise.proto.persistent_query_pb2.PQS_DISCONNECTED or \
            status == deephaven_enterprise.proto.persistent_query_pb2.PQS_STOPPED or \
            status == deephaven_enterprise.proto.persistent_query_pb2.PQS_FAILED or \
            status == deephaven_enterprise.proto.persistent_query_pb2.PQS_COMPLETED

    @staticmethod
    def is_status_uninitialized(status: deephaven_enterprise.proto.persistent_query_pb2.PersistentQueryStatusEnum) -> bool:
        """
        Is the status from the query info uninitialized?

        This is the case before a query is ever started.
        """
        return status == deephaven_enterprise.proto.persistent_query_pb2.PQS_UNSPECIFIED or \
            status == deephaven_enterprise.proto.persistent_query_pb2.PQS_UNINITIALIZED

    def _req_with_authentication_retry(self, request, timeout, method):
        """
        Perform the requested method with retries.

        :param request: the request that we'll be sending in method, the cookie for authentication is set on each try
        :param timeout: how long in seconds we have to complete the call
        :param method: the method to execute, must take a single parameter which is the number of seconds for the timeout
        """
        deadline = time.time() + timeout
        while True:
            request.cookie = self.cookie
            try:
                return method(timeout)
            except grpc.RpcError as e:
                timeout = deadline - time.time()
                if timeout > 0:
                    if self._should_retry_auth(e):
                        self.log.info(f'{self.me}: Retryable gRPC Authentication Error: {str(e)}')
                        self._reauthenticate(timeout)
                        continue
                    if self._should_retry(e):
                        self.log.info(f'{self.me}: Retryable gRPC Error: {str(e)}')
                        continue

                    deephaven_enterprise.client.util._maybe_reinterpret_and_raise(e)
                self.log.error(f'{self.me}: {e}')
                raise e

    def _req_with_authentication_retry_no_timeout(self, request, method):
        """
        Perform the requested method with retries, no timeout is provided to the method; the authentication call
        uses our standard timeout.  This is intended for use when we have an external thing managing timeouts (like
        for streaming RPCs).

        :param request: the request that we'll be sending in method, the cookie for authentication is set on each try
        :param method: the method to execute
        """
        while True:
            request.cookie = self.cookie
            try:
                return method()
            except grpc.RpcError as e:
                if self._should_retry_auth(e):
                    self.log.info(f'{self.me}: Retryable gRPC Authentication Error: {str(e)}')
                    self._reauthenticate(self.rpc_timeout_secs)
                    continue
                if self._should_retry(e):
                    self.log.info(f'{self.me}: Retryable gRPC Error: {str(e)}')
                    continue
                deephaven_enterprise.client.util._maybe_reinterpret_and_raise(e)
                self.log.error(f'{self.me}: {e}')
                raise e

    def add_query(self,
                  query_config: deephaven_enterprise.proto.persistent_query_pb2.PersistentQueryConfigMessage) -> int:
        """
        Add a persistent query.
        A successful call to authenticate should have happened before this call.

        :param query_config: the configuration of the query to add.
        :return: the serial number of the created query
        """
        if self.cookie is None:
            raise Exception("Should authenticate first.")
        aqreq = deephaven_enterprise.proto.controller_pb2.AddQueryRequest()
        aqreq.config.CopyFrom(query_config)

        aqresp: deephaven_enterprise.proto.controller_pb2.AddQueryResponse = \
            self._req_with_authentication_retry(
                aqreq,
                timeout=self.rpc_timeout_secs,
                method=lambda timeout: self.stub.addQuery(
                    aqreq, timeout, wait_for_ready=True))

        return aqresp.querySerial

    def modify_query(self,
                     query_config: deephaven_enterprise.proto.persistent_query_pb2.PersistentQueryConfigMessage,
                     do_restart: bool) -> None:
        """
        Modify a persistent query.
        A successful call to authenticate should have happened before this call.

        :param query_config: the configuration of the query to modify.
        :do_restart: whether to restart the modified query.
        """
        if self.cookie is None:
            raise Exception("Should authenticate first.")
        mqreq = deephaven_enterprise.proto.controller_pb2.ModifyQueryRequest()
        mqreq.config.CopyFrom(query_config)
        mqreq.doRestart = do_restart

        self._req_with_authentication_retry(
            mqreq,
            timeout=self.rpc_timeout_secs,
            method=lambda timeout: self.stub.modifyQuery(
                mqreq, timeout, wait_for_ready=True))

    def delete_query(self, serial: int) -> None:
        """
        Delete a query.
        A successful call to authenticate should have happened before this call.

        :param serial: the serial number to delete
        """
        if self.cookie is None:
            raise Exception("Should authenticate first.")
        remove_request: deephaven_enterprise.proto.controller_pb2.RemoveQueryRequest = \
            deephaven_enterprise.proto.controller_pb2.RemoveQueryRequest()
        remove_request.serial = serial

        self._req_with_authentication_retry(remove_request, self.rpc_timeout_secs,
                                            method=lambda timeout: self.stub.removeQuery(remove_request, timeout,
                                                                                         wait_for_ready=True))

    def restart_query(self, serials: Union[Iterable[int], int], timeout_seconds: int = None) -> None:
        """
        Restart one or more queries.
        A successful call to authenticate should have happened before this call.

        :param serials: a query serial number, or an iterable of serial numbers
        """
        if self.cookie is None:
            raise Exception("Should authenticate first.")
        restartreq = deephaven_enterprise.proto.controller_pb2.RestartQueryRequest()
        if isinstance(serials, int):
            restartreq.serials.append(serials)
        else:
            for serial in serials:
                restartreq.serials.append(serial)
        use_timeout: int = timeout_seconds if timeout_seconds is not None else self.rpc_timeout_secs
        self._req_with_authentication_retry(restartreq, use_timeout,
                                            lambda timeout: self.stub.restartQuery(restartreq, timeout, wait_for_ready=True))

    def start_and_wait(self, serial: int, timeout_seconds: int = 120) -> None:
        """
        Start the given query serial number; wait for the query to becoming running (or Completed).
        If the query fails, then raises an exception.

        :param serial: the serial to start
        :param timeout_seconds: how long to wait for the query to become running.
        """
        deadline = time.time() + timeout_seconds

        info = self.map()[serial]
        startLastUpdateNanos = None
        if info.state is not None:
            startLastUpdateNanos = info.state.lastUpdateNanos

        self.restart_query(serial, timeout_seconds=timeout_seconds)

        def is_restarted(maparg: Dict[int, deephaven_enterprise.proto.persistent_query_pb2.PersistentQueryInfoMessage],
                         serial=serial) -> \
                Tuple[bool, deephaven_enterprise.proto.persistent_query_pb2.PersistentQueryInfoMessag]:
            info = maparg[serial]
            if info.state is None:
                return (False, info)
            state = info.state
            if startLastUpdateNanos is not None and state.lastUpdateNanos == startLastUpdateNanos:
                return (False, info)
            status = info.state.status
            if self.is_running(status) or self.is_terminal(status):
                return (True, info)
            return (False, info)

        (ok, info) = self._wait_for_map_predicate(is_restarted, deadline - time.time())
        if ok:
            return

        state = info.state if info is not None else None

        raise Exception("Query (" + str(serial) + ", " +
                        info.config.name + ") is not stopped: " + str(state))

    def stop_query(self, serials: Union[Iterable[int], int], timeout_seconds: int = None) -> None:
        """
        Stop one or more queries.
        A successful call to authenticate should have happened before this call.

        :param serials: a query serial number, or an iterable of serial numbers
        """
        if self.cookie is None:
            raise Exception("Should authenticate first.")
        stopReq = deephaven_enterprise.proto.controller_pb2.StopQueryRequest()
        if isinstance(serials, int):
            stopReq.serials.append(serials)
        else:
            for serial in serials:
                stopReq.serials.append(serial)
        use_timeout: int = timeout_seconds if timeout_seconds is not None else self.rpc_timeout_secs

        self._req_with_authentication_retry(stopReq, use_timeout,
                                            lambda timeout: self.stub.stopQuery(stopReq, timeout, wait_for_ready=True))

    def stop_and_wait(self, serial: int, timeout_seconds: int = 120) -> None:
        """
        Stop the given query serial number; wait for the query to stop (be terminal).
        If the query does not stop in the given time, raise an exception.

        :param serial: the serial to start
        :param timeout_seconds: how long, to wait for the query to become running.
        """
        deadline = time.time() + timeout_seconds

        self.stop_query(serial, timeout_seconds=timeout_seconds)

        def is_stopped(maparg: Dict[int, deephaven_enterprise.proto.persistent_query_pb2.PersistentQueryInfoMessage],
                       serial=serial) -> \
                Tuple[bool, deephaven_enterprise.proto.persistent_query_pb2.PersistentQueryInfoMessag]:
            info = maparg[serial]
            state = info.state
            if state is None:
                return (True, info)
            status = info.state.status
            if self.is_terminal(status) or self.is_status_uninitialized(status):
                return (True, info)
            return (False, info)

        (ok, info) = self._wait_for_map_predicate(is_stopped, deadline - time.time())
        if ok:
            return
        state = None if info is None else info.state

        msg = f'Query ({str(serial)}, {info.config.name}) is not stopped: {str(state)}'
        self.log.error('{self.me}: {msg}')
        raise Exception(msg)

    def wait_for_state(self, state_function: Callable[[], (bool, Any)], timeout_seconds: float = None) -> (bool, Any):
        """
        Wait for a particular state transition in the controller map to occur.

        :param state_function: a function that returns a tuple.  The first element is True if the state transition
        occurred and False otherwise.  The second element is the current state which is then returned to the user.
        :param timeout_seconds: how long, to wait for the state transition to occur
        :return: a tuple.  The first element is True if the state_function returned True; or False if the timeout
        expired.  The second element is the return value of the state_function or None if the state_function returned False.
        """
        if timeout_seconds is None:
            timeout_seconds = self.rpc_timeout_secs
        deadline = time.time() + timeout_seconds
        remaining: int = 0  # always check at least once
        current_state = None
        while True:
            # Don't hold our lock/condition while invoking the callback.
            current_state = state_function()
            if current_state[0]:
                return current_state
            remaining: int = deadline - time.time()
            if remaining < 0:
                return current_state
            with self.query_map_condition:
                self.query_map_condition.wait(remaining)

    def _wait_for_map_predicate(self,
                                map_predicate: Callable[[Dict[int, deephaven_enterprise.proto.persistent_query_pb2.PersistentQueryInfoMessage]],
                                                        (bool, Any)],
                                timeout_seconds: float = None) -> bool:
        # map_predicate should be fast to evaluate, as it is invoked holding our query_map_condition lock.
        deadline: Optional[float] = None
        if timeout_seconds is not None:
            deadline = time.time() + timeout_seconds
        self._maybe_wait_for_subscription_secs(deadline)
        with self.query_map_condition:
            while True:
                found, state = map_predicate(self.query_map)
                if found:
                    return (True, state)
                if deadline is None:
                    self.query_map_condition.wait()
                else:
                    remaining = deadline - time.time()
                    if remaining < 0:
                        return (False, None)
                    self.query_map_condition.wait(remaining)

    def make_temporary_config(self, name: str, heap_size_gb: float,
                              server: str = None,
                              extra_jvm_args: List[str] = None,
                              extra_environment_vars: List[str] = None,
                              engine: str = "DeephavenCommunity",
                              auto_delete_timeout: Optional[int] = 600,
                              admin_groups: List[str] = None,
                              viewer_groups: List[str] = None) -> deephaven_enterprise.proto.persistent_query_pb2.PersistentQueryConfigMessage:
        """
        Create a configuration suitable for use as a temporary InteractiveConsole query.  The worker uses the default
        DeephavenCommunity engine.  This kind of query enables a client to use the controller to create workers for
        general use, in the same way Enterprise clients would have used the dispatcher.  For options that are not
        represented in the arguments, the returned PersistentQueryConfigMessage can be modified before adding it to
        the controller.

        :param name: the name of the persistent query.  Defaults to None, which means a name based on the current time is used
        :param heap_size_gb: the heap size of the worker
        :param server: the server to connect to. Defaults to None, which means the first available server
        :param extra_jvm_args: extra JVM arguments for starting the worker. Defaults to None.
        :param extra_environment_vars: extra Environment variables for the worker. Defaults to None.
        :param engine: which engine (worker kind) to use for the backend worker. Defaults to None, which means
               "DeephavenCommunity"
        :param auto_delete_timeout: after how many seconds should the query be automatically deleted after inactivity.
               Defaults to ten minutes.  If none, auto-delete is disabled.  If zero, the query is deleted immediately after a
               client connection is lost
        :param admin_groups: list of groups that may administer the query.  Defaults to None, which means only the
               current user may administer the query.
        :param viewer_groups: list of groups that may view the query.  Defaults to None, which means only the current
               user may view the query.
        :return: a configuration suitable for passing to add_query.
        """
        if extra_jvm_args is None:
            extra_jvm_args = []
        if extra_environment_vars is None:
            extra_environment_vars = []
        if self.effective_user is None:
            raise Exception(
                "Expect to be authenticated when creating temporary query configuration")
        config: deephaven_enterprise.proto.persistent_query_pb2.PersistentQueryConfigMessage = \
            deephaven_enterprise.proto.persistent_query_pb2.PersistentQueryConfigMessage()
        # Java Long.MIN_VALUE allows the controller to assign a serial number
        config.serial = -2 ** 63
        config.name = name
        config.version = 1
        config.owner = self.effective_user
        config.enabled = True
        config.heapSizeGb = heap_size_gb
        config.bufferPoolToHeapRatio = 0.25
        config.detailedGCLoggingEnabled = True

        if extra_jvm_args is not None:
            config.extraJvmArguments.extend(extra_jvm_args)
        if extra_environment_vars is not None:
            config.extraEnvironmentVariables.extend(extra_environment_vars)

        # config.classPathAdditions
        if server is not None:
            config.serverName = server
        else:
            config.serverName = self.server_config.dbServers[0].name

        if admin_groups is not None:
            config.adminGroups.extend(admin_groups)
        if viewer_groups is not None:
            config.viewerGroups.extend(viewer_groups)
        config.restartUsers = deephaven_enterprise.proto.persistent_query_pb2.RU_ADMIN

        config.scriptCode = ""

        config.scriptLanguage = "Python"
        config.configurationType = "InteractiveConsole"

        if auto_delete_timeout is not None:
            auto_delete_value = True;
            tsf = {
                "TerminationDelay": auto_delete_timeout * 1000,
            }
            config.typeSpecificFieldsJson = self.__encode_type_specific_fields(
                tsf)
        else:
            auto_delete_value = False;

        scheduling = GenerateScheduling.generate_temporary_scheduler(expiration_time_minutes=2880,
            queue_name="InteractiveConsoleTemporaryQueue",
            auto_delete=auto_delete_value)

        config.scheduling.extend(scheduling)

        # How long to wait for the query to initialize, without an initialization script the default of 60 seconds
        # should be safe on most installations.
        initialize_timeout_seconds: float = 60.0
        config.timeoutNanos = int(initialize_timeout_seconds * 1_000_000_000)

        config.jvmProfile = "Default"

        # config.kubernetesControl = None
        config.workerKind = engine

        return config

    @staticmethod
    def generate_disabled_scheduler():
        """
        Generates a scheduler array for a PQ that has scheduling disabled.
        """
        return GenerateScheduling.generate_disabled_scheduler()

    @staticmethod
    def __encode_type_specific_fields(tsf: Dict) -> str:
        """
        Encodes type specific fields from a Python dictionary into the JSON object that the controller expects.
        :param tsf: a Python dictionary with type specific fields
        :return: a JSON encoded string suitable for the controller
        """
        if tsf is None or len(tsf) == 0:
            return ""

        encoded = {}
        for (k, v) in tsf.items():
            if v is None:
                continue
            if isinstance(v, int):
                encoded[k] = {"type": "long", "value": str(v)}
            elif isinstance(v, bool):
                encoded[k] = {"type": "boolean",
                              "value": "true" if v else "false"}
            elif isinstance(v, str):
                encoded[k] = {"type": "string", "value": v}
            elif isinstance(v, float):
                encoded[k] = {"type": "double", "value": v}

        return json.dumps(encoded)

    def ping(self):
        """
        Ping the controller and refresh our cookie.
        :return: True if the ping was sent, False if we had no cookie
        """
        ping_request = deephaven_enterprise.proto.controller_common_pb2.PingRequest()
        cookie = self.cookie
        if cookie is None:
            return False

        ping_request.cookie = cookie
        self.stub.ping(
            ping_request, timeout=self.rpc_timeout_secs, wait_for_ready=True)
        return True

    def _process_one_event(self, event: deephaven_enterprise.proto.controller_pb2.SubscribeResponse):
        """
        Process a controller event.
        :param event: the event to process
        :return: True if this is the end of the initial subscription batch
        """
        batch_end: bool = event.event == deephaven_enterprise.proto.controller_pb2.SubscriptionEvent.SE_BATCH_END
        if event.event == deephaven_enterprise.proto.controller_pb2.SubscriptionEvent.SE_PUT or batch_end:
            serial = event.queryInfo.config.serial
            with self.query_map_condition:
                self.query_map[serial] = event.queryInfo
                self.query_map_version += 1
                self.query_map_condition.notify_all()
        elif event.event == deephaven_enterprise.proto.controller_pb2.SubscriptionEvent.SE_REMOVE:
            serial = event.querySerial
            if serial in self.query_map:
                with self.query_map_condition:
                    del self.query_map[serial]
                    self.query_map_version += 1
                    self.query_map_condition.notify_all()
            else:
                raise Exception("Unknown query: " + str(event))
        elif event.event == deephaven_enterprise.proto.controller_pb2.SubscriptionEvent.SE_CONFIG_UPDATE:
            self.server_config = event.config
        else:
            msg = f'Unexpected event: {str(event)}'
            self.log.error(f'{self.me}: msg')
            raise Exception(msg)
        return batch_end
