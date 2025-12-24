from src.domain.model.paper.gateway.prompt_repository import PromptRepository
import logging
from typing import Dict, Any

import os

logger = logging.getLogger(__name__)

class PromptPaper(PromptRepository):

    async def generate_search_prompt(self, topic: str, num_papers: int = 5) -> str:
        """Generate a prompt for Claude to find and discuss academic papers on a specific topic."""
        return f"""Search for {num_papers} academic papers about '{topic}' using the search_papers tool. Follow these instructions:
        1. First, search for papers using search_papers(topic='{topic}', max_results={num_papers})
        2. For each paper found, extract and organize the following information:
        - Paper title
        - Authors
        - Publication date
        - Brief summary of the key findings
        - Main contributions or innovations
        - Methodologies used
        - Relevance to the topic '{topic}'
        
        3. Provide a comprehensive summary that includes:
        - Overview of the current state of research in '{topic}'
        - Common themes and trends across the papers
        - Key research gaps or areas for future investigation
        - Most impactful or influential papers in this area
        
        4. Organize your findings in a clear, structured format with headings and bullet points for easy readability.
        
        Please present both detailed information about each paper and a high-level synthesis of the research landscape in {topic}."""

# --- MÉTODO MODIFICADO ---
    async def read_prompt(self, prompt_name: str) -> str: # <--- Cambia Dict[str, Any] a str
        """Lee un prompt estático desde un archivo .txt y devuelve solo el contenido."""
        base_path = os.path.dirname(__file__)
        content_path = os.path.join(base_path, "content")
        file_path = os.path.join(content_path, f"{prompt_name}.txt")

        logger.info(f"Intentando leer prompt estático desde: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()

            # Extrae el contenido real después del separador ---
            parts = file_content.rsplit('---\n', 1)
            if len(parts) == 2:
                prompt_text = parts[1].strip()
            else:
                lines = file_content.splitlines()
                prompt_lines = [line for line in lines if not line.strip().startswith('#')]
                prompt_text = "\n".join(prompt_lines).strip()
                if not prompt_text:
                    prompt_text = file_content.strip()

            logger.info(f"Prompt '{prompt_name}' leído exitosamente.")
            # Devuelve SOLO el texto
            return prompt_text # <--- Cambia return {"role": "...", ...} a esto

        except FileNotFoundError:
            logger.error(f"Archivo de prompt no encontrado: {file_path}")
            raise FileNotFoundError(f"El archivo para el prompt '{prompt_name}' no fue encontrado.") from None
        except Exception as e:
            logger.error(f"Error leyendo el archivo de prompt {file_path}: {e}", exc_info=True)
            raise RuntimeError(f"No se pudo leer el prompt '{prompt_name}'.") from e
    # --- FIN MÉTODO MODIFICADO ---