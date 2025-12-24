import asyncio
from dependency_injector.wiring import inject, Provide
from application.settings.container import Container
from infrastructure.driven_adapters.logging.logger_config import LoggerConfig
from infrastructure.entry_points.kafka.adapters import KafkaConsumerAdapter

logger = LoggerConfig().get_logger(__name__)


@inject
async def run_kafka_app(
    consumer: KafkaConsumerAdapter = Provide[Container.kafka_consumer_adapter]
):
    """Run the Kafka application."""
    try:
        await consumer.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error("Application error: %s", e)
        raise
    finally:
        await consumer.stop()


def start_kafka_app():
    """Main entry point for Kafka consumer application."""
    try:
        asyncio.get_running_loop()
        logger.info("Using existing event loop")
        return asyncio.ensure_future(run_kafka_app())
    except RuntimeError:
        logger.info("Creating new event loop")
        return asyncio.run(run_kafka_app())
