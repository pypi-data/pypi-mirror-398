# main.py
import asyncio

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from dependency_injector.wiring import inject, Provide

from application.settings.container import Container
from domain.usecase.agent_collaboration_usecase import AgentCollaborationUseCase
from domain.usecase.agent_interaction_usecase import AgentInteractionUseCase
from infrastructure.driven_adapters.logging.logger_config import LoggerConfig
from infrastructure.entry_points.api.dto.chat_request import ChatRequest

logger = LoggerConfig().get_logger(__name__)

@asynccontextmanager
async def lifespan(application: FastAPI):
    """Inicializa recursos asíncronos del contenedor"""
    container = Container()

    # Inicializar recursos asíncronos
    await container.init_resources()

    # Wire del contenedor
    container.wire(modules=[__name__])

    # Configurar servidor A2A
    a2a_server =  await container.a2a_server()
    a2a_server.setup_routes(application)

    # Cargar Kafka solo si mount_kafka está habilitado
    kafka_task = None
    if container.config().mount_kafka:
        logger.info("Kafka habilitado. Iniciando consumer...")
        kafka_consumer = await container.kafka_consumer()
        kafka_task = asyncio.create_task(kafka_consumer.start())
    else:
        logger.info("Kafka deshabilitado en configuración")

    yield

    # Shutdown: cerrar recursos
    if kafka_task and not kafka_task.done():
        logger.info("Deteniendo Kafka consumer...")
        kafka_consumer = await container.kafka_consumer()
        await kafka_consumer.stop()
        kafka_task.cancel()
        try:
            await kafka_task
        except asyncio.CancelledError:
            pass
    await container.shutdown_resources()


app = FastAPI(title="Agent Service", lifespan=lifespan)


@app.post("/chat")
@inject
async def chat(
        request: ChatRequest,
        use_case: AgentInteractionUseCase = Depends(Provide[Container.agent_interaction_use_case])
):
    """Endpoint tradicional para clientes que no usan protocolo A2A"""
    response = await use_case.interact_with_agent(request.message)
    if response is None:
        raise HTTPException(status_code=500, detail="No response from agent")
    return response


@app.post("/collaborate")
@inject
async def collaborate_with_external_agent(
        agent_url: str,
        task: str,
        use_case: AgentCollaborationUseCase = Depends(Provide[Container.agent_collaboration_use_case])
):
    """Endpoint para que administradores inicien colaboración con otros agentes"""
    result = await use_case.delegate_task_to_external_agent(agent_url, task)
    return {"result": result}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
