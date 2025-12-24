import os
from typing import Optional, List, Dict, Any
from pydantic import Field, field_validator, model_validator

from application.settings.base_settings import GeneralBaseSettings
from application.settings.kafka_settings import KafkaConsumerConfig, KafkaProducerConfig


class Config(GeneralBaseSettings):
    """Config settings for the agent."""
    api_key: str = Field(alias="API_KEY")
    api_base: str = Field(alias="API_BASE")
    model_name: str = Field(alias="MODEL_NAME")
    temperature: float = Field(default=0.7, alias="TEMPERATURE")
    agent_instructions: str = Field(alias="AGENT_INSTRUCTIONS")
    agent_name: str = Field(alias="AGENT_NAME")
    agent_description: str = Field(alias="AGENT_DESCRIPTION")
    agent_base_url: str = Field(alias="AGENT_BASE_URL")

    # Kafka mount flag
    mount_kafka: bool = Field(
        default=False,
        alias="MOUNT_KAFKA",
        validation_alias="MOUNT_KAFKA"
    )

    # Kafka configs (optional)
    kafka_consumer: Optional[KafkaConsumerConfig] = Field(
        default=None,
    )
    kafka_producer: Optional[KafkaProducerConfig] = Field(
        default=None,
    )

    # MCP Connections (leído dinámicamente)
    mcp_connections: List[Dict[str, str]] = Field(default_factory=list)

    @field_validator('kafka_consumer', 'kafka_producer', mode='before')
    @classmethod
    def validate_kafka_configs(cls, v, info):
        """Initialize Kafka configs only if mount_kafka is True."""
        mount_kafka = info.data.get('mount_kafka', False)
        if mount_kafka and v is None:
            return {} if v is None else v
        return None if not mount_kafka else v

    @model_validator(mode='before')
    @classmethod
    def load_mcp_connections(cls, data: Any) -> Any:
        """
        Lee dinámicamente las variables de entorno MCP_CONNECTION_X_NAME
        y MCP_CONNECTION_X_ENDPOINT y las carga en 'mcp_connections'.
        """
        if not isinstance(data, dict):
            return data

        connections = []
        i = 1
        while True:
            name_var = f"MCP_CONNECTION_{i}_NAME"
            endpoint_var = f"MCP_CONNECTION_{i}_ENDPOINT"
            
            name = data.get(name_var, os.getenv(name_var))
            endpoint = data.get(endpoint_var, os.getenv(endpoint_var))

            if name and endpoint:
                connections.append({"name": name, "endpoint": endpoint})
                i += 1
            else:
                break
        
        if connections:
            data['mcp_connections'] = connections
        
        i = 1
        while f"MCP_CONNECTION_{i}_NAME" in data:
            del data[f"MCP_CONNECTION_{i}_NAME"]
            del data[f"MCP_CONNECTION_{i}_ENDPOINT"]
            i += 1

        return data