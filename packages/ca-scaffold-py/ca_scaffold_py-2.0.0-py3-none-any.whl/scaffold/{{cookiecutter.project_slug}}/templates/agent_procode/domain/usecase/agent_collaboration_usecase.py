from domain.model.gateways.agent.collaborate_adapter import CollaborateAdapter
from domain.usecase.agent_interaction_usecase import AgentInteractionUseCase
from typing import AsyncIterator

class AgentCollaborationUseCase:
    def __init__(self, collaborate_adapter: CollaborateAdapter, agent_usecase: AgentInteractionUseCase):
        self.collaborate_adapter = collaborate_adapter
        self.agent_usecase = agent_usecase

    async def delegate_task_to_external_agent(self, agent_url: str, task: str) -> str:
        """Tu agente delega una tarea a otro agente"""

        # 1. Descubrir capacidades del agente externo
        agent_card = await self.collaborate_adapter.discover_agent(agent_url)
        print(f"Discovered agent: {agent_card['name']} with skills: {agent_card.get('skills', [])}")

        response = await self.collaborate_adapter.send_to_agent(agent_url, task)

        final_result = await self.agent_usecase.interact_with_agent(f"Formatea esta respuesta para el usuario: {response.get('content')}")

        return final_result

    async def collaborate_with_agent_streaming(self, agent_url: str, task: str) -> AsyncIterator:
        """Tu agente colabora con otro agente usando streaming"""

        # 1. Descubrir capacidades del agente externo
        accumulate_response =  ""

        async for chunk in self.collaborate_adapter.stream_from_agent(agent_url, task):
            accumulate_response += str(chunk.get('content', ''))
            yield chunk

        final_result = await self.agent_usecase.interact_with_agent(f"Analiza y formatea esta respuesta: {accumulate_response}")

        yield final_result