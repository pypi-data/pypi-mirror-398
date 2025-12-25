from __future__ import annotations

from typing import List, Union

import base64
import datetime
import io
import secrets
import urllib.parse
import webbrowser
import urllib
import json
import requests

import Cryptodome.PublicKey.DSA
import Cryptodome.Hash.SHA256
import Cryptodome.Signature.DSS

import logging
import re
import time
import threading
import deephaven_enterprise.proto.auth_service_pb2_grpc
import deephaven_enterprise.proto.auth_pb2
import grpc

import deephaven_enterprise.client.util


class RefreshThread(threading.Thread):
    def __init__(self, auth_client: "AuthClient", slack_seconds: int = 60 * 2):
        """
        Create a thread to refresh the authentication cookie.  If the cookie is not refreshed within the deadline,
        then we will become unauthenticated and not be able to generate any more tokens.
        :param auth_client: auth client to refresh
        :param slack_seconds: how long before the cookie's expiration, in seconds, should we begin the refresh.
        Defaults to two minutes.
        """
        threading.Thread.__init__(self)
        self.daemon = True
        self.auth_client = auth_client
        self.slack = slack_seconds

    def run(self):
        # We don't want to hit the server too hard
        minimum_sleeps: List[int] = [1, 1, 2, 3, 5, 8, 13]
        sleep_index = 0

        while self.auth_client.cookie is not None:
            start_time = time.time()
            next_deadline_millis = self.auth_client.cookie_deadline_time_millis
            if next_deadline_millis is None or next_deadline_millis < start_time:
                # we've failed to refresh, we could try re-authentication with a private key if that was our method
                break
            next_deadline_seconds = next_deadline_millis / 1000

            to_sleep: float = next_deadline_seconds - start_time - self.slack
            time.sleep(to_sleep)
            self.auth_client.ping()
            # We expect the deadline to handle most sleeps, this logic prevents tight loops.
            duration_seconds: float = (time.time() - start_time)
            if duration_seconds < minimum_sleeps[sleep_index]:
                catchup_seconds = minimum_sleeps[sleep_index] - \
                    duration_seconds
                time.sleep(catchup_seconds)
                sleep_index = min(len(minimum_sleeps) - 1, sleep_index + 1)
            else:
                sleep_index = 0


class AuthClient:
    """
    AuthClient authenticates to a Deephaven authentication server and produces tokens for use with other Deephaven
    services.

    Presently, password and private key authentication are provided.
    """
    cookie_deadline_time_millis: int
    refresh_thread: "RefreshThread"
    channel: grpc.Channel
    me: str
    opened_channel: bool
    rpc_timeout_secs: int
    log: logging.Logger

    def __init__(self, host: str = None, port: int = None, rpc_timeout_seconds: int = 120, channel: grpc.Channel = None, channel_options=None, client_name=None):
        """
        Create an AuthClient and connect to the server.

        You may either specify the host and port to connect to, or provide your own grpc channel.  The simplest case
        is to simply provide the host and port, but if you need advanced channel configuration or want to share the
        channel for several clients, then you can create it and pass it in.

        :param host: the host to connect to, requires port
        :param port: the port to connect to, requires host
        :param rpc_timeout_seconds: the rpc timeout period to use, defaults to 120 seconds if not provided
        :param channel: a pre-created channel to use for the gRPC messages, it will not be closed by this client.
        :param channel_options: a list of options for channel creation (not used if the channel is provided)
        :param client_name: a name to append to the client identifier, useful for debugging and logging.
        """
        self.cookie = None
        self.refresh_thread = None
        self.cookie_deadline_time_millis = None
        self.rpc_timeout_secs = rpc_timeout_seconds
        self.log = logging.getLogger("deephaven_enterprise.client.auth")
        (self.channel, self.me) = deephaven_enterprise.client.util.get_grpc_channel(
            channel=channel, host=host, port=port, channel_options=channel_options)
        if client_name is not None:
            self.me += '_' + client_name
        self.opened_channel = channel is None
        self.clientID = deephaven_enterprise.client.util.make_client_id(
            self.me)
        self.me += '_' + deephaven_enterprise.client.util._uuid_str(self.clientID.uuid)
        self.log.info(f'{self.me} starting')

        self.stub = deephaven_enterprise.proto.auth_service_pb2_grpc.AuthApiStub(
            self.channel)

        self._send_ping()

    def _send_ping(self) -> float:
        """
        Sends a common ping request over the stub.
        :param stub: the stub to send a ping request over
        :param me: client identifier
        :return: the RTT in milliseconds of the ping
        """
        pingreq = deephaven_enterprise.proto.common_pb2.PingRequest()
        sendTime = time.time_ns()
        pingreq.sender_send_time_millis = int(sendTime / 1_000_000)
        pingreq.__setattr__("from", self.me)
        response = self.stub.ping(pingreq, timeout=self.rpc_timeout_secs, wait_for_ready=True)
        rtt = (time.time_ns() - sendTime) / 1_000_000
        server_time = datetime.datetime.utcfromtimestamp(response.receiver_receive_time_millis/1_000)
        server = getattr(response, 'from')
        self.log.info(
            f'{self.me} sent ping RPC request and got response, rountrip={rtt:.3f}s, ' +
            
            f'answer from={server} at {server_time}')
        return rtt

    def external_login(self, auth_key: Union[str, bytes]) -> None:
        """
        Authenticate to the server using an external authentication method, such as SAML or a custom, non-standard external
        authentication module.

        This requires that the server be configured with the external authentication module and that the external
        authentication module should be configured to accept the provided auth_key.

        :param auth_key: the authentication key used for external login.  This must be a string or bytes.
        """
        abe: deephaven_enterprise.proto.auth_pb2.AuthenticateByExternalRequest = deephaven_enterprise.proto.auth_pb2.AuthenticateByExternalRequest()
        abe.client_id.CopyFrom(self.clientID)
        if isinstance(auth_key, bytes):
            # If auth_key is bytes, decode it to a string
            auth_key = auth_key.decode('utf-8')
        abe.key = auth_key

        start_time = time.time()
        ar: deephaven_enterprise.proto.auth_pb2.AuthenticateByExternalLoginResponse = self.stub.authenticateByExternal(
            abe)
        end_time = time.time()
        if not ar.result.authenticated:
            msg = "Failed to authenticate with external login."
            self.log.error(f'{self.me}: {msg} in {(end_time-start_time)/1_000:.3f}s.')
            raise AuthenticationFailedException(msg)
        self.__set_cookie(ar)
        self.log.info(f'{self.me} authenticated with external login in {(end_time-start_time)/1_000:.3f}s.')

    def password(self, user: str, password: str, effective_user: str = None) -> None:
        """
        Authenticates to the server using a username and password.

        :param user: the user to authenticate
        :param password: the user's password
        :param effective_user: the user to operate as, defaults to the user to authenticate
        """
        uc = deephaven_enterprise.proto.auth_pb2.UserContext()
        uc.authenticatedUser = user
        if effective_user is None:
            uc.effectiveUser = user
        else:
            uc.effectiveUser = effective_user

        abp = deephaven_enterprise.proto.auth_pb2.AuthenticateByPasswordRequest()
        abp.client_id.CopyFrom(self.clientID)
        abp.user_context.CopyFrom(uc)
        abp.password = password
        start_time = time.time()
        ar = self.stub.authenticateByPassword(abp,
                                              timeout=self.rpc_timeout_secs, wait_for_ready=True)
        end_time = time.time()
        if not ar.result.authenticated:
            msg = "Failed to authenticate with password."
            self.log.error(f'{self.me}: {msg} in {(end_time-start_time)/1_000:.3f}s.')
            raise AuthenticationFailedException(msg)
        self.__set_cookie(ar)
        self.log.info(f'{self.me} authenticated with password in {(end_time-start_time)/1_000:.3f}s.')

    def saml(self, login_uri: str) -> None:
        """
        Authenticate using SAML, which must be configured on the server.

        :param login_uri: the URI for the Deephaven SAML plugin.  Often "https://deephaven-auth-server:9032/dh-saml/", but is dependent on configuration.
        """
        random_bytes = secrets.token_bytes(96)
        nonce = base64.b64encode(random_bytes)
        uri = login_uri + "?key=" + urllib.parse.quote_plus(nonce)
        webbrowser.open(uri)

        try:
            self.external_login(nonce)
        except AuthenticationFailedException as e:
            msg = "Failed to authenticate with SAML."
            raise AuthenticationFailedException(msg) from e

    @staticmethod
    def generate_keypair(user: str) -> (str, str):
        """
        Generate a new keypair in Deephaven format.

        The private key can be stored as a file and used to authenticate using the private_key method.  The public key
        contains a username followed by the public key.  The public key should be uploaded to the Deephaven ACL write
        server.

        :param user: the username to write into the key
        :return: a tuple containing the private key text and the public key text in Deephaven format
        """
        key = Cryptodome.PublicKey.ECC.generate(curve='p256')
        ec_sentinel = "EC:".encode("utf-8")
        pub = base64.b64encode(ec_sentinel + key.public_key().export_key(
            format="DER")).decode("us-ascii")
        priv = base64.b64encode(ec_sentinel + key.export_key(
            format="DER", use_pkcs8=True)).decode("us-ascii")
        privtext = """user %s
operateas %s
public %s
private %s
""" % (user, user, pub, priv)
        pubtext = "%s %s" % (user, pub)
        return (privtext, pubtext)

    def upload_key(self, pubtext: str, url: str, delete: bool = False):
        """
        Upload a public key to the ACL write server.

        :param pubtext: text of the public key, in Deephaven format
        :param url: URL of the ACL write server (e.g., https://foo.bar.company.com:9044/acl/)
        :param delete: True to delete the key instead of add the key
        """
        lines: List[str] = list(filter(lambda y: len(y) > 0, map(
            lambda x: x.strip(), pubtext.splitlines())))
        if (len(lines) != 1):
            raise Exception(
                "Invalid public key text, must be one line of the form '<username> <base64 encoded key>'")

        auth_token = self.get_token("DbAclWriteServer")
        token_as_string = auth_token.SerializeToString()
        token_encoded: bytes = base64.b64encode(token_as_string)
        authorization_header = token_encoded.decode("us-ascii")
        (user, key) = pubtext.split(" ")

        headers = {"Authorization": authorization_header,
                   "Content-Type": 'application/json'}

        ec_sentinel = "EC:".encode("utf-8")
        pub_key_bytes = base64.b64decode(key)
        if pub_key_bytes[0:3] == ec_sentinel:
            algorithm = "EC"
        else:
            algorithm = "DSA"

        if delete:
            path = url + ("/" if not url.endswith("/") else "") + \
                "publickey/" + urllib.parse.quote_plus(user)
            query_params = {"encodedStr": key, "algorithm": algorithm}
            response: requests.Response = requests.delete(
                path, params=query_params, headers=headers)
            if response.status_code != 204:
                raise Exception("Unexpected response: " + str(response))
        else:
            entity = dict()
            entity["user"] = user
            entity["encodedStr"] = key
            entity["algorithm"] = algorithm

            path = url + ("/" if not url.endswith("/") else "") + "publickey/"

            response: requests.Response = requests.post(
                path, json=entity, headers=headers)
            if response.status_code != 201:
                raise Exception("Unexpected response: " + str(response))

    def private_key(self, file: Union[str, io.StringIO]) -> None:
        """
        Authenticate to the server using a Deephaven format private key file.

        https://deephaven.io/enterprise/docs/resources/how-to/connect-from-java/#instructions-for-setting-up-private-keys

        :param file: a string file name containing the private key produced by generate-iris-keys, or alternatively an
        io.StringIO instance (which may be closed after it is read)
        """
        # Read the key information from the file

        desc: str = None

        if isinstance(file, str):
            # 'file' is a string: assume it's the path to the private key file
            desc = file
            with open(file, 'r') as fp:
                keydict = self.__read_key_dict(fp)
        else:
            desc = "<StringIO>"
            with file:
                keydict = self.__read_key_dict(file)

        for field in ["public", "private", "user", "operateas"]:
            if field not in keydict:
                raise Exception(
                    "'%s' is not a Deephaven private key file, %s is not present" % (desc, field))

        try:
            # pkcs8 encoded keyspec
            public_pkcs8_bytes = base64.b64decode(keydict["public"])
            private_pkcs8_bytes = base64.b64decode(keydict["private"])

            ec_sentinel = "EC:".encode("utf-8")
            if private_pkcs8_bytes[0:3] == ec_sentinel:
                private_key = Cryptodome.PublicKey.ECC.import_key(
                    private_pkcs8_bytes[3:])
                public_key = Cryptodome.PublicKey.ECC.import_key(
                    public_pkcs8_bytes[3:])
            else:
                private_key = Cryptodome.PublicKey.DSA.import_key(
                    private_pkcs8_bytes)
                public_key = Cryptodome.PublicKey.DSA.import_key(
                    public_pkcs8_bytes)
        except Exception as e:
            msg = "Invalid private key file '%s'" % desc
            self.log.error(f'{self.me}: {msg}')
            raise Exception(msg) from e

        # Get the nonce
        nr = deephaven_enterprise.proto.auth_pb2.GetNonceRequest()
        nr.client_id.CopyFrom(self.clientID)
        gnr = self.stub.getNonce(nr)

        # Sign the nonce
        try:
            hash_of_nonce = Cryptodome.Hash.SHA256.new(gnr.nonce)
            signer = Cryptodome.Signature.DSS.new(
                private_key, 'fips-186-3', encoding="der")
            signature = signer.sign(hash_of_nonce)
        except Exception as e:
            msg = "Could not sign nonce with private key '%s'" % desc
            self.log.error(f'{self.me}: {msg}')
            raise Exception(msg) from e

        # Now verify our signature locally, just in case
        try:
            verifier = Cryptodome.Signature.DSS.new(
                public_key, 'fips-186-3', encoding="der")
            verifier.verify(hash_of_nonce, signature)
        except Exception as e:
            msg = "Could not verify our own signature with private key '%s'" % desc
            self.log.error(f'{self.me}: {msg}')
            raise Exception(msg) from e

        # Produce the authentication message
        abpk = deephaven_enterprise.proto.auth_pb2.AuthenticateByPublicKeyRequest()
        abpk.user_context.authenticatedUser = keydict["user"]
        abpk.user_context.effectiveUser = keydict["operateas"]
        abpk.client_id.CopyFrom(self.clientID)
        abpk.public_key = public_pkcs8_bytes
        abpk.challenge_response = signature
        abpk.ip_address = gnr.ip_address

        # Do the authentication
        start_time = time.time()
        response = self.stub.authenticateByPublicKey(abpk,
                                                     timeout=self.rpc_timeout_secs, wait_for_ready=True)
        end_time = time.time()
        if not response.result.authenticated:
            msg = "Failed to authenticate with private key."
            self.log.error(f'{self.me}: {msg} in {(end_time-start_time)/1_000:.3f}s.')
            raise AuthenticationFailedException(msg)
        self.__set_cookie(response)
        self.log.info(f'{self.me} authenticated with private key in {(end_time-start_time)/1_000:.3f}s.')

    def __read_key_dict(self, fp):
        keydict = {}
        for x in fp.readlines():
            stripped = x.split("#", 1)[0].strip()
            if len(stripped) == 0:
                continue
            kv = re.split("\\s+", stripped, 2)
            keydict[kv[0]] = kv[1]
        return keydict

    def get_token(self, service: str, timeout: float = None) -> deephaven_enterprise.proto.auth_pb2.Token:
        """
        Get an authentication token to present to another Deephaven service.  This token may only be used one time,
        as it is consumed by the authentication server during the verification process.

        :param service: the service that will verify the token (e.g., "PersistentQueryController")
        :param timeout: how long to wait for the gRPC call to complete
        :return: the token
        """
        gtr: deephaven_enterprise.proto.auth_pb2.GetTokenRequest = deephaven_enterprise.proto.auth_pb2.GetTokenRequest()
        gtr.service = service
        gtr.cookie = self.cookie
        return self.stub.getToken(gtr,
                                  timeout=self.rpc_timeout_secs, wait_for_ready=True).token

    def close(self) -> None:
        """
        Logout from the authentication server.  No further tokens may be requested by this client.
        """
        if self.cookie is not None:
            ivcr = deephaven_enterprise.proto.auth_pb2.InvalidateCookieRequest()
            ivcr.cookie = self.cookie
            self.cookie = None
            self.cookie_deadline_time_millis = None
            self.stub.invalidateCookie(ivcr,
                                       timeout=self.rpc_timeout_secs, wait_for_ready=True)
        if self.opened_channel:
            self.channel.close()

    def ping(self):
        """
        Pings the server, refreshing our cookie.
        :returns: True if a ping was sent, False if there is no active cookie.
        """
        cookie = self.cookie
        if cookie is None:
            return False
        rcreq = deephaven_enterprise.proto.auth_pb2.RefreshCookieRequest()
        rcreq.cookie = cookie
        rcresp = self.stub.refreshCookie(rcreq,
                                         timeout=self.rpc_timeout_secs, wait_for_ready=True)
        self.cookie_deadline_time_millis = rcresp.cookie_deadline_time_millis
        return True

    def _delegate_token(self, abdt: deephaven_enterprise.proto.auth_pb2.AuthenticateByDelegateTokenRequest):
        """
        Authenticate using the provided AuthenticateByDelegateTokenRequest

        Note: This method is for internal use only.

        :param abdt: an AuthenticateByDelegateTokenRequest that is sent to our gRPC stub
        """
        start_time = time.time()
        ar = self.stub.authenticateByDelegateToken(abdt)
        end_time = time.time()
        if not ar.result.authenticated:
            msg = "Failed to authenticate with delegate token."
            self.log.error(f'{self.me}: {msg} in {(end_time-start_time)/1_000:.3f}s.')
            raise deephaven_enterprise.client.auth.AuthenticationFailedException(msg)
        self.__set_cookie(ar)
        self.log.info(f'{self.me}: authenticated with delegate token in {(end_time-start_time)/1_000:.3f}s.')

    def __set_cookie(self, ar):
        self.cookie = ar.result.cookie
        self.cookie_deadline_time_millis = ar.result.cookie_deadline_time_millis
        self.__start_refresh()

    def __start_refresh(self):
        self.refresh_thread = RefreshThread(self)
        self.refresh_thread.start()


class AuthenticationFailedException(Exception):
    """
    This Exception is raised when the server responds to our authentication request with a failure (e.g. bad password or
    bad key).  Other errors, like the server not responding at all are not covered by this Exception.
    """
    pass
