"""
Async validation support for non-blocking data validation.

This module provides async/await support for validation operations,
enabling non-blocking validation in async data pipelines.
"""

import asyncio
from typing import Any, AsyncIterator, Dict, Iterator, Optional, Type

from pydantic import BaseModel

from pycharter.runtime_validator.validator import ValidationResult, validate


async def validate_async(
    model: Type[BaseModel],
    data: Dict[str, Any],
    strict: bool = False,
) -> ValidationResult:
    """
    Async validation for non-blocking operations.

    This function runs validation in a thread pool executor to avoid
    blocking the event loop, making it suitable for async applications.

    Args:
        model: Pydantic model class (generated from JSON Schema)
        data: Data dictionary to validate
        strict: If True, raise exception on validation error

    Returns:
        ValidationResult object

    Example:
        >>> import asyncio
        >>> from pycharter import get_model_from_contract, validate_async
        >>> 
        >>> async def process_data():
        ...     UserModel = get_model_from_contract("user_contract.yaml")
        ...     result = await validate_async(UserModel, {"name": "Alice", "age": 30})
        ...     if result.is_valid:
        ...         print(f"Valid: {result.data.name}")
        >>> 
        >>> asyncio.run(process_data())
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, validate, model, data, strict)


async def validate_batch_async(
    model: Type[BaseModel],
    data_list: list[Dict[str, Any]],
    strict: bool = False,
    max_concurrent: Optional[int] = None,
) -> list[ValidationResult]:
    """
    Async batch validation with optional concurrency control.

    Args:
        model: Pydantic model class
        data_list: List of data dictionaries to validate
        strict: If True, stop on first validation error
        max_concurrent: Maximum number of concurrent validations (None = unlimited)

    Returns:
        List of ValidationResult objects

    Example:
        >>> async def validate_many():
        ...     results = await validate_batch_async(
        ...         UserModel,
        ...         [{"name": "Alice"}, {"name": "Bob"}],
        ...         max_concurrent=10
        ...     )
        ...     return results
    """
    if max_concurrent:
        # Use semaphore to limit concurrency
        semaphore = asyncio.Semaphore(max_concurrent)

        async def validate_with_semaphore(data: Dict[str, Any]) -> ValidationResult:
            async with semaphore:
                return await validate_async(model, data, strict=strict)

        tasks = [validate_with_semaphore(data) for data in data_list]
    else:
        # No concurrency limit
        tasks = [validate_async(model, data, strict=strict) for data in data_list]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Handle exceptions
    validated_results: list[ValidationResult] = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            validated_results.append(
                ValidationResult(
                    is_valid=False,
                    errors=[f"Validation error: {str(result)}"],
                )
            )
            if strict:
                break
        else:
            validated_results.append(result)
            if strict and not result.is_valid:
                break

    return validated_results


async def validate_stream_async(
    model: Type[BaseModel],
    data_stream: AsyncIterator[Dict[str, Any]],
    strict: bool = False,
    yield_invalid: bool = False,
) -> AsyncIterator[ValidationResult]:
    """
    Async streaming validation.

    Validates data as it streams through async iterators, making it ideal
    for async data pipelines and real-time processing.

    Args:
        model: Pydantic model class
        data_stream: Async iterator of data dictionaries
        strict: If True, raise exception on first validation error
        yield_invalid: If True, yield invalid results

    Yields:
        ValidationResult objects as data is validated

    Example:
        >>> async def async_data_source():
        ...     yield {"name": "Alice", "age": 30}
        ...     yield {"name": "Bob", "age": 25}
        >>> 
        >>> async def process_stream():
        ...     async for result in validate_stream_async(UserModel, async_data_source()):
        ...         if result.is_valid:
        ...             await process_valid_data(result.data)
    """
    async for data in data_stream:
        result = await validate_async(model, data, strict=strict)
        if result.is_valid or yield_invalid:
            yield result
        if strict and not result.is_valid:
            break


class AsyncStreamingValidator:
    """
    Async validator optimized for high-throughput async streaming scenarios.
    """

    def __init__(self, model: Type[BaseModel]):
        """
        Initialize async streaming validator.

        Args:
            model: Pydantic model class (cached for reuse)
        """
        self.model = model
        self._validation_count = 0

    async def validate_record(
        self, data: Dict[str, Any], strict: bool = False
    ) -> ValidationResult:
        """
        Fast async single-record validation.

        Args:
            data: Data dictionary to validate
            strict: If True, raise exception on validation error

        Returns:
            ValidationResult object
        """
        self._validation_count += 1
        return await validate_async(self.model, data, strict=strict)

    async def validate_stream(
        self,
        data_stream: AsyncIterator[Dict[str, Any]],
        strict: bool = False,
        yield_invalid: bool = False,
    ) -> AsyncIterator[ValidationResult]:
        """
        Async streaming validation.

        Args:
            data_stream: Async iterator of data dictionaries
            strict: If True, raise exception on first validation error
            yield_invalid: If True, yield invalid results

        Yields:
            ValidationResult objects
        """
        async for result in validate_stream_async(
            self.model, data_stream, strict=strict, yield_invalid=yield_invalid
        ):
            yield result

    @property
    def validation_count(self) -> int:
        """Get total number of validations performed."""
        return self._validation_count

