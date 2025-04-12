from utils.exceptions.base import BaseServiceException


class ExternalServiceException(BaseServiceException):
    """Base exception for external service errors"""
    def __init__(self, service_name, message, **kwargs):
        full_message = f"Error with external service {service_name}: {message}"
        kwargs.setdefault('error_code', 'EXTERNAL_SERVICE_ERROR')
        kwargs.setdefault('details', {'service': service_name})
        super().__init__(full_message, **kwargs)

class WebSearchException(ExternalServiceException):
    """Exception raised when web search fails"""
    def __init__(self, message, search_query=None, **kwargs):
        details = kwargs.get('details', {})
        if search_query:
            details['search_query'] = search_query
        kwargs['details'] = details
        kwargs.setdefault('error_code', 'WEB_SEARCH_ERROR')
        super().__init__("Web Search", message, **kwargs)

class LLMServiceException(ExternalServiceException):
    """Exception raised for issues with LLM API"""
    def __init__(self, message, model=None, **kwargs):
        details = kwargs.get('details', {})
        if model:
            details['model'] = model
        kwargs['details'] = details
        kwargs.setdefault('error_code', 'LLM_SERVICE_ERROR')
        kwargs.setdefault('suggestion', 'Check API key and model availability')
        super().__init__("LLM Service", message, **kwargs)

class EmailDeliveryException(ExternalServiceException):
    """Exception raised when email sending fails"""
    def __init__(self, message, recipient=None, **kwargs):
        details = kwargs.get('details', {})
        if recipient:
            details['recipient'] = recipient
        kwargs['details'] = details
        kwargs.setdefault('error_code', 'EMAIL_DELIVERY_ERROR')
        super().__init__("Email Service", message, **kwargs)