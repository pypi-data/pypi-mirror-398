
from pydantic import AliasChoices, Field

from application.settings.base_settings import GeneralBaseSettings


class KafkaBaseConfig(GeneralBaseSettings):
    """Base class for common Kafka configuration fields."""
    bootstrap_servers: str = Field(
        default="localhost:9092",
        alias="KAFKA_BOOTSTRAP_SERVERS",
        validation_alias=AliasChoices("KAFKA_BOOTSTRAP_SERVERS",
                                      "kafka_bootstrap_servers")
    )
    client_id: str = Field(
        alias="HOSTNAME",
        validation_alias=AliasChoices("HOSTNAME")
    )
    security_protocol: str = Field(
        default="SASL_SSL",
        alias="KAFKA_SECURITY_PROTOCOL",
        validation_alias=AliasChoices("KAFKA_SECURITY_PROTOCOL",
                                      "kafka_security_protocol")
    )
    sasl_mechanism: str = Field(
        default="SCRAM-SHA-512",
        alias="KAFKA_SASL_MECHANISM",
        validation_alias=AliasChoices("KAFKA_SASL_MECHANISM",
                                      "kafka_sasl_mechanism")
    )
    sasl_plain_username: str = Field(
        default="",
        alias="KAFKA_SASL_USERNAME",
        validation_alias=AliasChoices("KAFKA_SASL_USERNAME",
                                      "kafka_sasl_username")
    )
    sasl_plain_password: str = Field(
        default="",
        alias="KAFKA_SASL_PASSWORD",
        validation_alias=AliasChoices("KAFKA_SASL_PASSWORD",
                                      "kafka_sasl_password")
    )


class KafkaConsumerConfig(KafkaBaseConfig):
    """Class to manage the Kafka Consumer configuration of the application."""
    input_topic: str = Field(
        default="input-topic",
        alias="KAFKA_INPUT_TOPIC",
        validation_alias=AliasChoices("KAFKA_INPUT_TOPIC",
                                      "kafka_input_topic")
    )
    max_concurrent_messages: int = Field(
        default=10,
        alias="KAFKA_MAX_CONCURRENT_MESSAGES",
        validation_alias=AliasChoices("KAFKA_MAX_CONCURRENT_MESSAGES",
                                      "kafka_max_concurrent_messages")
    )
    max_retry_messages: int = Field(
        default=3,
        alias="KAFKA_MAX_RETRY_MESSAGES",
        validation_alias=AliasChoices("KAFKA_MAX_RETRY_MESSAGES",
                                      "kafka_max_retry_messages")
    )
    group_id: str = Field(
        default="orchestration-agent-consumer-group",
        alias="KAFKA_GROUP_ID",
        validation_alias=AliasChoices("KAFKA_GROUP_ID", "kafka_group_id")
    )
    auto_offset_reset: str = Field(
        default="earliest",
        alias="KAFKA_AUTO_OFFSET_RESET",
        validation_alias=AliasChoices("KAFKA_AUTO_OFFSET_RESET",
                                      "kafka_auto_offset_reset")
    )
    enable_auto_commit: bool = Field(
        default=True,
        alias="KAFKA_ENABLE_AUTO_COMMIT",
        validation_alias=AliasChoices("KAFKA_ENABLE_AUTO_COMMIT",
                                      "kafka_enable_auto_commit")
    )


class KafkaProducerConfig(KafkaBaseConfig):
    """Class to manage the Kafka Producer configuration of the application."""
    output_topic: str = Field(
        default="output-topic",
        alias="KAFKA_OUTPUT_TOPIC",
        validation_alias=AliasChoices("KAFKA_OUTPUT_TOPIC",
                                      "kafka_output_topic")
    )
