import argparse
import logging
import subprocess
import sys
from typing import List

from pygls.protocol import JsonRPCProtocol
from pygls.server import Server

from lsp_devtools.agent import Agent
from lsp_devtools.agent import logger
from lsp_devtools.handlers import LspHandler
from lsp_devtools.handlers import LspMessage


class WSHandler(LspHandler):
    """Logging handler that forwards captured LSP messages through to the web socket
    client."""

    def __init__(self, server: Server, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.server = server

    def handle_message(self, message: LspMessage):
        self.server.lsp.notify(
            "$/lspMessage",
            {
                "session": message.session,
                "timestamp": message.timestamp,
                "source": message.source,
                "id": message.id,
                "method": message.method,
                "params": message.params,
                "result": message.result,
                "error": message.error,
            },
        )


def agent(args, extra: List[str]):

    if extra is None:
        print("Missing server start command", file=sys.stderr)
        return 1

    process = subprocess.Popen(extra, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    server = Server(protocol_cls=JsonRPCProtocol)

    handler = WSHandler(server)
    handler.setLevel(logging.INFO)

    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    agent = Agent(process, sys.stdin.buffer, sys.stdout.buffer)
    agent.start()

    server.start_ws(args.host, args.port)


def cli(commands: argparse._SubParsersAction):
    cmd = commands.add_parser(
        "agent",
        help="interactively inspect an LSP session",
        description="""\
This command runs the given language server as a subprocess, wrapping it in a websocket
server that can be used to inspect and manipulate the session interactively.
""",
    )  # type: argparse.ArgumentParser

    cmd.add_argument(
        "--host",
        help="the host to run the websocket server on.",
        default="localhost",
    )
    cmd.add_argument(
        "-p",
        "--port",
        help="the port to run the websocket server on",
        default=8765,
    )

    cmd.set_defaults(run=agent)
