import base64
import dataclasses
from typing import Any

from databind.core.dataclasses import dataclass
from databind.json import loads
from sapiopylib.rest.utils.singletons import SapioContextManager


@dataclasses.dataclass
class ProcessAssayPlateRequest:
    """
    A request to process the results of assay plate reader with a configuration set in Sapio.

    Attributes:
        num_rows (int): The number of rows in the plate.
        num_columns (int): The number of columns in the plate.
        plate_ids_in_context (list[str]): List of plate IDs that are in context for this request.
        filename (str): The name of the file containing the assay data.
        file_data (bytes): The binary content of the file.
        plate_reader_config_name (str): The name of the plate reader configuration to use.
    """
    num_rows: int
    num_columns: int
    plate_ids_in_context: list[str] | None
    filename: str
    file_data: bytes
    plate_reader_config_name: str

    def to_json(self) -> dict[str, Any]:
        return {
            "numRows": self.num_rows,
            "numCols": self.num_columns,
            "plateIdsInContext": self.plate_ids_in_context,
            "fileName": self.filename,
            "fileDataBase64": base64.b64encode(self.file_data).decode('utf-8'),
            "plateReaderName": self.plate_reader_config_name
        }


@dataclass
class AssayPlateResultIdent:
    plateId: str
    channelIdOrBlock: str
    kineticAssaySeconds: float | None


@dataclass
class AssayResultDatum:
    """
    Describes the data received from an assay plate reader.
    Most of the time, the data is a single value, but sometimes it can be multiple values, especially for kinetic data.
    """
    DEFAULT_PROPERTY_NAME: str = "read"
    rowPosition: str
    columnPosition: str
    valueByPropertyName: dict[str, float]
    textValueByPropertyName: dict[str, str]


@dataclass
class AssayPlateResult:
    """
    Assay plate load result for a single plate in a file. A file can have more than one of this result if it has multiple plate of data in a single file.
    """
    resultIdent: AssayPlateResultIdent
    numRows: int
    numColumns: int
    resultDatum: list[AssayResultDatum]


@dataclass
class AssayFileLoadResult:
    """
    The entire top-level file loading result for an assay plate reader file.
    """
    filename: str
    plateResultList: list[AssayPlateResult]


class AssayPlateReader(SapioContextManager):
    """
    This class contains services for Sapio Assay Plate Reader.
    """

    def process_plate_reader_data(self, request: ProcessAssayPlateRequest) -> AssayFileLoadResult:
        """
        Processes the assay plate reader data using provided request into a structured result using configuration defined in Sapio.
        """
        payload = request.to_json()
        response = self.user.plugin_post("assayplatereader/process", payload=payload)
        self.user.raise_for_status(response)
        return loads(response.text, AssayFileLoadResult)
