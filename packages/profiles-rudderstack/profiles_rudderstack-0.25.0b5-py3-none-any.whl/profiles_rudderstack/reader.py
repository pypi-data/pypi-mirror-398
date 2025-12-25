import profiles_rudderstack.tunnel.tunnel_pb2 as tunnel
from profiles_rudderstack.go_client import get_gorpc


class Reader:
    def __init__(self):
        self.__gorpc = get_gorpc()

    def get_input(self, prompt: str, is_secret=False) -> str:
        response: tunnel.GetInputResponse = self.__gorpc.GetInput(
            tunnel.GetInputRequest(prompt=prompt, is_secret=is_secret)
        )
        return response.input
