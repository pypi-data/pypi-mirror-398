"""
Kafka integration for validating messages in motion.

This module provides integration with Apache Kafka for validating
messages as they flow through Kafka topics.
"""

from typing import Any, Callable, Dict, Iterator, Optional, Union

from pycharter.contract_parser import ContractMetadata, parse_contract, parse_contract_file
from pycharter.runtime_validator.validator_core import (
    ValidationResult,
    validate,
)
from pycharter.runtime_validator.wrappers import get_model_from_contract


class KafkaValidator:
    """
    Kafka message validator for validating messages in motion.

    This class validates Kafka messages against data contracts as they
    are consumed from topics, enabling validation before persistence.

    Example:
        >>> from pycharter.integrations import KafkaValidator
        >>> 
        >>> validator = KafkaValidator(
        ...     contract="user_contract.yaml",
        ...     kafka_config={"bootstrap_servers": "localhost:9092"}
        ... )
        >>> 
        >>> for message in validator.consume_and_validate("user-topic"):
        ...     if message.is_valid:
        ...         process(message.data)
        ...     else:
        ...         send_to_dlq(message)
    """

    def __init__(
        self,
        contract: Union[str, Dict[str, Any], ContractMetadata],
        kafka_config: Optional[Dict[str, Any]] = None,
        strict: bool = False,
    ):
        """
        Initialize Kafka validator.

        Args:
            contract: Contract file path, dict, or ContractMetadata
            kafka_config: Optional Kafka consumer configuration
            strict: If True, raise exception on validation error

        Note:
            Requires kafka-python package: pip install kafka-python
        """
        try:
            from kafka import KafkaConsumer  # type: ignore[import-untyped]
        except ImportError:
            raise ImportError(
                "kafka-python is required for Kafka integration. "
                "Install with: pip install kafka-python"
            )

        self.model = get_model_from_contract(contract)
        self.kafka_config = kafka_config or {}
        self.strict = strict
        self._consumer: Optional[KafkaConsumer] = None

    def consume_and_validate(
        self,
        topic: str,
        group_id: Optional[str] = None,
        yield_invalid: bool = False,
        on_valid: Optional[Callable[[Any], None]] = None,
        on_invalid: Optional[Callable[[Any], None]] = None,
    ) -> Iterator[ValidationResult]:
        """
        Consume messages from Kafka topic and validate them.

        Args:
            topic: Kafka topic name
            group_id: Optional consumer group ID
            yield_invalid: If True, yield invalid results
            on_valid: Optional callback for valid messages
            on_invalid: Optional callback for invalid messages

        Yields:
            ValidationResult objects with message data

        Example:
            >>> for result in validator.consume_and_validate("user-topic"):
            ...     if result.is_valid:
            ...         await process_message(result.data)
        """
        from kafka import KafkaConsumer  # type: ignore[import-untyped]

        # Create consumer
        consumer_config = self.kafka_config.copy()
        if group_id:
            consumer_config["group_id"] = group_id

        consumer = KafkaConsumer(topic, **consumer_config)
        self._consumer = consumer

        try:
            for kafka_message in consumer:
                # Extract message value (assuming JSON)
                import json

                try:
                    if isinstance(kafka_message.value, bytes):
                        data = json.loads(kafka_message.value.decode("utf-8"))
                    elif isinstance(kafka_message.value, str):
                        data = json.loads(kafka_message.value)
                    else:
                        data = kafka_message.value

                    # Validate message
                    result = validate(self.model, data, strict=self.strict)

                    # Call callbacks
                    if result.is_valid and on_valid:
                        on_valid(result.data)
                    elif not result.is_valid and on_invalid:
                        on_invalid(result)

                    # Yield result
                    if result.is_valid or yield_invalid:
                        yield result

                    if self.strict and not result.is_valid:
                        break

                except (json.JSONDecodeError, ValueError) as e:
                    # Invalid JSON, create error result
                    error_result = ValidationResult(
                        is_valid=False,
                        errors=[f"JSON decode error: {str(e)}"],
                        data=None,
                    )
                    if on_invalid:
                        on_invalid(error_result)
                    if yield_invalid:
                        yield error_result

        finally:
            if self._consumer:
                self._consumer.close()

    def validate_message(self, message_value: Union[str, bytes, Dict[str, Any]]) -> ValidationResult:
        """
        Validate a single Kafka message value.

        Args:
            message_value: Message value (JSON string, bytes, or dict)

        Returns:
            ValidationResult object
        """
        import json

        # Parse message if needed
        if isinstance(message_value, bytes):
            data = json.loads(message_value.decode("utf-8"))
        elif isinstance(message_value, str):
            data = json.loads(message_value)
        else:
            data = message_value

        return validate(self.model, data, strict=self.strict)

    def close(self):
        """Close Kafka consumer."""
        if self._consumer:
            self._consumer.close()
            self._consumer = None

