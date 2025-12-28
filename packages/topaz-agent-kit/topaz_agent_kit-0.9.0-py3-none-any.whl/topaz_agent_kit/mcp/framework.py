from typing import Protocol
from fastmcp import FastMCP


class McpToolkit(Protocol):
    def register(self, server: FastMCP) -> None: ...


class McpServerApp:
    def __init__(self, name: str, host: str, port: int):
        self.server = FastMCP(name=name)
        self.host = host
        self.port = port

    def register_toolkit(self, toolkit: McpToolkit) -> None:
        toolkit.register(self.server)

    def run(self, transport: str = "streamable-http") -> None:
        self.server.run(transport=transport, host=self.host, port=self.port)

