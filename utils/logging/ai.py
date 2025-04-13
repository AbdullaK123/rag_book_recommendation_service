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
        
        # Add AI error data if available
        if hasattr(record, "ai_error_data"):
            log_record["ai_error_data"] = record.ai_error_data
        
        # Add any other extra fields
        for key, value in record.__dict__.items():
            if key not in ["exc_info", "exc_text", "args", "msg", "message", "ai_error_data"] and not key.startswith("_"):
                try:
                    json.dumps({key: value})  # Test JSON serialization
                    log_record[key] = value
                except (TypeError, OverflowError):
                    log_record[key] = str(value)
        
        return json.dumps(log_record)


class SensitiveDataFilter(logging.Filter):
    """Filter that removes sensitive data from logs"""
    SENSITIVE_FIELDS = {
        'api_key', 'password', 'token', 'secret', 'authorization', 
        'access_token', 'refresh_token', 'prompt', 'openai_api_key'
    }
    
    def __init__(self, name=''):
        super().__init__(name)
    
    def filter(self, record):
        if hasattr(record, 'ai_error_data') and isinstance(record.ai_error_data, dict):
            self._redact_sensitive_data(record.ai_error_data)
            
        return True
    
    def _redact_sensitive_data(self, data, path=''):
        """Recursively redact sensitive data in dictionaries"""
        if isinstance(data, dict):
            for key, value in list(data.items()):
                current_path = f"{path}.{key}" if path else key
                # Check if this is a sensitive field
                if any(sensitive in key.lower() for sensitive in self.SENSITIVE_FIELDS):
                    if isinstance(value, str):
                        # Redact string values
                        data[key] = "[REDACTED]"
                    elif isinstance(value, (dict, list)):
                        # For containers, remove them entirely
                        data[key] = "[REDACTED_OBJECT]"
                # Redact prompts and completions to avoid logging PII
                elif key.lower() in {'prompt', 'completion', 'input', 'output'} and isinstance(value, str) and len(value) > 100:
                    # Truncate long text to avoid logging PII
                    data[key] = value[:50] + "... [TRUNCATED]"
                # Recurse into nested structures
                elif isinstance(value, (dict, list)):
                    self._redact_sensitive_data(value, current_path)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                current_path = f"{path}[{i}]"
                if isinstance(item, (dict, list)):
                    self._redact_sensitive_data(item, current_path)


def setup_ai_logging(
    log_level: str = "INFO",
    log_to_file: bool = True,
    log_dir: str = "logs",
    json_format: bool = True,
    redact_sensitive_data: bool = True
):
    """
    Configure AI processing logging
    
    Args:
        log_level: Minimum log level to capture
        log_to_file: Whether to log to file
        log_dir: Directory for log files
        json_format: Whether to use JSON formatting
        redact_sensitive_data: Whether to redact sensitive data from logs
    """
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create AI logger
    ai_logger = logging.getLogger('utils.decorators.ai_exception_handler')
    ai_logger.setLevel(numeric_level)
    
    # Clear existing handlers
    for handler in ai_logger.handlers[:]:
        ai_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    
    # Create formatter
    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    console_handler.setFormatter(formatter)
    
    # Add sensitive data filter if requested
    if redact_sensitive_data:
        sensitive_filter = SensitiveDataFilter()
        console_handler.addFilter(sensitive_filter)
    
    ai_logger.addHandler(console_handler)
    
    # Add file handler if requested
    if log_to_file:
        # Create log directory if it doesn't exist
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        # Create AI log file
        log_file = log_path / "ai_errors.log"
        
        # Create file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        
        if redact_sensitive_data:
            file_handler.addFilter(sensitive_filter)
            
        ai_logger.addHandler(file_handler)
    
    # Log setup completion
    ai_logger.info("AI processing logging configured")

    return ai_logger


def get_ai_logger():
    """Get the AI logger"""
    return logging.getLogger('utils.decorators.ai_exception_handler')


# Automatic setup during import
def init_ai_logging():
    """Initialize AI logging based on environment"""
    env = os.getenv("APP_ENV", "development")
    log_level = "DEBUG" if env == "development" else "INFO"
    json_format = env != "development"
    
    return setup_ai_logging(
        log_level=log_level,
        log_to_file=True,
        json_format=json_format,
        redact_sensitive_data=True
    )