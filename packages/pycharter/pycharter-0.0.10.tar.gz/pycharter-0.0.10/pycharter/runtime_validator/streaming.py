"""
Streaming validation support for data in motion.

This module provides iterator-based validation for streaming data pipelines,
enabling validation of data as it flows through systems before persistence.
"""

from typing import Any, Callable, Dict, Iterator, Optional, Type

from pydantic import BaseModel

from pycharter.runtime_validator.validator import ValidationResult, validate


def validate_stream(
    model: Type[BaseModel],
    data_stream: Iterator[Dict[str, Any]],
    strict: bool = False,
    yield_invalid: bool = False,
    on_valid: Optional[Callable[[BaseModel], None]] = None,
    on_invalid: Optional[Callable[[ValidationResult], None]] = None,
) -> Iterator[ValidationResult]:
    """
    Validate a stream of data records.

    This function validates data as it streams through, making it ideal for
    validating data in motion before it reaches persistent storage.

    Args:
        model: Pydantic model class (generated from JSON Schema)
        data_stream: Iterator/generator of data dictionaries
        strict: If True, raise exception on first validation error
        yield_invalid: If True, yield invalid results; if False, skip them
        on_valid: Optional callback function called with validated data for each valid record
        on_invalid: Optional callback function called with ValidationResult for each invalid record

    Yields:
        ValidationResult objects as data is validated

    Example:
        >>> from pycharter import get_model_from_contract, validate_stream
        >>> UserModel = get_model_from_contract("user_contract.yaml")
        >>> 
        >>> def data_generator():
        ...     yield {"name": "Alice", "age": 30}
        ...     yield {"name": "Bob", "age": 25}
        ... 
        >>> for result in validate_stream(UserModel, data_generator()):
        ...     if result.is_valid:
        ...         print(f"Valid: {result.data.name}")
        ...     else:
        ...         print(f"Invalid: {result.errors}")
    """
    for data in data_stream:
        result = validate(model, data, strict=strict)
        
        # Call callbacks if provided
        if result.is_valid and on_valid:
            on_valid(result.data)
        elif not result.is_valid and on_invalid:
            on_invalid(result)
        
        # Yield based on configuration
        if result.is_valid or yield_invalid:
            yield result
        
        # Stop on first error if strict mode
        if strict and not result.is_valid:
            break


def validate_batch_parallel(
    model: Type[BaseModel],
    data_list: list[Dict[str, Any]],
    max_workers: int = 4,
    chunk_size: int = 1000,
    strict: bool = False,
) -> list[ValidationResult]:
    """
    Parallel batch validation for large datasets.

    This function splits the data into chunks and validates them in parallel,
    making it efficient for high-throughput scenarios.

    Args:
        model: Pydantic model class
        data_list: List of data dictionaries to validate
        max_workers: Maximum number of worker threads
        chunk_size: Number of records per chunk
        strict: If True, stop on first validation error

    Returns:
        List of ValidationResult objects

    Example:
        >>> results = validate_batch_parallel(
        ...     UserModel,
        ...     large_data_list,
        ...     max_workers=8,
        ...     chunk_size=500
        ... )
        >>> valid_count = sum(1 for r in results if r.is_valid)
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    def validate_chunk(chunk: list[Dict[str, Any]]) -> list[ValidationResult]:
        """Validate a chunk of data."""
        chunk_results = []
        for data in chunk:
            result = validate(model, data, strict=strict)
            chunk_results.append(result)
            if strict and not result.is_valid:
                break
        return chunk_results

    # Split data into chunks
    chunks = [
        data_list[i : i + chunk_size]
        for i in range(0, len(data_list), chunk_size)
    ]

    # Validate chunks in parallel
    all_results: list[ValidationResult] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_chunk = {
            executor.submit(validate_chunk, chunk): chunk for chunk in chunks
        }

        for future in as_completed(future_to_chunk):
            try:
                chunk_results = future.result()
                all_results.extend(chunk_results)
                # If strict mode and we found an error, stop processing remaining chunks
                if strict and any(not r.is_valid for r in chunk_results):
                    # Cancel remaining futures
                    for f in future_to_chunk:
                        f.cancel()
                    break
            except Exception as e:
                # If chunk validation fails, create error results
                chunk = future_to_chunk[future]
                for data in chunk:
                    all_results.append(
                        ValidationResult(
                            is_valid=False,
                            errors=[f"Chunk validation error: {str(e)}"],
                        )
                    )

    return all_results


class StreamingValidator:
    """
    Optimized validator for high-throughput streaming scenarios.

    This class provides:
    - Model caching for efficient repeated validation
    - Streaming validation with optional parallelization
    - Callback support for real-time processing
    - Statistics tracking (validation count, success rate, etc.)

    Example:
        >>> from pycharter import get_model_from_contract, StreamingValidator
        >>> 
        >>> UserModel = get_model_from_contract("user_contract.yaml")
        >>> validator = StreamingValidator(
        ...     UserModel,
        ...     on_valid=lambda data: send_to_database(data),
        ...     on_invalid=lambda result: send_to_dlq(result)
        ... )
        >>> 
        >>> # Single record validation
        >>> result = validator.validate_record({"name": "Alice", "age": 30})
        >>> 
        >>> # Stream validation
        >>> for result in validator.validate_stream(data_stream()):
        ...     process(result)
        >>> 
        >>> # Check statistics
        >>> print(f"Success rate: {validator.success_rate:.2%}")
    """

    def __init__(
        self,
        model: Type[BaseModel],
        on_valid: Optional[Callable[[BaseModel], None]] = None,
        on_invalid: Optional[Callable[[ValidationResult], None]] = None,
        strict: bool = False,
    ):
        """
        Initialize streaming validator.

        Args:
            model: Pydantic model class (cached for reuse)
            on_valid: Optional callback function called with validated data for each valid record
            on_invalid: Optional callback function called with ValidationResult for each invalid record
            strict: If True, raise exception on validation error
        """
        self.model = model
        self.on_valid = on_valid
        self.on_invalid = on_invalid
        self.strict = strict
        self._validation_count = 0
        self._valid_count = 0
        self._invalid_count = 0

    def validate_record(
        self,
        data: Dict[str, Any],
        strict: Optional[bool] = None,
        on_valid: Optional[Callable[[BaseModel], None]] = None,
        on_invalid: Optional[Callable[[ValidationResult], None]] = None,
    ) -> ValidationResult:
        """
        Validate a single record with optional callbacks.

        Args:
            data: Data dictionary to validate
            strict: If True, raise exception on validation error (overrides instance setting)
            on_valid: Optional callback for this validation (overrides instance callback)
            on_invalid: Optional callback for this validation (overrides instance callback)

        Returns:
            ValidationResult object
        """
        self._validation_count += 1
        strict_mode = strict if strict is not None else self.strict
        result = validate(self.model, data, strict=strict_mode)

        # Use provided callbacks or instance callbacks
        valid_callback = on_valid or self.on_valid
        invalid_callback = on_invalid or self.on_invalid

        if result.is_valid:
            self._valid_count += 1
            if valid_callback:
                valid_callback(result.data)
        else:
            self._invalid_count += 1
            if invalid_callback:
                invalid_callback(result)

        return result

    def validate_stream(
        self,
        data_stream: Iterator[Dict[str, Any]],
        strict: Optional[bool] = None,
        yield_invalid: bool = False,
        parallel: bool = False,
        max_workers: int = 4,
        on_valid: Optional[Callable[[BaseModel], None]] = None,
        on_invalid: Optional[Callable[[ValidationResult], None]] = None,
    ) -> Iterator[ValidationResult]:
        """
        Validate a stream of data records.

        Args:
            data_stream: Iterator/generator of data dictionaries
            strict: If True, raise exception on first validation error (overrides instance setting)
            yield_invalid: If True, yield invalid results; if False, skip them
            parallel: If True, use parallel processing (requires converting stream to list)
            max_workers: Maximum number of worker threads (if parallel=True)
            on_valid: Optional callback for valid records (overrides instance callback)
            on_invalid: Optional callback for invalid records (overrides instance callback)

        Yields:
            ValidationResult objects

        Note:
            Parallel mode requires loading the entire stream into memory first.
            Use only for bounded streams or when memory is not a concern.
        """
        strict_mode = strict if strict is not None else self.strict
        valid_callback = on_valid or self.on_valid
        invalid_callback = on_invalid or self.on_invalid

        if parallel:
            # For parallel processing, we need to convert stream to list
            # This is a trade-off: parallelization vs memory efficiency
            data_list = list(data_stream)
            results = validate_batch_parallel(
                self.model, data_list, max_workers=max_workers, strict=strict_mode
            )
            for result in results:
                self._validation_count += 1
                if result.is_valid:
                    self._valid_count += 1
                    if valid_callback:
                        valid_callback(result.data)
                else:
                    self._invalid_count += 1
                    if invalid_callback:
                        invalid_callback(result)
                if result.is_valid or yield_invalid:
                    yield result
        else:
            # Streaming mode - memory efficient
            for data in data_stream:
                result = self.validate_record(
                    data, strict=strict_mode, on_valid=valid_callback, on_invalid=invalid_callback
                )
                if result.is_valid or yield_invalid:
                    yield result
                if strict_mode and not result.is_valid:
                    break

    @property
    def validation_count(self) -> int:
        """Get total number of validations performed."""
        return self._validation_count

    @property
    def valid_count(self) -> int:
        """Get number of valid records."""
        return self._valid_count

    @property
    def invalid_count(self) -> int:
        """Get number of invalid records."""
        return self._invalid_count

    @property
    def success_rate(self) -> float:
        """Get success rate (0.0 to 1.0)."""
        if self._validation_count == 0:
            return 0.0
        return self._valid_count / self._validation_count

