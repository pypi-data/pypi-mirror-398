"""Custom exceptions for Keyword Generation V2"""


class KeywordGenerationError(Exception):
    """Base exception for keyword generation errors"""
    pass


class AIGenerationError(KeywordGenerationError):
    """Error during AI keyword generation"""
    
    def __init__(self, message: str, original_error: Exception = None):
        super().__init__(message)
        self.original_error = original_error


class GapAnalysisError(KeywordGenerationError):
    """Error during gap analysis"""
    
    def __init__(self, message: str, original_error: Exception = None):
        super().__init__(message)
        self.original_error = original_error


class ScoringError(KeywordGenerationError):
    """Error during keyword scoring"""
    
    def __init__(self, message: str, original_error: Exception = None):
        super().__init__(message)
        self.original_error = original_error


class APIError(KeywordGenerationError):
    """Error with external API calls"""
    
    def __init__(self, message: str, api_name: str = None, status_code: int = None, original_error: Exception = None):
        super().__init__(message)
        self.api_name = api_name
        self.status_code = status_code
        self.original_error = original_error


class ConfigurationError(KeywordGenerationError):
    """Error with configuration"""
    pass


class ValidationError(KeywordGenerationError):
    """Error validating input data"""
    pass

