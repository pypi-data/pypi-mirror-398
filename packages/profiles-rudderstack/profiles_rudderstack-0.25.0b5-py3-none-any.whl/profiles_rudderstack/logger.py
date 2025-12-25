import profiles_rudderstack.tunnel.tunnel_pb2 as tunnel
from profiles_rudderstack.go_client import get_gorpc


class Logger:
    def __init__(self, name: str) -> None:
        self.__name = name
        self.__gorpc = get_gorpc()
        if self.__gorpc is None:
            raise Exception(
                "error: creating logger, go client is not initialized")

    def info(self, message: str) -> None:
        self.__gorpc.LogInfo(tunnel.LogRequest(
            name=self.__name, message=message))

    def warn(self, message: str) -> None:
        self.__gorpc.LogWarn(tunnel.LogRequest(
            name=self.__name, message=message))

    def error(self, message: str) -> None:
        self.__gorpc.LogError(tunnel.LogRequest(
            name=self.__name, message=message))

    def debug(self, message: str) -> None:
        self.__gorpc.LogDebug(tunnel.LogRequest(
            name=self.__name, message=message))
