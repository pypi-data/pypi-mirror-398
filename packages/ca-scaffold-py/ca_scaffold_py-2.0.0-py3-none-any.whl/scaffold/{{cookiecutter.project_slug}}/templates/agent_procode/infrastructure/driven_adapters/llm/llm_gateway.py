from langchain.chat_models import init_chat_model

from infrastructure.driven_adapters.logging.logger_config import LoggerConfig


class LlmGateway:

    def __init__(self, model_name: str, temperature, api_base: str, api_key: str):
        self.logger = LoggerConfig().get_logger(self.__class__.__name__)
        try:
            self.model = init_chat_model(
                model=model_name,
                temperature=temperature,
                base_url=api_base,
                api_key=api_key,
            )
        except Exception as e:
            self.logger.error(f"Error initializing LLM model: {e}")
            raise e

    def get_llm(self):
        return self.model