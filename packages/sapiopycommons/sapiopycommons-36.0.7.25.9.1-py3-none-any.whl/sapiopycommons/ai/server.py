from __future__ import annotations

import asyncio
from argparse import ArgumentParser
from typing import Any

import grpc

from sapiopycommons.ai.converter_service_base import ConverterServiceBase
from sapiopycommons.ai.protoapi.pipeline.converter.converter_pb2_grpc import add_ConverterServiceServicer_to_server, \
    ConverterServiceServicer
from sapiopycommons.ai.protoapi.pipeline.script.script_pb2_grpc import add_ScriptServiceServicer_to_server, \
    ScriptServiceServicer
from sapiopycommons.ai.protoapi.agent.agent_pb2_grpc import add_AgentServiceServicer_to_server, AgentServiceServicer
from sapiopycommons.ai.agent_service_base import AgentServiceBase


class SapioGrpcServer:
    """
    A gRPC server for handling the various Sapio gRPC services.
    """
    port: int
    options: list[tuple[str, Any]]
    debug_mode: bool
    _converter_services: list[ConverterServiceServicer]
    _script_services: list[ScriptServiceServicer]
    _agent_services: list[AgentServiceServicer]

    @staticmethod
    def args_parser() -> ArgumentParser:
        """
        Create an argument parser for the gRPC server.

        :return: The argument parser.
        """
        parser = ArgumentParser()
        parser.add_argument("--debug_mode", "-d", action="store_true")
        parser.add_argument("--port", "-p", default=50051, type=int)
        parser.add_argument("--message_mb_size", "-s", default=1024, type=int)
        return parser

    @staticmethod
    def from_args(options: list[tuple[str, Any]] | None = None) -> SapioGrpcServer:
        return SapioGrpcServer(options=options, **vars(SapioGrpcServer.args_parser().parse_args()))

    def __init__(self, port: int = 50051, message_mb_size: int = 1024, debug_mode: bool = False,
                 options: list[tuple[str, Any]] | None = None) -> None:
        """
        Initialize the gRPC server with the specified port and message size.

        :param port: The port to listen on for incoming gRPC requests.
        :param message_mb_size: The maximum size of a sent or received message in megabytes.
        :param debug_mode: Sets the debug mode for services.
        :param options: Additional gRPC server options to set. This should be a list of tuples where the first item is
            the option name and the second item is the option value.
        """
        if isinstance(port, str):
            port = int(port)
        self.port = port
        self.options = [
            ('grpc.max_send_message_length', message_mb_size * 1024 * 1024),
            ('grpc.max_receive_message_length', message_mb_size * 1024 * 1024)
        ]
        if options:
            self.options.extend(options)
        self.debug_mode = debug_mode
        if debug_mode:
            print("Debug mode is enabled.")
        self._converter_services = []
        self._script_services = []
        self._agent_services = []

    def update_message_size(self, message_mb_size: int) -> None:
        """
        Update the maximum message size for the gRPC server.

        :param message_mb_size: The new maximum message size in megabytes.
        """
        for i, (option_name, _) in enumerate(self.options):
            if option_name in ('grpc.max_send_message_length', 'grpc.max_receive_message_length'):
                self.options[i] = (option_name, message_mb_size * 1024 * 1024)

    def add_converter_service(self, service: ConverterServiceBase) -> None:
        """
        Add a converter service to the gRPC server.

        :param service: The converter service to register with the server.
        """
        service.debug_mode = self.debug_mode
        self._converter_services.append(service)

    def add_script_service(self, service: ScriptServiceServicer) -> None:
        """
        Add a script service to the gRPC server.

        :param service: The script service to register with the server.
        """
        self._script_services.append(service)

    def add_agent_service(self, service: AgentServiceBase) -> None:
        """
        Add an agent service to the gRPC server.

        :param service: The agent service to register with the server.
        """
        service.debug_mode = self.debug_mode
        self._agent_services.append(service)

    def start(self) -> None:
        """
        Start the gRPC server for the provided servicers.
        """
        if not (self._converter_services or self._script_services or self._agent_services):
            raise ValueError("No services have been added to the server. Use add_converter_service, add_script_service,"
                             "or add_agent_service to register a service before starting the server.")

        async def serve():
            server = grpc.aio.server(options=self.options)

            for service in self._converter_services:
                print(f"Registering Converter service: {service.__class__.__name__}")
                add_ConverterServiceServicer_to_server(service, server)
            for service in self._script_services:
                print(f"Registering Script service: {service.__class__.__name__}")
                add_ScriptServiceServicer_to_server(service, server)
            for service in self._agent_services:
                print(f"Registering Agent service: {service.__class__.__name__}")
                add_AgentServiceServicer_to_server(service, server)

            from grpc_health.v1 import health_pb2, health_pb2_grpc
            from grpc_health.v1.health import HealthServicer
            health_servicer = HealthServicer()
            health_servicer.set("", health_pb2.HealthCheckResponse.ServingStatus.SERVING)
            health_servicer.set("ScriptService", health_pb2.HealthCheckResponse.ServingStatus.SERVING)
            health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)

            server.add_insecure_port(f"[::]:{self.port}")
            await server.start()
            print(f"Server started, listening on {self.port}")
            try:
                await server.wait_for_termination()
            finally:
                print("Stopping server...")
                await server.stop(0)
                print("Server stopped.")

        try:
            asyncio.run(serve())
        except KeyboardInterrupt:
            print("Server stopped by user.")
        except Exception as e:
            print(f"An error occurred: {e}")
