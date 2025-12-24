# infrastructure/driven_adapters/logging/logger_config.py
import logging
import json
from typing import Optional
from datetime import datetime, UTC


class JSONFormatter(logging.Formatter):
    """Formateador que genera logs en formato JSON para consola"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


class LoggerConfig:
    """Configuración centralizada de logging (solo consola)"""

    _instance: Optional['LoggerConfig'] = None
    _loggers: dict = {}
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if LoggerConfig._initialized:
            return
        LoggerConfig._initialized = True

    def get_logger(self, name: str, level: int = logging.INFO) -> logging.Logger:
        """Obtiene o crea un logger con output a consola únicamente"""

        if name in self._loggers:
            return self._loggers[name]

        logger = logging.getLogger(name)
        logger.setLevel(level)

        # Evitar duplicados
        if logger.handlers:
            return logger

        # Handler para consola con formato JSON
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(JSONFormatter())
        logger.addHandler(console_handler)

        self._loggers[name] = logger
        return logger
