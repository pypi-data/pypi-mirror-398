import grpc
from grpc_interceptor import ClientCallDetails, ClientInterceptor
from profiles_rudderstack.tunnel.tunnel_pb2_grpc import WhtServiceStub

GoRpc = None


def init_go_rpc(goRpcAddress: str, token: str):
    interceptors = [ClientTokenAuthInterceptor(token)]
    size_in_kb = 64 # Default is 8
    options = [
        ('grpc.max_metadata_size', size_in_kb * 1024)
    ]
    channel = grpc.insecure_channel(goRpcAddress, options=options)
    intercept_channel = grpc.intercept_channel(channel, *interceptors)
    global GoRpc
    GoRpc = WhtServiceStub(intercept_channel)
    return GoRpc, channel


def get_gorpc() -> WhtServiceStub:
    if GoRpc is None:
        raise Exception("Go RPC Client not initialized")
    return GoRpc


class ClientTokenAuthInterceptor(ClientInterceptor):
    def __init__(self, token: str):
        self.token = token

    def intercept(self, method, request_or_iterator, call_details: grpc.ClientCallDetails):
        new_details = ClientCallDetails(
            call_details.method,
            call_details.timeout,
            [("authorization", self.token)],
            call_details.credentials,
            call_details.wait_for_ready,
            call_details.compression,
        )

        return method(request_or_iterator, new_details)
