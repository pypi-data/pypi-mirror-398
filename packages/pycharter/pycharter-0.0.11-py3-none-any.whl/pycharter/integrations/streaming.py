"""
Generic streaming validator for any streaming source.

This module provides a generic adapter for validating data from any
streaming source that implements the iterator protocol.
"""

from typing import Any, Callable, Dict, Iterator, Optional, Union

from typing import Iterator

from pycharter.contract_parser import ContractMetadata, parse_contract, parse_contract_file
from pycharter.runtime_validator.validator_core import (
    ValidationResult,
    validate,
)
from pycharter.runtime_validator.wrappers import get_model_from_contract


class StreamValidator:
    """
    Generic streaming validator for any iterator-based data source.

    This class provides a simple way to validate data from any streaming
    source that implements the iterator protocol.

    Example:
        >>> from pycharter.integrations import StreamValidator
        >>> 
        >>> class MyStreamSource:
        ...     def __iter__(self):
        ...         yield {"name": "Alice", "age": 30}
        ...         yield {"name": "Bob", "age": 25}
        >>> 
        >>> validator = StreamValidator("user_contract.yaml")
        >>> for result in validator.validate_stream(MyStreamSource()):
        ...     if result.is_valid:
        ...         process(result.data)
    """

    def __init__(
        self,
        contract: Union[str, Dict[str, Any], ContractMetadata],
        strict: bool = False,
    ):
        """
        Initialize stream validator.

        Args:
            contract: Contract file path, dict, or ContractMetadata
            strict: If True, raise exception on first validation error
        """
        self.model = get_model_from_contract(contract)
        self.strict = strict

    def validate_stream(
        self,
        data_stream: Iterator[Dict[str, Any]],
        yield_invalid: bool = False,
        on_valid: Optional[Callable[[Any], None]] = None,
        on_invalid: Optional[Callable[[Any], None]] = None,
    ) -> Iterator[ValidationResult]:
        """
        Validate a stream of data.

        Args:
            data_stream: Iterator/generator of data dictionaries
            yield_invalid: If True, yield invalid results
            on_valid: Optional callback for valid records
            on_invalid: Optional callback for invalid records

        Yields:
            ValidationResult objects
        """
        for data in data_stream:
            result = validate(self.model, data, strict=self.strict)
            
            if result.is_valid and on_valid:
                on_valid(result.data)
            elif not result.is_valid and on_invalid:
                on_invalid(result)
            
            if result.is_valid or yield_invalid:
                yield result
            
            if self.strict and not result.is_valid:
                break

    def validate_record(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Validate a single record.

        Args:
            data: Data dictionary to validate

        Returns:
            ValidationResult object
        """
        return validate(self.model, data, strict=self.strict)

