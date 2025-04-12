from utils.exceptions.base import BaseServiceException


class ProcessingException(BaseServiceException):
    """Base exception for processing errors"""
    def __init__(self, message, **kwargs):
        kwargs.setdefault('error_code', 'PROCESSING_ERROR')
        super().__init__(message, **kwargs)

class RAGException(ProcessingException):
    """Exception raised for RAG pipeline issues"""
    def __init__(self, message, stage=None, **kwargs):
        details = kwargs.get('details', {})
        if stage:
            details['stage'] = stage
        kwargs['details'] = details
        kwargs.setdefault('error_code', 'RAG_ERROR')
        super().__init__(message, **kwargs)

class ContentGenerationException(ProcessingException):
    """Exception raised when content generation fails"""
    def __init__(self, message, content_type=None, **kwargs):
        details = kwargs.get('details', {})
        if content_type:
            details['content_type'] = content_type
        kwargs['details'] = details
        kwargs.setdefault('error_code', 'CONTENT_GENERATION_ERROR')
        super().__init__(message, **kwargs)

class RecommendationException(ProcessingException):
    """Exception raised for recommendation engine failures"""
    def __init__(self, message, user_id=None, **kwargs):
        details = kwargs.get('details', {})
        if user_id:
            details['user_id'] = user_id
        kwargs['details'] = details
        kwargs.setdefault('error_code', 'RECOMMENDATION_ERROR')
        super().__init__(message, **kwargs)