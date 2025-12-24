# domain/model/skills.py
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class Skill:
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema
        }

def get_available_skills() -> List[Skill]:
    return [
        Skill(
            name="analyze_text",
            description="Crea componentes de UI basados en el análisis del texto proporcionado con el framework Angular.",
            input_schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "task": {"type": "string"}
                },
                "required": ["text"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "result": {"type": "string"}
                }
            }
        ),
        # Agregar más skills aquí
    ]