from dotenv import load_dotenv
load_dotenv('application/settings/.env')

from dependency_injector import containers, providers

from application.settings.settings import Config
from domain.usecase.agent_collaboration_usecase import AgentCollaborationUseCase
from domain.usecase.agent_interaction_usecase import AgentInteractionUseCase
from infrastructure.driven_adapters.a2a.a2a_client import A2AClient
from infrastructure.driven_adapters.kafka_producer_adapter.adapter.kafka_producer_adapter import KafkaProducerAdapter
from infrastructure.driven_adapters.langgraph_agent.langgraph_agent_adapter import LangGraphAgentAdapter
from infrastructure.driven_adapters.llm.llm_gateway import LlmGateway
from infrastructure.driven_adapters.tools.mcp_client import MCPClient
from infrastructure.entry_points.a2a.a2a_server import A2AServer
from infrastructure.entry_points.kafka.adapters import KafkaConsumerAdapter
from infrastructure.entry_points.kafka.handlers import AgentMessageHandler


async def get_tools_from_mcp(mcp_client: MCPClient):
    """Factory function to get tools asynchronously"""
    return await mcp_client.get_tools()


def create_kafka_producer_if_enabled(config: Config):
    """Create Kafka producer only if mount_kafka is True"""
    if config.mount_kafka:
        # Asegurarse de que kafka_producer no es None antes de dumpear
        if config.kafka_producer:
            return KafkaProducerAdapter(kafka_config=config.kafka_producer.model_dump())
    return None


def create_kafka_consumer_if_enabled(config: Config, message_handler: AgentMessageHandler):
    """Create Kafka consumer only if mount_kafka is True"""
    if not config.mount_kafka or not config.kafka_consumer:
        return None

    return KafkaConsumerAdapter(
        kafka_config=config.kafka_consumer.model_dump(),
        message_handler=message_handler
    )

def agent_message_handler_if_enabled(config: Config, agent_use_case: AgentInteractionUseCase, producer: KafkaProducerAdapter):
    """Create AgentMessageHandler only if mount_kafka is True"""
    if not config.mount_kafka:
        return None

    return AgentMessageHandler(
        agent_interaction_use_case=agent_use_case,
        kafka_producer=producer,
    )


class Container(containers.DeclarativeContainer):
    """Dependency injection container for MCP server management."""

    config = providers.Singleton(Config)

    llm_gateway = providers.Singleton(
        LlmGateway, 
        api_key=config.provided.api_key, 
        api_base=config.provided.api_base,
        model_name=config.provided.model_name, 
        temperature=config.provided.temperature
    )

    mcp_client = providers.Singleton(
        MCPClient,
        mcp_connections=config.provided.mcp_connections
    )

    tools = providers.Resource(get_tools_from_mcp, mcp_client=mcp_client)

    langgraph_agent_adapter = providers.Singleton(
        LangGraphAgentAdapter, 
        llm_gateway=llm_gateway, 
        tools=tools,
        agent_instructions=config.provided.agent_instructions
    )

    agent_interaction_use_case = providers.Singleton(
        AgentInteractionUseCase, 
        agent=langgraph_agent_adapter
    )

    a2a_client = providers.Singleton(A2AClient)

    agent_collaboration_use_case = providers.Singleton(
        AgentCollaborationUseCase, 
        collaborate_adapter=a2a_client,
        agent_usecase=agent_interaction_use_case
    )

    a2a_server = providers.Singleton(
        A2AServer, 
        agent_name=config.provided.agent_name,
        agent_description=config.provided.agent_description,
        agent_base_url=config.provided.agent_base_url,
        agent_use_case=agent_interaction_use_case
    )

    kafka_producer = providers.Factory(
        create_kafka_producer_if_enabled,
        config=config
    )

    agent_message_handler = providers.Factory(
        agent_message_handler_if_enabled,
        config=config,
        agent_interaction_use_case=agent_interaction_use_case,
        producer=kafka_producer,
    )

    kafka_consumer = providers.Factory(
        create_kafka_consumer_if_enabled,
        config=config,
        message_handler=agent_message_handler
    )