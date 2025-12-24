# infrastructure/entry_points/a2a/agent_card.py
from typing import Dict, Any

class AgentCardBuilder:
    def __init__(self, agent_name, agent_description, agent_base_url ):
        self.agent_name: str = agent_name
        self.agent_description: str = agent_description
        self.agent_base_url: str = agent_base_url

    def build(self) -> Dict[str, Any]:
        return {
            "name": self.agent_name,
            "description": self.agent_description,
            "url": self.agent_base_url,
            "version": "1.0.0",
            "protocol_version": "0.0.1",
            "capabilities": {
                "streaming": True,
                "task_management": True
            },
            "skills": self._get_skills()
        }

    def _get_skills(self):
        # Obtiene las skills del dominio
        from domain.model.skills import get_available_skills
        return [skill.to_dict() for skill in get_available_skills()]