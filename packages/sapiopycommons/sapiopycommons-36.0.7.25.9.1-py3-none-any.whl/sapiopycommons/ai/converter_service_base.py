from __future__ import annotations

import traceback
from abc import ABC, abstractmethod

from grpc import ServicerContext

from sapiopycommons.ai.protoapi.agent.item.item_container_pb2 import ContentTypePbo, StepItemContainerPbo
from sapiopycommons.ai.protoapi.pipeline.converter.converter_pb2 import ConverterDetailsResponsePbo, ConvertResponsePbo, \
    ConvertRequestPbo, ConverterDetailsRequestPbo, ContentTypePairPbo
from sapiopycommons.ai.protoapi.pipeline.converter.converter_pb2_grpc import ConverterServiceServicer
from sapiopycommons.files.temp_files import TempFileHandler


class ConverterServiceBase(ConverterServiceServicer, ABC):
    debug_mode: bool = False

    def GetConverterDetails(self, request: ConverterDetailsRequestPbo, context: ServicerContext) \
            -> ConverterDetailsResponsePbo:
        try:
            supported_types: list[ContentTypePairPbo] = []
            for c in self.register_converters():
                converter = c(self.debug_mode)
                supported_types.append(ContentTypePairPbo(
                    converter_name=converter.name(),
                    input_content_type=converter.input_type_pbo(),
                    output_content_type=converter.output_type_pbo()
                ))
            return ConverterDetailsResponsePbo(supported_types=supported_types, service_name=self.name())
        except Exception as e:
            print(f"CRITICAL ERROR: {e}")
            print(traceback.format_exc())
            return ConverterDetailsResponsePbo()

    def ConvertContent(self, request: ConvertRequestPbo, context: ServicerContext) -> ConvertResponsePbo:
        try:
            input_container: StepItemContainerPbo = request.item_container
            input_type: ContentTypePbo = input_container.content_type
            target_type: ContentTypePbo = request.target_content_type

            use_converter: ConverterBase | None = None
            for c in self.register_converters():
                converter = c(self.debug_mode)
                if converter.can_convert(input_type, target_type):
                    use_converter = converter
                    break
            if use_converter is None:
                raise ValueError(f"No converter found for converting {input_type.name} ({', '.join(input_type.extensions)}) "
                                 f"to {target_type.name} ({', '.join(target_type.extensions)}).")

            return ConvertResponsePbo(item_container=self.run(use_converter, input_container))
        except Exception as e:
            print(f"CRITICAL ERROR: {e}")
            print(traceback.format_exc())
            return ConvertResponsePbo()

    @staticmethod
    @abstractmethod
    def name() -> str:
        """
        :return: The name of this converter service.
        """
        pass

    @abstractmethod
    def register_converters(self) -> list[type[ConverterBase]]:
        """
        Register converter types with this service. Provided converters should implement the ConverterBase class.

        :return: A list of converters to register to this service.
        """
        pass

    def run(self, converter: ConverterBase, input_container: StepItemContainerPbo) -> StepItemContainerPbo:
        try:
            return converter.convert(input_container)
        finally:
            # Clean up any temporary files created by the converter. If in debug mode, then log the files instead
            # so that they can be manually inspected.
            if self.debug_mode:
                print("Temporary files/directories created during converter execution:")
                for directory in converter.temp_data.directories:
                    print(f"\tDirectory: {directory}")
                for file in converter.temp_data.files:
                    print(f"\tFile: {file}")
            else:
                converter.temp_data.cleanup()


class ConverterBase(ABC):
    temp_data: TempFileHandler
    debug_mode: bool

    def __init__(self, debug_mode: bool):
        self.temp_data = TempFileHandler()
        self.debug_mode = debug_mode

    def name(self) -> str:
        """
        :return: The name of this converter, typically in the format "<input_type> to <output_type>".
        """
        return self.input_type() + " to " + self.output_type()

    def input_type_pbo(self) -> ContentTypePbo:
        """
        :return: The input content type this converter accepts as a ContentTypePbo.
        """
        return ContentTypePbo(name=self.input_type(), extensions=self.input_file_extensions())

    def output_type_pbo(self) -> ContentTypePbo:
        """
        :return: The output content type this converter produces as a ContentTypePbo.
        """
        return ContentTypePbo(name=self.output_type(), extensions=self.output_file_extensions())

    @abstractmethod
    def input_type(self) -> str:
        """
        :return: The input content type this converter accepts.
        """
        pass

    @abstractmethod
    def input_file_extensions(self) -> list[str]:
        """
        :return: A list of file extensions this converter accepts as input.
        """
        pass

    @abstractmethod
    def output_type(self) -> str:
        """
        :return: The output content type this converter produces.
        """
        pass

    @abstractmethod
    def output_file_extensions(self) -> list[str]:
        """
        :return: A list of file extensions this converter produces as output.
        """
        pass

    def can_convert(self, input_type: ContentTypePbo, target_type: ContentTypePbo) -> bool:
        """
        Check if this converter can convert from the input type to the target type.

        :param input_type: The input content type.
        :param target_type: The target content type.
        :return: True if this converter can convert from the input type to the target type, False otherwise.
        """
        return (self.input_type().lower() == input_type.name.lower()
                and self.output_type().lower() == target_type.name.lower())

    @abstractmethod
    def convert(self, content: StepItemContainerPbo) -> StepItemContainerPbo:
        """
        Convert the provided content from the input type to the output type.

        :param content: The content to convert.
        :return: The converted content.
        """
        pass
