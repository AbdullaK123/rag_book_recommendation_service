import logging
import json
import sys
import os
from datetime import datetime
from pathlib import Path

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add traceback if exception occurred
        if record.exc_info:
            log_record["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }
        
        # Add database error data if available
        if hasattr(record, "db_error_data"):
            log_record["db_error_data"] = record.db_error_data
        
        # Add any other extra fields
        for key, value in record.__dict__.items():
            if key not in ["exc_info", "exc_text", "args", "msg", "message", "db_error_data"] and not key.startswith("_"):
                try:
                    json.dumps({key: value})  # Test JSON serialization
                    log_record[key] = value
                except (TypeError, OverflowError):
                    log_record[key] = str(value)
        
        return json.dumps(log_record)


def setup_db_logging(
    log_level: str = "INFO",
    log_to_file: bool = True,
    log_dir: str = "logs",
    json_format: bool = True
):
    """
    Configure database logging
    
    Args:
        log_level: Minimum log level to capture
        log_to_file: Whether to log to file
        log_dir: Directory for log files
        json_format: Whether to use JSON formatting
    """
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create database logger
    db_logger = logging.getLogger('utils.decorators.db_exception_handler')
    db_logger.setLevel(numeric_level)
    
    # Clear existing handlers
    for handler in db_logger.handlers[:]:
        db_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    
    # Create formatter
    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    console_handler.setFormatter(formatter)
    db_logger.addHandler(console_handler)
    
    # Add file handler if requested
    if log_to_file:
        # Create log directory if it doesn't exist
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        # Create database log file
        log_file = log_path / "database_errors.log"
        
        # Create file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        db_logger.addHandler(file_handler)
    
    # Log setup completion
    db_logger.info("Database logging configured")

    return db_logger


def get_db_logger():
    """Get the database logger"""
    return logging.getLogger('utils.decorators.db_exception_handler')


# Automatic setup during import
def init_db_logging():
    """Initialize database logging based on environment"""
    env = os.getenv("APP_ENV", "development")
    log_level = "DEBUG" if env == "development" else "INFO"
    json_format = env != "development"
    
    return setup_db_logging(
        log_level=log_level,
        log_to_file=True,
        json_format=json_format
    )
