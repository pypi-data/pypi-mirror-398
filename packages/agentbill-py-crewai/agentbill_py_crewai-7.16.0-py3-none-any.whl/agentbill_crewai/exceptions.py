"""AgentBill CrewAI Exceptions - v7.6.11

Full standalone exception classes for Cost Guard protection.
"""

from typing import Optional, Dict, Any


class AgentBillError(Exception):
    """Base exception for all AgentBill errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class BudgetExceededError(AgentBillError):
    """Raised when a request would exceed the configured budget limits."""
    CODE = "BUDGET_EXCEEDED"
    
    def __init__(self, reason: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(f"Budget exceeded: {reason}", details)
        self.reason = reason
        self.code = self.CODE


class RateLimitExceededError(AgentBillError):
    """Raised when a request would exceed rate limits."""
    CODE = "RATE_LIMIT_EXCEEDED"
    
    def __init__(self, reason: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(f"Rate limit exceeded: {reason}", details)
        self.reason = reason
        self.code = self.CODE


class PolicyViolationError(AgentBillError):
    """Raised when a request violates a Cost Guard policy."""
    CODE = "POLICY_VIOLATION"
    
    def __init__(self, reason: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(f"Policy violation: {reason}", details)
        self.reason = reason
        self.code = self.CODE


class ValidationError(AgentBillError):
    """Raised when input validation fails."""
    CODE = "VALIDATION_ERROR"
    
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(f"Validation error: {message}")
        self.field = field
        self.code = self.CODE


class TracingError(AgentBillError):
    """Raised when tracing operations fail."""
    CODE = "TRACING_ERROR"
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(f"Tracing error: {message}", details)
        self.code = self.CODE


__all__ = [
    "AgentBillError",
    "BudgetExceededError",
    "RateLimitExceededError",
    "PolicyViolationError",
    "ValidationError",
    "TracingError",
]
