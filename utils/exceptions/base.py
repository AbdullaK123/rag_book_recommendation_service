
class BaseServiceException(Exception):
    """Base exception for all services"""
    def __init__(
        self,
        message: str,
        error_code: str = None,
        http_status_code: str = None,
        details: str = None,
        source: str = None,
        suggestion: str = None,
        original_exception: Exception = None
    ):
        self.message = message
        self.error_code = error_code
        self.http_status_code = http_status_code
        self.details = details or {}
        self.source = source
        self.suggestion = suggestion
        self.original_exception = original_exception

        enhanced_message = f"{message}"

        if error_code:
            enhanced_message += f"[Error Code: {error_code}]"
        if http_status_code:
            enhanced_message += f"[HTTP Status Code: {http_status_code}]" 
        if suggestion:
            enhanced_message += f"[Suggestion: {suggestion}]"

        super().__init__(enhanced_message)


    def to_dict(self) -> dict:
        """Convert exception to dictionary for logging/serialization"""
        result = {
            "error_type": self.__class__.__name__,
            "message": self.message
        }

        if self.error_code:
            result["error_code"] = self.error_code
        if self.http_status_code:
            result["http_status_code"] = self.http_status_code
        if self.details:
            result["details"] = self.details
        if self.source:
            result["source"] = self.source
        if self.suggestion:
            result["suggestion"] = self.suggestion
        if self.original_exception:
            result["original_exception"] = str(self.original_exception)
            
        return result

class ConfigurationException(BaseServiceException):
    """Exception raised for configuration errors"""
    def __init__(self, message, **kwargs):
        kwargs.setdefault('error_code', 'CONFIG_ERROR')
        kwargs.setdefault('suggestion', 'Check environment variables and config files')
        super().__init__(message, **kwargs)

class ValidationException(BaseServiceException):
    """Exception raised for data validation errors"""
    def __init__(self, message, **kwargs):
        kwargs.setdefault('error_code', 'VALIDATION_ERROR')
        kwargs.setdefault('http_status_code', 400)
        super().__init__(message, **kwargs)