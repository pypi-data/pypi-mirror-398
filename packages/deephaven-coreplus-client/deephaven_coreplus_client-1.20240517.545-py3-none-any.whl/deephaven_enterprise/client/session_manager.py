from __future__ import annotations

import base64
import logging
from json import loads, dumps
import io
import time
import urllib.request
import urllib.parse
from datetime import datetime
from typing import Callable, Dict, Optional, List, Union

import grpc
import pydeephaven
from pydeephaven._table_ops import FetchTableOp
from pydeephaven.table import Table
from deephaven_enterprise.proto.persistent_query_pb2 import PersistentQueryConfigMessage, PersistentQueryInfoMessage
import deephaven_enterprise.client
from pydeephaven.dherror import DHError
from pydeephaven.ticket import Ticket

from deephaven_enterprise.client.auth import AuthClient
from deephaven_enterprise.client.controller import ControllerClient

from pydeephaven.session import SharedTicket
import importlib.util
import atexit

class SessionManager:
    """
    The SessionManager authenticates to the Deephaven Enterprise server and allows you to create sessions for DnD
    workers by either creating a new temporary Persistent Query or connecting to an existing Persistent Query.
    """
    config: Dict[str, str]
    json_connection_info: str
    auth_client: AuthClient
    controller_client: ControllerClient
    active_sessions: List["DndSession"]
    log: logging.Logger
    client_name: str
    owned_channels: List[grpc.Channel]

    def __init__(self, url: str = None, json: str = None, client_name: str = None, rpc_timeout_seconds: int = 120):
        """
        Create a SessionManager for the specified JSON, which may either be a string or a URL to download.
        The Deephaven server typically provides the JSON as "https://host:port/iris/connection.json".  Exactly one
        of url or json must be provided.

        The JSON must have the following parameters: auth_host, auth_port, controller_host, controller_port.  If the
        truststore_url is set, then a trust store PEM file is downloaded from the given URL.  If the
        override_authorities parameter is set then the authority used for the TLS connection to the authentication server
        is the value of the auth_authority parameter (or "authserver" if unspecified) and the TLS connection to the
        controller uses the value of the controller_authority parameter (or for backwards compatibility "authserver"
        if unspecified).

        :param url: a URL to get the JSON connection information from
        :param json: a JSON document containing connection information
        :client_name: a descriptive string identifying this client that will be used in the server for logging
        :rpc_timeout_seconds: the timeout period in seconds for RPCs. Defaults to 120 if not provided.
        """
        self.log = logging.getLogger("deephaven_enterprise.session_manager")
        in_worker: bool = False
        if url is not None:
            if json is not None:
                raise Exception("url and json are mutually exclusive")
            urllib.parse.urlparse(url)
            json = urllib.request.urlopen(url).read()
        elif json is None:
            try:
                import deephaven_enterprise.client_worker_auth
                # If we've gotten here, this means we are local to a worker so should generate our own connection.json and then authenticate with a delegate token
                json = deephaven_enterprise.client_worker_auth.get_connection_json()
                in_worker = True
            except ImportError:
                raise Exception("Must specify url or json")

        self.client_name = client_name
        self.config = loads(json)
        self.active_sessions = []
        self.owned_channels = []

        truststore_url: Optional[str] = self.config.get("truststore_url")
        if truststore_url is not None and truststore_url != "":
            self.truststore_pem = urllib.request.urlopen(truststore_url).read()
        else:
            self.truststore_pem = None

        self.auth_client = self.create_auth_client(rpc_timeout_seconds=rpc_timeout_seconds)
        self.controller_client = self.create_controller_client(rpc_timeout_seconds=rpc_timeout_seconds)

        if in_worker:
            deephaven_enterprise.client_worker_auth.delegate_authentication(
                self.auth_client)
            self.__init_controller()

        atexit.register(self.close)

    def create_auth_client(self, auth_host: str = None, rpc_timeout_seconds: int = 120) -> AuthClient:
        """
        Create the authentication client for this session manager.

        :param auth_host: the host to connect to, defaults to the first host in the JSON config's auth_host list
        :param rpc_timeout_seconds: the timeout period in seconds for RPCs. Defaults to 120 if not provided.
        :return: the authentication client
        """
        auth_port = self.config.get("auth_port")
        auth_host = self.config.get("auth_host")[0] if auth_host is None else auth_host

        auth_channel_options = []

        if self.config.get("authentication_service_config"):
            auth_channel_options.append(("grpc.enable_retries", 1))
            auth_channel_options.append(("grpc.service_config", SessionManager._clamp_retries(
                self.config.get("authentication_service_config"), self.log)))

        if self.truststore_pem is None:
            return AuthClient(
                auth_host, auth_port,
                channel_options=auth_channel_options, client_name=self.client_name)
        else:
            credentials = grpc.ssl_channel_credentials(
                root_certificates=self.truststore_pem)

            auth_target = auth_host + ":" + str(auth_port)
            if self.config.get("override_authorities"):
                authority: str = self.config.get("auth_authority") if self.config.get(
                    "auth_authority") else "authserver"
                auth_channel_options.append(
                    ('grpc.ssl_target_name_override', authority))

            auth_channel: grpc.Channel = grpc.secure_channel(
                auth_target, credentials, auth_channel_options)
            self.owned_channels.append(auth_channel)
            return AuthClient(channel=auth_channel, rpc_timeout_seconds=rpc_timeout_seconds)

    def create_controller_client(self, rpc_timeout_seconds: int = 120) -> ControllerClient:
        """
        Create the controller client for this session manager.

        :param rpc_timeout_seconds: the timeout period in seconds for RPCs. Defaults to 120 if not provided.
        :return: the controller client
        """
        controller_port = self.config.get("controller_port")
        controller_host = self.config.get("controller_host")

        controller_channel_options = []

        if self.config.get("controller_service_config"):
            controller_channel_options.append(("grpc.enable_retries", 1))
            controller_channel_options.append(("grpc.service_config", SessionManager._clamp_retries(
                self.config.get("controller_service_config"), self.log)))

        if self.truststore_pem is None:
            return ControllerClient(
                controller_host, controller_port,
                channel_options=controller_channel_options,
                client_name=self.client_name)
        else:
            credentials = grpc.ssl_channel_credentials(
                root_certificates=self.truststore_pem)

            if self.config.get("override_authorities"):
                authority = self.config.get("controller_authority") if self.config.get(
                    "controller_authority") else "authserver"
                controller_channel_options.append(
                    ('grpc.ssl_target_name_override', authority))

            controller_target = controller_host + ":" + str(controller_port)
            controller_channel: grpc.Channel = grpc.secure_channel(controller_target, credentials,
                                                                   controller_channel_options)
            self.owned_channels.append(controller_channel)
            return ControllerClient(
                channel=controller_channel,
                client_name=self.client_name,
                rpc_timeout_seconds=rpc_timeout_seconds)

    @staticmethod
    def _clamp_retries(config_json: str, log: logging.Logger, num: int = 5) -> str:
        """
        If we use the default Java configuration of 60 retries, then we end up with ugly warning messages emitted by gRPC of:
         E0724 09:20:06.453121678 1253749 retry_service_config.cc:145]          service config: clamped retryPolicy.maxAttempts at 5

        :param config_json: the configuration json to mutate
        :param num: the maximum number of retries permitted
        """
        try:
            modified = False
            as_dict = loads(config_json)
            methodConfig = as_dict["methodConfig"]
            for method in methodConfig:
                retryPolicy = method["retryPolicy"]
                maxAttempts = retryPolicy["maxAttempts"]
                if maxAttempts > 5:
                    retryPolicy["maxAttempts"] = num
                    modified = True
                    log.debug(
                        "Clamping maximum gRPC retries to %d." % num)

            if modified:
                return dumps(as_dict)
        except Exception as e:
            print(e)
        return config_json

    def external_login(self, auth_key: Union[str, bytes]) -> None:
        """
        Authenticate to the server using an external authentication method, such as SAML or a custom, non-standard external
        authentication module.

        This requires that the server be configured with the external authentication module and that the external
        authentication module should be configured to accept the provided auth_key.

        :param auth_key: the authentication key used for external login.  This must be a string or bytes.
        """
        self.auth_client.external_login(auth_key)
        self.__init_controller()

    def password(self, user: str, password: str, effective_user: str = None):
        """
        Authenticates to the server using a username and password.

        :param user: the user to authenticate
        :param password: the user's password
        :param effective_user: the user to operate as, defaults to the user to authenticate
        """
        self.auth_client.password(user, password, effective_user)
        self.__init_controller()

    def saml(self):
        """
        Authenticate using SAML, which must be configured on the server.
        """
        if not "saml_sso_uri" in self.config:
            raise Exception("SAML URI is not defined in connection.json")
        self.auth_client.saml(self.config["saml_sso_uri"])
        self.__init_controller()

    def upload_key(self, pubtext: str):
        """
        Upload the provided public key to the Deephaven server.
        """
        if not "acl_write_server" in self.config:
            raise Exception("ACL Write URI is not defined in connection.json")

        self.auth_client.upload_key(pubtext, self.config["acl_write_server"])

    def delete_key(self, pubtext: str):
        """
        Delete the specified public key from the Deephaven server.
        """
        if not "acl_write_server" in self.config:
            raise Exception("ACL Write URI is not defined in connection.json")

        self.auth_client.upload_key(
            pubtext, self.config["acl_write_server"], delete=True)

    def private_key(self, file: Union[str, io.StringIO]):
        """
        Authenticate to the server using a Deephaven format private key file.

        https://deephaven.io/enterprise/docs/resources/how-to/connect-from-java/#instructions-for-setting-up-private-keys

        :param file: a string file name containing the private key produced by generate-iris-keys, or alternatively an
        io.StringIO instance (which may be closed after it is read)
        """
        self.auth_client.private_key(file)
        self.__init_controller()

    def close(self):
        """
        Terminate this session managers connection to the authentication server and controller.
        """
        # We should close the queries in order to delete the sessions:
        while len(self.active_sessions) > 0:
            session = self.active_sessions.pop()
            session.close()
        self.auth_client.close()
        self.controller_client.close()
        for channel in self.owned_channels:
            try:
                channel.close()
            except grpc.RpcError as e:
                self.log.warning("Failed to close channel: %s", e)

    def ping(self):
        """
        Send a ping to the authentication server and controller.
        :return: False if either ping was not sent, True if both pings were sent.
        """
        if not self.auth_client.ping():
            return False
        return self.controller_client.ping()

    def connect_to_new_worker(self, name, heap_size_gb: float,
                              server: str = None,
                              extra_jvm_args: List[str] = None,
                              extra_environment_vars: List[str] = None,
                              engine: str = "DeephavenCommunity",
                              auto_delete_timeout: Optional[int] = 600,
                              admin_groups: List[str] = None,
                              viewer_groups: List[str] = None,
                              timeout_seconds: float = 60,
                              configuration_transformer: Callable[[
                                  PersistentQueryConfigMessage], PersistentQueryConfigMessage] = None,
                              session_arguments: Dict[str, any] = None) -> "DndSession":
        """
        Create a new worker (as a temporary PersistentQuery) and establish a session to it.

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
        :param timeout_seconds: how long to wait for the query to start.  Defaults to 60 seconds.
        :param configuration_transformer: a function that can replace (or edit) the automatically generated persistent
               query configuration, enabling you to set more advanced options than the other function parameters provide.  Defaults to None.
        :param session_arguments: a dictionary of additional arguments to pass to the pydeephaven.Session created and wrapped by a DndSession
        :return: a session connected to a new Interactive Console PQ worker
        """
        now: datetime = datetime.now()
        start_time = time.time()

        # Create the Configuration
        name = "Python Console " + str(now) if name is None else name
        temp_config: PersistentQueryConfigMessage
        temp_config = self.controller_client.make_temporary_config(name, heap_size_gb,
                                                                   server=server,
                                                                   extra_jvm_args=extra_jvm_args,
                                                                   extra_environment_vars=extra_environment_vars,
                                                                   engine=engine,
                                                                   auto_delete_timeout=auto_delete_timeout,
                                                                   admin_groups=admin_groups,
                                                                   viewer_groups=viewer_groups)
        if configuration_transformer is not None:
            temp_config = configuration_transformer(temp_config)
        serial: int = self.controller_client.add_query(temp_config)
        self.controller_client.restart_query(serial)

        print("Waiting for query \"%s\" to be ready" % name)
        timeout_left = timeout_seconds - (time.time() - start_time)
        pqinfo: PersistentQueryInfoMessage = self.__wait_for_ready(
            serial, timeout_left)

        if pqinfo is None:
            time_elapsed = time.time() - start_time
            self.controller_client.delete_query(serial)
            raise Exception("Persistent Query did not start after %.1f seconds, serial=%s, name=%s" % (
                time_elapsed, serial, name))

        if self.controller_client.is_terminal(pqinfo.state.status):
            self.controller_client.delete_query(serial)
            raise Exception(
                "Query is in terminal state.  Exception details: ", pqinfo.state.exceptionDetails)

        if not self.controller_client.is_running(pqinfo.state.status):
            time_elapsed = time.time() - start_time
            self.controller_client.delete_query(serial)
            status_name = self.controller_client.status_name(
                pqinfo.state.status)
            details = "" if pqinfo.state.statusDetails is None else pqinfo.state.statusDetails
            raise Exception("Query '%s' is not running after %.1f seconds.  Status: %s %s" % (
                name, time_elapsed, status_name, details))

        print("Connecting to new query \"%s\", ProcessInfoId=\"%s\"" %
              (pqinfo.config.name, pqinfo.state.connectionDetails.processInfoId))

        return self.__make_session(pqinfo, serial, auto_delete=True, session_arguments=session_arguments)

    def __wait_for_ready(self, serial, timeout_seconds) -> Optional[deephaven_enterprise.proto.persistent_query_pb2.PersistentQueryInfoMessage]:
        last_status = None
        last_status_details = None
        pqinfo: Optional[deephaven_enterprise.proto.persistent_query_pb2.PersistentQueryInfoMessage] = None
        deadline = time.time() + timeout_seconds
        while deadline > time.time():
            pq_info_map, map_version = self.controller_client.map_and_version()
            pqinfo = pq_info_map.get(serial, None)
            if pqinfo:
                if not pqinfo.HasField("state"):
                    if last_status is not None:
                        print(datetime.now(), "No state for ", pqinfo.config.name)
                        last_status = None
                        last_status_details = None
                else:
                    status = pqinfo.state.status
                    status_details = pqinfo.state.statusDetails
                    if self.controller_client.is_running(status):
                        break
                    elif self.controller_client.is_terminal(status):
                        break
                    if status != last_status or status_details != last_status_details:
                        status_name = self.controller_client.status_name(status)
                        print(datetime.now(), pqinfo.config.name,
                              ": Query Status: ", status_name, status_details)
                    last_status = status
                    last_status_details = status_details
            # Only to continue if there are actual changes to the pq info map
            self.controller_client.wait_for_change_from_version(map_version=map_version, timeout_seconds=deadline - time.time())
        return pqinfo

    def connect_to_persistent_query(self, name: str = None, serial: int = None, session_arguments: Dict[str, any] = None) -> "DndSession":
        """
        Connect to an existing persistent query by name or serial number.  The query must be running.

        :param name: the name of the persistent query to connect to
        :param serial: the serial number of the persistent query to connect to
        :param session_arguments: a dictionary of additional arguments to pass to the pydeephaven.Session created and wrapped by a DndSession

        :return: a session connected to the persistent query
        """
        pqinfo: Optional[PersistentQueryInfoMessage]

        if serial is not None:
            pqinfo = self.controller_client.get(serial)
            if pqinfo is None:
                raise Exception(
                    "Could not find query with serial: " + str(serial))
            if name is not None:
                if pqinfo.config.name != name:
                    raise Exception(
                        "Name (" + name + ") and serial number (" + str(serial) + ") are inconsistent: " + str(
                            pqinfo.config))
        elif name is not None:
            pqinfo = None
            for search_pq in self.controller_client.map().values():
                if search_pq.config.name == name:
                    pqinfo = search_pq
                    serial = search_pq.config.serial
                    break
            if pqinfo is None:
                raise Exception("Could not find query with name: " + name)
        else:
            raise Exception(
                "You must specify either name or serial to connect_to_persistent_query.")

        if self.controller_client.is_terminal(pqinfo.state.status):
            raise Exception(
                "Query is in terminal state.  Exception details: " + str(pqinfo.state.exceptionDetails))

        if not self.controller_client.is_running(pqinfo.state.status):
            status_name = self.controller_client.status_name(
                pqinfo.state.status)
            raise Exception("Query '%s' is not running, state is %s" %
                            (name, status_name))

        return self.__make_session(pqinfo, serial, auto_delete=False, session_arguments=session_arguments)

    def __make_session(self, pqinfo, serial, auto_delete: bool, session_arguments: Dict[str, any] = None):
        url: str = pqinfo.state.connectionDetails.grpcUrl
        if url is None or url == "":
            if pqinfo.state.engineVersion == "":
                raise Exception("Not a Community engine: " +
                                pqinfo.config.name + "(" + str(pqinfo.config.serial) + ")")
            raise Exception("gRPC is not available for " +
                            pqinfo.config.name + "(" + str(pqinfo.config.serial) + ")")
        parsed = urllib.parse.urlparse(url)

        envoy_prefix: str = pqinfo.state.connectionDetails.envoyPrefix
        extra_headers = {b'envoy-prefix': bytes(envoy_prefix, 'us-ascii')}

        token: deephaven_enterprise.proto.auth_pb2.Token = self.auth_client.get_token(
            "RemoteQueryProcessor")
        token_base64 = base64.b64encode(
            token.SerializeToString()).decode('us-ascii')

        port = parsed.port
        if port is None:
            if parsed.scheme == 'https':
                port = 443
            elif parse.scheme == 'http':
                port = 80
            else:
                raise RuntimeError("no explicit port in URL " + url + " and unknown scheme " + parsed.scheme)

        session = DndSession(session_manager=self, pqinfo=pqinfo, host=parsed.hostname, port=port, auth_token=token_base64,
                             extra_headers=extra_headers, delete_on_close=serial if auto_delete else None,
                             session_type=pqinfo.config.scriptLanguage,
                             session_arguments=session_arguments
                             )

        return session

    def __init_controller(self):
        self.controller_client.set_auth_client(self.auth_client)
        self.controller_client.subscribe()


class DndSession(pydeephaven.session.Session):
    """
    Wrapper around a basic Community session.  For queries that are ephemeral, they are explicitly deleted on session
    close.
    """
    delete_on_close: Optional[int]
    session_manager: SessionManager
    __pqinfo: PersistentQueryInfoMessage
    __barrage_session: barrage.BarrageSession
    __barrage_scope: LivenessScope

    def __init__(self, session_manager: SessionManager,
                 pqinfo: PersistentQueryInfoMessage,
                 host: str = None, port: int = None,
                 auth_type: str = "io.deephaven.proto.auth.Token", auth_token: str = None,
                 extra_headers: Dict[bytes, bytes] = None, delete_on_close: int = None,
                 session_type: str = 'python',
                 session_arguments: Dict[str, any] = None):
        # We initialize enough to delete the query
        self.delete_on_close = delete_on_close
        self.session_manager = session_manager
        self.session_manager.active_sessions.append(self)

        # Then call the super, the base class __del__ method is still invoked by the Python runtime.  The
        # pydeephaven.Session __del__ method calls close() - which we override.  If we call into the super close,
        # in those cases, the uninitialized Session object will throw from the close method.
        try:
            super().__init__(host=host, port=port, auth_type=auth_type, auth_token=auth_token, use_tls=True,
                             extra_headers=extra_headers, tls_root_certs=session_manager.truststore_pem,
                             session_type=session_type,
                             **(session_arguments if session_arguments is not None else dict()))
        except Exception as e:
            self.init_complete = False
            raise e
        # init was complete, we can close the object when it comes time
        self.init_complete = True
        self.__pqinfo = pqinfo
        self.__barrage_session = None
        self.__barrage_scope = None

    def pqinfo(self) -> PersistentQueryInfoMessage:
        """
        Retrieve the persistent query information for this query.

        :return:
        """
        return self.__pqinfo

    def close(self):
        if self.__barrage_scope is not None:
            self.__barrage_scope.release()
        if self.__barrage_session is not None:
            self.__barrage_session.close()
        if self.init_complete:
            super().close()
        if self.delete_on_close is not None:
            self.session_manager.controller_client.delete_query(
                self.delete_on_close)
            self.delete_on_close = None
        try:
            self.session_manager.active_sessions.remove(self)
        except ValueError:
            pass

    def historical_table(self, namespace: str, table_name: str):
        """
        Fetches a historical table from the database on the server.

        :param namespace: the namespace of the table
        :param table_name: the name of the table

        :return: a Table object
        :raise: DHError
        """
        return self.__fetch_table_(DatabaseTicket.historical_ticket(namespace, table_name))

    def live_table(self, namespace: str, table_name: str):
        """
        Fetches a live table from the database on the server.

        :param namespace: the namespace of the table
        :param table_name: the name of the table

        :return: a Table object
        :raise: DHError
        """
        return self.__fetch_table_(DatabaseTicket.live_ticket(namespace, table_name))

    def catalog_table(self):
        """
        Fetches the catalog table from the database on the server.

        :return: a Table object
        :raise: DHError
        """
        return self.__fetch_table_(CatalogTicket.catalog_ticket())

    def __fetch_table_(self, ticket):
        with self._r_lock:
            faketable = Table(session=self, ticket=ticket)
            try:
                table_op = FetchTableOp()
                return self.table_service.grpc_table_op(faketable, table_op)
            except Exception as e:
                if isinstance(e.__cause__, grpc.RpcError):
                    if e.__cause__.code() == grpc.StatusCode.INVALID_ARGUMENT:
                        raise DHError(
                            f"no table by the name {ticket}") from None
                raise e
            finally:
                # Explicitly close the table without releasing it (because it isn't ours)
                faketable.ticket = None
                faketable.schema = None

    def _maybe_init_barrage_session(self):
        if importlib.util.find_spec("deephaven") is None:
            raise Exception(
                "Barrage functionality is only supported in workers.")
        else:
            from deephaven import barrage
            from deephaven.liveness_scope import LivenessScope

        if self.__barrage_session is None:
            url = urllib.parse.urlparse(
                self.__pqinfo.state.connectionDetails.grpcUrl)
            host = url.hostname
            port = url.port

            auth_type = "io.deephaven.proto.auth.Token"
            token = self.session_manager.auth_client.get_token(
                "RemoteQueryProcessor")
            auth_token = base64.b64encode(
                token.SerializeToString()).decode('us-ascii')

            envoy_prefix = self.__pqinfo.state.connectionDetails.envoyPrefix
            extra_headers = None if envoy_prefix is None else {
                "envoy-prefix": envoy_prefix}

            self.__barrage_session = barrage.barrage_session(host=host, port=port, auth_type=auth_type, auth_token=auth_token,
                                                             use_tls=True, tls_root_certs=self.session_manager.truststore_pem, extra_headers=extra_headers)
            self.__barrage_scope = LivenessScope()

        return self.__barrage_session

    def barrage_subscribe(self, table_ref: Table) -> deephaven.table.Table:
        """
        Creates a local table of the specified table reference that subscribes to updates.

        :param table_ref: table reference to create local table of
        :return: local table subscribed to updates
        """
        barrage_session = self._maybe_init_barrage_session()

        ticket = SharedTicket.random_ticket()
        self.publish_table(ticket, table_ref)

        with self.__barrage_scope.open():
            barrage_table = barrage_session.subscribe(ticket.bytes)

        return barrage_table

    def barrage_snapshot(self, table_ref: Table) -> deephaven.table.Table:
        """
        Creates a local table snapshot of the specified table reference.

        :param table_ref: table reference to create local table of
        :return: local table snapshot
        """
        barrage_session = self._maybe_init_barrage_session()

        ticket = SharedTicket.random_ticket()
        self.publish_table(ticket, table_ref)
        return barrage_session.snapshot(ticket.bytes)

    def barrage_session(self) -> barrage.BarrageSession:
        """
        Returns a Barrage session connected to the same Persistent Query as this DndSession.

        :return: the Barrage session connected to the same Persistent Query as this DndSession
        """

        return self._maybe_init_barrage_session()

class DatabaseTicket(Ticket):
    """A DatabaseTicket is ticket that references a table by namespace and table name"""
    def __init__(self, ticket_bytes: bytes):
        """Initializes a DatabaseTicket.

        Args:
            ticket_bytes (bytes): the raw bytes for the ticket
        """
        if not ticket_bytes:
            raise DHError('DatabaseTicket: ticket is None')
        elif not ticket_bytes.startswith(b'd/'):
            raise DHError(f'DatabaseTicket: ticket {ticket_bytes} is not a database table ticket')
        elif len(ticket_bytes.split(b'/')) != 4:
            raise DHError(f'DatabaseTicket: ticket {ticket_bytes} is not in the correct format')

        splits = ticket_bytes.split(b'/')

        self.type = splits[1].decode(encoding='ascii')
        self.namespace = splits[2].decode(encoding='ascii')
        self.table_name = splits[3].decode(encoding='ascii')

        super().__init__(ticket_bytes)

    @classmethod
    def live_ticket(cls, namespace: str, table_name: str) -> DatabaseTicket:
        """Creates a ticket that references a database intraday table

        Args:
            namespace (str): the namespace
            table_name (str): the table name

        Returns:
            a DatabaseTicket
        """
        return DatabaseTicket._db_ticket('live', namespace, table_name)

    @classmethod
    def historical_ticket(cls, namespace: str, table_name: str) -> DatabaseTicket:
        """Creates a ticket that references a database historical table

        Args:
            namespace (str): the namespace
            table_name (str): the table name

        Returns:
            a DatabaseTicket
        """
        return DatabaseTicket._db_ticket('hist', namespace, table_name)

    @classmethod
    def _db_ticket(cls, type: str, namespace: str, table_name: str) -> DatabaseTicket:
        """Creates a ticket that references a database table

        Args:
            type (str): the type (live, hist, or catalog)
            namespace (str): the namespace
            table_name (str): the table name

        Returns:
            an LiveTicket
        """
        if not type or type not in ['live', 'hist', 'catalog']:
            raise DHError('db_ticket: type must be one of [live, hist, catalog]')
        if not namespace:
            raise DHError('db_ticket: namespace must be a non-empty string')
        if not table_name:
            raise DHError('db_ticket: table_name must be a non-empty string')

        return cls(ticket_bytes=f'd/{type}/{namespace}/{table_name}'.encode(encoding='ascii'))

class CatalogTicket(Ticket):
    """A CatalogTicket is ticket that the catalog table"""
    def __init__(self):

        super().__init__(f'd/catalog'.encode(encoding='ascii'))

    @classmethod
    def catalog_ticket(cls):
        """Creates a ticket that references the database catalog table

        Returns:
            a CatalogTicket
        """
        return cls()
