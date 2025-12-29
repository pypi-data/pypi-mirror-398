from __future__ import annotations

from abc import ABC
from typing import Any, Callable

from sapiopycommons.ai.test_client import ContainerType
from sapiopycommons.ai.agent_service_base import AgentBase


class InputValidation(ABC):
    """
    A base class for validating the input to an agent.
    """
    index: int
    max_entries: int | None
    allow_empty_input: bool
    allow_empty_entries: bool

    def __init__(self, index: int, max_entries: int | None = None,
                 allow_empty_input: bool = False, allow_empty_entries: bool = False):
        """
        :param index: The index of the input to validate.
        :param max_entries: The maximum number of entries allowed for this input. If None, then there is no limit.
        :param allow_empty_input: If true, then the input can be completely empty.
        :param allow_empty_entries: If true, then individual entries in the input can be empty.
        """
        self.index = index
        self.max_entries = max_entries
        self.allow_empty_input = allow_empty_input
        self.allow_empty_entries = allow_empty_entries


class BinaryValidation(InputValidation):
    """
    A class representing a validation requirement for a binary input.
    """
    func: Callable[[bytes], list[str]] | None

    def __init__(self, index: int, max_entries: int | None = None,
                 allow_empty_input: bool = False, allow_empty_entries: bool = False,
                 func: Callable[[bytes], list[str]] | None = None):
        """
        :param index: The index of the input to validate.
        :param max_entries: The maximum number of entries allowed for this input. If None, then there is no limit.
        :param allow_empty_input: If true, then the input can be completely empty.
        :param allow_empty_entries: If true, then individual entries in the input can be empty
        :param func: An optional function to run on each entry in the input. The function should take the entry as an
            argument, and return a list of error messages if the entry is not valid. If the entry is valid, the function
            should return an empty list. This function will not be called if the input or entry are empty.
        """
        super().__init__(index, max_entries, allow_empty_input, allow_empty_entries)
        self.func = func


class CsvValidation(InputValidation):
    """
    A class representing a validation requirement for a CSV input.
    """
    required_headers: list[str] | None = None

    func: Callable[[dict[str, Any]], list[str]] | None

    def __init__(self, index: int, max_entries: int | None = None,
                 allow_empty_input: bool = False, allow_empty_entries: bool = False,
                 required_headers: list[str] | None = None,
                 func: Callable[[dict[str, Any]], list[str]] | None = None):
        """
        :param index: The index of the input to validate.
        :param max_entries: The maximum number of entries allowed for this input. If None, then there is no limit.
        :param allow_empty_input: If true, then the input can be completely empty.
        :param allow_empty_entries: If true, then individual entries in the input can be empty.
        :param required_headers: A list of headers that must be present in the CSV input. If None, then no header
            validation will be performed.
        :param func: An optional function to run on each entry in the input. The function should take the entry as an
            argument, and return a list of error messages if the entry is not valid. If the entry is valid, the function
            should return an empty list. This function will not be called if the input or entry are empty.
        """
        super().__init__(index, max_entries, allow_empty_input, allow_empty_entries)
        self.required_headers = required_headers
        self.func = func


class JsonValidation(InputValidation):
    """
    A class representing a validation requirement for a JSON input.
    """
    json_requirements: dict[str, JsonKeyValidation]

    func: Callable[[dict[str, Any]], list[str]] | None

    def __init__(self, index: int, max_entries: int | None = None,
                 allow_empty_input: bool = False, allow_empty_entries: bool = False,
                 json_requirements: list[JsonKeyValidation] | None = None,
                 func: Callable[[dict[str, Any]], list[str]] | None = None):
        """
        :param index: The index of the input to validate.
        :param max_entries: The maximum number of entries allowed for this input. If None, then there is no limit.
        :param allow_empty_input: If true, then the input can be completely empty.
        :param allow_empty_entries: If true, then individual entries in the input can be empty.
        :param json_requirements: A list of JSON requirements to validate for JSON inputs. Each requirement
            specifies a key to validate, the expected type of the value for that key, and any nested requirements
            for that key. Only applicable to JSON inputs.
        :param func: An optional function to run on each entry in the input. The function should take the entry as an
            argument, and return a list of error messages if the entry is not valid. If the entry is valid, the function
            should return an empty list. This function will not be called if the input or entry are empty.
        """
        super().__init__(index, max_entries, allow_empty_input, allow_empty_entries)
        self.json_requirements = {}
        if json_requirements:
            for req in json_requirements:
                if req.key in self.json_requirements:
                    raise ValueError(f"Duplicate JSON requirement key {req.key} for input index {index}.")
                self.json_requirements[req.key] = req

        self.func = func


class JsonKeyValidation:
    """
    A class representing a validation requirement for a specific key in a JSON input.
    """
    key: str
    json_type: type
    required: bool
    allow_empty: bool

    list_type: type | None = None
    nested_requirements: dict[str, JsonKeyValidation]

    func: Callable[[str, Any], list[str]] | None = None

    def __init__(self, key: str, json_type: type, required: bool = True, allow_empty: bool = False,
                 list_type: type | None = None, nested_requirements: list[JsonKeyValidation] | None = None,
                 func: Callable[[str, Any], list[str]] | None = None):
        """
        :param key: The key in the JSON input to validate.
        :param json_type: The expected type of the value for this key. This should be one of: str, int, float, bool,
            list, or dict.
        :param required: If true, then this key must be present in the JSON input. If false, then the key is optional,
            but if present, it must still match the other expected criteria.
        :param allow_empty: If true, then the value for this key can be empty (e.g., an empty string, list, or dict).
            If false, then the value must not be empty.
        :param list_type: The expected type of the entries in the list if json_type is list.
        :param nested_requirements: A list of nested JSON requirements to validate for this key if it is a dict. Each
            requirement specifies a key to validate, the expected type of the value for that key, and any nested
            requirements for that key. Only applicable if json_type is dict, or if json_type is list and list_type is
            dict.
        :param func: An optional function to run on the value for this key. The function should take the path and the
            value as arguments, and return a list of error messages if the value is not valid. If the value is valid,
            the function should return an empty list. This function will not be called if the key is missing,
            the value is of the wrong type, or the value is an empty str/list/dict and allow_empty is false.
        """
        self.key = key
        self.json_type = json_type
        self.required = required
        self.allow_empty = allow_empty

        self.list_type = list_type
        self.nested_requirements = {}
        if nested_requirements:
            for req in nested_requirements:
                if req.key in self.nested_requirements:
                    raise ValueError(f"Duplicate nested requirement key {req.key} for JSON key {key}.")
                self.nested_requirements[req.key] = req

        self.func = func

        allowed_types: set[type] = {str, int, float, bool, list, dict}
        if self.json_type not in allowed_types:
            raise ValueError(f"Invalid json_type {self.json_type} for key {key}. Must be one of: "
                             f"{', '.join([t.__name__ for t in allowed_types])}.")
        if self.list_type is not None and self.list_type not in allowed_types:
            raise ValueError(f"Invalid list_type {self.list_type} for key {key}. Must be one of: "
                             f"{', '.join([t.__name__ for t in allowed_types])}.")


class TextValidation(InputValidation):
    """
    A class representing a validation requirement for a text input.
    """
    flatten: bool
    disallowed_characters: str | None = None
    regex: str | None = None

    func: Callable[[str], list[str]] | None = None

    def __init__(self, index: int, max_entries: int | None = None,
                 allow_empty_input: bool = False, allow_empty_entries: bool = False, flatten: bool = False,
                 disallow_characters: str | None = None, regex: str | None = None,
                 func: Callable[[str], list[str]] | None = None):
        """
        :param index: The index of the input to validate.
        :param max_entries: The maximum number of entries allowed for this input. If None, then there is no limit.
        :param allow_empty_input: If true, then the input can be completely empty.
        :param allow_empty_entries: If true, then individual entries in the input can be empty.
        :param flatten: If true, then the input will be flattened before validation
        :param disallow_characters: A string of characters that are not allowed in any entry in the input. If None,
            then no character validation will be performed. This parameter will not be used if the input or entry are
            empty.
        :param regex: An optional regular expression that each entry in the input must fully match. If None, then no
            regex validation will be performed. This parameter will not be used if the input or entry are empty.
        :param func: An optional function to run on each entry in the input. The function should take the entry as an
            arguments, and return a list of error messages if the entry is not valid. If the entry is valid, the
            function should return an empty list. The function will only be called if the entry passes those previous
            checks (e.g. not empty, doesn't include disallowed characters, passes the regex, etc.).
        """
        super().__init__(index, max_entries, allow_empty_input, allow_empty_entries)
        self.flatten = flatten
        self.disallowed_characters = disallow_characters
        self.regex = regex
        self.func = func


class InputValidator:
    """
    A class for validating the inputs to an agent based on their container types and specified validation requirements.
    """
    agent: AgentBase
    requirements: dict[int, InputValidation]

    def __init__(self, agent: AgentBase, requirements: list[InputValidation] | None = None):
        """
        :param agent: The agent to validate the request of.
        :param requirements: A list of validation requirements to apply to the request. If a validation object is
            not provided for a given input, then default validation will be applied. Default validation requires that
            the input is not empty, and that the entries in the input are not empty.
        """
        self.agent = agent
        self.requirements = {}
        if requirements:
            self.add_requirements(requirements)

    def add_requirements(self, requirements: list[InputValidation]) -> None:
        for req in requirements:
            if req.index < 0 or req.index >= len(self.agent.input_configs):
                raise ValueError(f"Validation requirement index {req.index} is out of range for agent "
                                 f"{self.agent.name()} with {len(self.agent.input_configs)} inputs.")
            if req.index in self.requirements:
                raise ValueError(f"Duplicate validation requirement index {req.index} for agent {self.agent.name()}.")
            self.requirements[req.index] = req

    def run(self) -> list[str]:
        """
        Run simple validation on all the inputs based on their container types. This requires the following:
        - The input may not be empty.
        - The entries in the input may not be empty, unless allow_empty is set to true.
        - If provided, the number of entries in the input may not exceed a maximum size.
        - If provided, certain keys must be present in the JSON input, and they must match the above behavior.

        :return: A list of the error messages if the request is not valid. If the request is valid, return an empty
            list.
        """
        errors: list[str] = []
        for i, input_type in enumerate(self.agent.input_container_types):
            match input_type:
                case ContainerType.BINARY:
                    r: InputValidation = self.requirements.get(i, BinaryValidation(i))
                    if not isinstance(r, BinaryValidation):
                        raise ValueError(f"Validation requirement for binary input at index {i} must be a "
                                         f"BinaryValidation object. Got {type(r)} instead.")
                    errors.extend(self.validate_input_binary(i, r))
                case ContainerType.CSV:
                    r: InputValidation = self.requirements.get(i, CsvValidation(i))
                    if not isinstance(r, CsvValidation):
                        raise ValueError(f"Validation requirement for CSV input at index {i} must be a "
                                         f"CsvValidation object. Got {type(r)} instead.")
                    errors.extend(self.validate_input_csv(i, r))
                case ContainerType.JSON:
                    r: InputValidation = self.requirements.get(i, JsonValidation(i))
                    if not isinstance(r, JsonValidation):
                        raise ValueError(f"Validation requirement for JSON input at index {i} must be a "
                                         f"JsonValidation object. Got {type(r)} instead.")
                    errors.extend(self.validate_input_json(i, r))
                case ContainerType.TEXT:
                    r: InputValidation = self.requirements.get(i, TextValidation(i))
                    if not isinstance(r, TextValidation):
                        raise ValueError(f"Validation requirement for text input at index {i} must be a "
                                         f"TextValidation object. Got {type(r)} instead.")
                    errors.extend(self.validate_input_text(i, r))
        return errors

    def validate_input_binary(self, index: int, r: BinaryValidation) -> list[str]:
        """
        Run simple validation on the binary input at the given index.

        :param index: The index of the input to validate.
        :param r: The validation requirement to use for this input.
        :return: A list of error messages if the input is not valid. If the input is valid, return an empty list.
        """
        input_files: list[bytes] = self.agent.get_input_binary(index)
        errors: list[str] = []
        if not input_files:
            if not r.allow_empty_input:
                errors.append(f"Input {index} is empty.")
        elif r.max_entries is not None and len(input_files) > r.max_entries:
            errors.append(f"Input {index} contains {len(input_files)} entries, which exceeds the maximum allowed "
                          f"number of {r.max_entries}.")
        elif not r.allow_empty_entries or r.func:
            for i, entry in enumerate(input_files):
                if not entry.strip():
                    if not r.allow_empty_entries:
                        errors.append(f"Entry {i} of input {index} is empty or contains only whitespace.")
                elif r.func:
                    func_errors: list[str] = r.func(entry)
                    if func_errors:
                        for error in func_errors:
                            errors.append(f"Error in entry {i} of input {index}: {error}")
        return errors

    def validate_input_csv(self, index: int, r: CsvValidation) -> list[str]:
        """
        Run simple validation on the CSV input at the given index.

        :param index: The index of the input to validate.
        :param r: The validation requirement to use for this input.
        :return: A list of error messages if the input is not valid. If the input is valid, return an empty list.
        """
        headers, csv = self.agent.get_input_csv(index)
        headers: list[str]
        csv: list[dict[str, Any]]

        errors: list[str] = []
        if r.required_headers:
            missing_headers: list[str] = [h for h in r.required_headers if h not in headers]
            if missing_headers:
                errors.append(f"Input {index} is missing required headers: {', '.join(missing_headers)}.")

        if not csv:
            if not r.allow_empty_input:
                errors.append(f"Input {index} is empty.")
        elif r.max_entries is not None and len(csv) > r.max_entries:
            errors.append(f"Input {index} contains {len(csv)} entries, which exceeds the maximum allowed "
                          f"number of {r.max_entries}.")
        elif not r.allow_empty_entries or r.func:
            for i, entry in enumerate(csv):
                if not entry or all(not cell.strip() for cell in entry):
                    if not r.allow_empty_entries:
                        errors.append(f"Entry {i} of input {index} is empty or contains only whitespace.")
                elif r.func:
                    func_errors: list[str] = r.func(entry)
                    if func_errors:
                        for error in func_errors:
                            errors.append(f"Error in entry {i} of input {index}: {error}")
        return errors

    def validate_input_json(self, index: int, r: JsonValidation) -> list[str]:
        """
        Run simple validation on the JSON input at the given index.

        :param index: The index of the input to validate.
        :param r: The validation requirement to use for this input.
        :return: A list of error messages if the input is not valid. If the input is valid, return an empty list.
        """
        input_json: list[dict[str, Any]] = self.agent.get_input_json(index)
        errors: list[str] = []
        if not input_json:
            if not r.allow_empty_input:
                errors.append(f"Input {index} is empty.")
        elif r.max_entries is not None and len(input_json) > r.max_entries:
            errors.append(f"Input {index} contains {len(input_json)} entries, which exceeds the maximum allowed "
                          f"number of {r.max_entries}.")
        elif not r.allow_empty_entries or r.func:
            for i, entry in enumerate(input_json):
                if not entry:
                    if not r.allow_empty_entries:
                        errors.append(f"Entry {i} of input {index} is empty.")
                elif r.func:
                    func_errors: list[str] = r.func(entry)
                    if func_errors:
                        for error in func_errors:
                            errors.append(f"Error in entry {i} of input {index}: {error}")

        for key, rk in r.json_requirements.items():
            for i, entry in enumerate(input_json):
                errors.extend(self.validate_input_json_key(entry, rk, f"input[{index}][{i}]"))

        return errors

    def validate_input_json_key(self, data: dict[str, Any], rk: JsonKeyValidation, path: str) -> list[str]:
        """
        Recursively validate a JSON key in a JSON object.

        :param data: The JSON object to validate.
        :param rk: The JSON key validation requirement to use.
        :param path: The path to the current JSON object, for error reporting.
        :return: A list of error messages if the JSON object is not valid. If the JSON object is valid, return an empty
            list.
        """
        errors: list[str] = []
        if rk.key not in data:
            if rk.required:
                errors.append(f"Missing required key '{rk.key}' at path '{path}'.")
            return errors

        value: Any = data[rk.key]
        if not isinstance(value, rk.json_type):
            errors.append(f"Key '{rk.key}' at path '{path}' is expected to be of type "
                          f"{rk.json_type.__name__}, but got {type(value).__name__}.")
            return errors

        if isinstance(value, (str, list, dict)) and not value:
            if not rk.allow_empty:
                errors.append(f"Key '{rk.key}' at path '{path}' is empty, but empty values are not allowed.")
            return errors

        correct_type: bool = True
        if rk.json_type is list and rk.list_type is not None:
            if not isinstance(value, list):
                raise RuntimeError("This should never happen; value was already checked to be of type list.")
            for i, item in enumerate(value):
                if not isinstance(item, rk.list_type):
                    errors.append(f"Entry {i} of list key '{rk.key}' at path '{path}' is expected to be of type "
                                  f"{rk.list_type.__name__}, but got {type(item).__name__}.")
                    correct_type = False
                elif rk.list_type is dict and rk.nested_requirements:
                    if not isinstance(item, dict):
                        raise RuntimeError("This should never happen; item was already checked to be of type dict.")
                    for nk, nrk in rk.nested_requirements.items():
                        errors.extend(self.validate_input_json_key(item, nrk, f"{path}.{rk.key}[{i}]"))

        elif rk.json_type is dict and rk.nested_requirements:
            if not isinstance(value, dict):
                raise RuntimeError("This should never happen; value was already checked to be of type dict.")
            for nk, nrk in rk.nested_requirements.items():
                errors.extend(self.validate_input_json_key(value, nrk, f"{path}.{rk.key}"))

        if rk.func and correct_type:
            errors.extend(rk.func(f"{path}.{rk.key}", value))

        return errors

    def validate_input_text(self, index: int, r: TextValidation) -> list[str]:
        """
        Run simple validation on the binary input at the given index.

        :param index: The index of the input to validate.
        :param r: The validation requirement to use for this input.
        :return: A list of error messages if the input is not valid. If the input is valid, return an empty list.
        """
        input_text: list[str] = self.agent.get_input_text(index)
        if r.flatten:
            input_text = self.agent.flatten_text(input_text)

        errors: list[str] = []
        if not input_text:
            if not r.allow_empty_input:
                errors.append(f"Input {index} is empty.")
        elif r.max_entries is not None and len(input_text) > r.max_entries:
            errors.append(f"Input {index} contains {len(input_text)} entries, which exceeds the maximum allowed "
                          f"number of {r.max_entries}.")
        elif not r.allow_empty_entries or r.regex or r.func:
            for i, entry in enumerate(input_text):
                if not entry.strip():
                    if not r.allow_empty_entries:
                        errors.append(f"Entry {i} of input {index} is empty or contains only whitespace.")
                elif r.disallowed_characters:
                    for c in r.disallowed_characters:
                        # Replace special characters with their escaped versions for better error messages.
                        if c == "\r":
                            c = r"\r"
                        elif c == '\n':
                            c = r"\n"
                        elif c == "\t":
                            c = r"\t"
                        if c in entry:
                            errors.append(f"Entry {i} of input {index} contains disallowed character '{c}'.")
                elif r.regex:
                    import re
                    if not re.fullmatch(r.regex, entry):
                        errors.append(f"Entry {i} of input {index} does not fully match the expected regex format "
                                      f"{r.regex}.")
                elif r.func:
                    func_errors: list[str] = r.func(entry)
                    if func_errors:
                        for error in func_errors:
                            errors.append(f"Error in entry {i} of input {index}: {error}")
        if errors and r.flatten:
            errors.append(f"Note that input flattening is enabled for input {index}, which may increase the number "
                          f"of entries reported in the above errors. Flattening splits each entry on newlines, removes "
                          f"empty lines, and iterates over every line in the input as opposed to each entry as a whole.")
        return errors
