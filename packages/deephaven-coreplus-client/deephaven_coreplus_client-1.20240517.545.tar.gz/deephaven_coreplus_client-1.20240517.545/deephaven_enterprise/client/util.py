from __future__ import annotations

import binascii
import grpc
import google.protobuf
import socket
import time
import uuid

import deephaven_enterprise.proto.auth_pb2 as auth_pb2


"""
Utility functions for the Deephaven Enterprise client, these are not part of the stable API or intended for external use. 
"""
def _proto_to_key(proto: google.protobuf.message.Message) -> str:
    return proto.DESCRIPTOR.full_name.lower()+"-bin"


_auth_error_metadata_key: str = _proto_to_key(auth_pb2.AuthError())


def get_grpc_channel(channel: grpc.Channel, host: str, port: int, channel_options=None) -> (grpc.Channel, str):
    """
    Given a channel or host and port, produce the grpc channel for use with the auth client or controller client and a
    "me" string that is used for logging on the server.

    :param channel: an already configured grpc channel (mutually exclusive with host and port)
    :param host: the host name to connect to (requires port)
    :param port: the port to connect to (requires host)
    :param channel_options: a list of options for grpc channel creation (not used when channel is set)
    :return:
    """
    if channel is not None:
        return (channel, "Python:" + get_ip("127.0.0.1", 80))
    elif host is not None:
        if port is None:
            raise Exception("port is required when host is specified")

        me = "Python:" + get_ip(host, port)
        target = host + ":" + str(port)
        channel = grpc.secure_channel(
            target, grpc.ssl_channel_credentials(), options=channel_options)
        return (channel, me)
    else:
        raise Exception("channel or host is required")


def make_client_id(me: str) -> auth_pb2.ClientId:
    """
    Generate a Deephaven client id using the "me" description and a random UUID.
    :param me: client identifier
    :return: a ClientID for use in RPCs
    """
    clientID: auth_pb2.ClientId = auth_pb2.ClientId()
    clientID.uuid = uuid.uuid4().bytes
    clientID.name = me
    return clientID


def _uuid_str(bs: bytes) -> str:
    return "UUID=" + binascii.hexlify(bs).decode('utf-8')


def get_ip(host: str, port: int) -> str:
    """
    Gets the local address by creating a datagram socket to the specified host and port and requesting the local sockname.
    :param host:remote host
    :param port:remote port
    :return: the local ip address (or "<unknown>")
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    # noinspection PyBroadException
    try:
        # doesn't even have to be reachable
        s.connect((host, port))
        ip = s.getsockname()[0]
    except Exception:
        ip = '<unknown>'
    finally:
        s.close()
    return ip


def _maybe_reinterpret_and_raise(error: grpc.RpcError):
    auth_error = auth_pb2.AuthError()
    if len(error.trailing_metadata()) > 0:
        for md in error.trailing_metadata():
            if md.key == _auth_error_metadata_key:
                auth_error.ParseFromString(md.value)
                raise Exception(auth_error.message) from None
    raise error
