from domain.model.gateways.agent.agent_adapter import AgentAdapter


class AgentInteractionUseCase:
    """" Use case for interacting with an agent. """

    def __init__(self, agent: AgentAdapter):
        self.agent = agent

    async def interact_with_agent(self, message):
        prompt = self.agent.create_prompt(message)
        response = await self.agent.interact(prompt)
        return response