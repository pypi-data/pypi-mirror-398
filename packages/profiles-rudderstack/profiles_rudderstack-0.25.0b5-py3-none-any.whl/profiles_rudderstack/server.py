import signal
import grpc
from concurrent import futures
from profiles_rudderstack.go_client import init_go_rpc
from profiles_rudderstack.service import PythonRpcService
from profiles_rudderstack.logger import Logger
from profiles_rudderstack.tunnel.tunnel_pb2 import SetPythonPortRequest
from profiles_rudderstack.tunnel.tunnel_pb2_grpc import add_PythonServiceServicer_to_server


class ProfilesRPCServer:
    def __init__(self, token: str, go_rpc_addr: str, current_supported_schema_version: int, pb_version: str):
        self.go_rpc_addr = go_rpc_addr
        self.__server_init(token, current_supported_schema_version, pb_version)

    def __server_init(self, token: str, current_supported_schema_version: int, pb_version: str):
        gorpc, channel = init_go_rpc(self.go_rpc_addr, token)
        self.channel = channel
        service = PythonRpcService(
            go_rpc=gorpc,
            current_supported_schema_version=current_supported_schema_version,
            pb_version=pb_version,
        )
        self.logger = Logger("ProfilesRPCServer")
        server = grpc.server(futures.ThreadPoolExecutor(
            max_workers=10), interceptors=[ServerTokenAuthInterceptor(token)])
        add_PythonServiceServicer_to_server(service, server)
        # 0.0.0.0:0 will bind to a free port on IPv4
        python_rpc_port = server.add_insecure_port("0.0.0.0:0")
        server.start()

        self.logger.info("Initialized Python rpc server")
        self.server = server

        # set python rpc port in go rpc server
        gorpc.SetPythonPort(SetPythonPortRequest(port=python_rpc_port, token=token))

        def signal_handler(sig, frame):
            self.stop()
            exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        server.wait_for_termination()

    def stop(self):
        self.channel.close()
        self.server.stop(0)


class ServerTokenAuthInterceptor(grpc.ServerInterceptor):
    def __init__(self, token: str):
        self.token = token

    def intercept_service(self, continuation, handler_call_details):
        metadata = dict(handler_call_details.invocation_metadata)
        token = metadata.get("authorization", "")

        if token != self.token:
            context = handler_call_details.invocation_context
            context.abort(grpc.StatusCode.UNAUTHENTICATED,
                          "Invalid credentials")
        else:
            return continuation(handler_call_details)
