from typing import Optional, Dict, Any, Coroutine

from langchain.agents import create_agent
from langchain_core.tools import BaseTool
from langgraph.typing import InputT

from domain.model.gateways.agent.agent_adapter import AgentAdapter
from infrastructure.driven_adapters.llm.llm_gateway import LlmGateway
from infrastructure.driven_adapters.logging.logger_config import LoggerConfig


class LangGraphAgentAdapter(AgentAdapter):
    def __init__(self, llm_gateway: LlmGateway, tools: list[BaseTool], agent_instructions: str):
        self.logger = LoggerConfig().get_logger(self.__class__.__name__)
        try:
            self.model = llm_gateway.get_llm()
            self.agent = create_agent(
                model=self.model,
                system_prompt=agent_instructions,
                tools=tools,
            )
        except Exception as e:
            self.logger.error(f"Error initializing LangGraph agent: {e}")

    def create_prompt(self, message) -> dict:
        return {"messages": [{"role": "user", "content": message}]}

    async def interact(self, prompt: InputT) -> Optional[Dict[str, Any]]:
        try:
            response = await self.agent.ainvoke(prompt)
            return response
        except Exception as e:
            self.logger.error(f"Error during agent interaction: {e}")
            return None