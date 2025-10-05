"""Core exceptions for VocabuRex Chatbot Service"""


class ChatbotServiceException(Exception):
    """Base exception for chatbot service"""
    pass


class GeminiAPIException(ChatbotServiceException):
    """Exception for Gemini API related errors"""
    pass


class ConversationNotFoundException(ChatbotServiceException):
    """Exception when conversation is not found"""
    pass


class InvalidMessageException(ChatbotServiceException):
    """Exception for invalid message format"""
    pass


class DeepLinkException(ChatbotServiceException):
    """Exception for deep link processing errors"""
    pass