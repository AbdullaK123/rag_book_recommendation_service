# Initialize all loggers
from utils.logging.api import init_api_logging
from utils.logging.db import init_db_logging
from utils.logging.ai import init_ai_logging

# Initialize loggers
api_logger = init_api_logging()
db_logger = init_db_logging()
ai_logger = init_ai_logging()

__all__ = ["api_logger", "db_logger", "ai_logger"]