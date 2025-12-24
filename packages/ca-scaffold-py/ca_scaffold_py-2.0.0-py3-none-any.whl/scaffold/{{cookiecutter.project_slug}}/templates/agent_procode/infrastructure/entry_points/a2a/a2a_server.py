from fastapi import FastAPI, Request, HTTPException
from infrastructure.entry_points.a2a.agent_card import AgentCardBuilder
from domain.usecase.agent_interaction_usecase import AgentInteractionUseCase


class A2AServer:
    def __init__(self, agent_name: str, agent_description: str, agent_base_url: str, agent_use_case: AgentInteractionUseCase):
        self.agent_card_builder = AgentCardBuilder(agent_name, agent_description, agent_base_url)
        self.agent_use_case: AgentInteractionUseCase = agent_use_case

    def setup_routes(self, app: FastAPI):
        # 1. Exponer agent card (descubrimiento)
        @app.get("/.well-known/agent.json")
        async def get_agent_card():
            return self.agent_card_builder.build()

        # 2. Recibir mensajes síncronos de otros agentes
        @app.post("/a2a/tasks")
        async def receive_message(request: Request):
            try:
                body = await request.json()
                message_content = self._extract_message_content(body)

                # Procesar con tu agente interno
                response = await self.agent_use_case.interact_with_agent(message_content)

                return self._format_a2a_response(response)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        # 3. Recibir mensajes streaming de otros agentes
        @app.post("/a2a/tasks/stream")
        async def receive_streaming_message(request: Request):
            body = await request.json()
            message_content = self._extract_message_content(body)

            async def event_generator():
                response = await self.agent_use_case.interact_with_agent(message_content)

                # Enviar evento de inicio
                yield self._format_stream_event("start", {"task_id": "123"})

                # Enviar contenido
                yield self._format_stream_event("content", {"text": response})

                # Enviar evento de fin
                yield self._format_stream_event("end", {})

            return event_generator()

    def _extract_message_content(self, body: dict) -> str:
        # Extraer según formato A2A
        message = body.get("message", {})
        parts = message.get("parts", [])
        if parts and parts[0].get("kind") == "text":
            return parts[0].get("text", "")
        return ""

    def _format_a2a_response(self, response: dict) -> dict:
        # Formatear respuesta según protocolo A2A
        content = response.get("messages", [])[-1].content if "messages" in response else str(response)

        return {
            "message": {
                "role": "assistant",
                "parts": [{"kind": "text", "text": content}]
            }
        }

    def _format_stream_event(self, event_type: str, data: dict) -> dict:
        return {
            "event": event_type,
            "data": data
        }
