"""AgentBill LangChain Exceptions - v7.6.11

Full standalone exception classes for Cost Guard protection.
These are NOT re-exports - they are full implementations.
"""

from typing import Optional, Dict, Any


class AgentBillError(Exception):
    """Base exception for all AgentBill errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        return self.message
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.message!r}, details={self.details!r})"


class BudgetExceededError(AgentBillError):
    """
    Raised when a request would exceed the configured budget limits.
    
    This is thrown by the context manager or wrapper when ai-cost-guard-router
    returns allowed=false due to budget constraints.
    
    Attributes:
        reason: Human-readable explanation of the budget violation
        code: Error code for programmatic handling
        details: Additional context about the violation
    
    Example:
        try:
            async with agentbill_tracing(customer_id="cust_123", daily_budget=0.01):
                response = await openai_client.chat.completions.create(...)
        except BudgetExceededError as e:
            print(f"Budget exceeded: {e.reason}")
            # Graceful degradation: use cached response or notify user
    """
    
    CODE = "BUDGET_EXCEEDED"
    
    def __init__(self, reason: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(f"Budget exceeded: {reason}", details)
        self.reason = reason
        self.code = self.CODE


class RateLimitExceededError(AgentBillError):
    """
    Raised when a request would exceed the configured rate limits.
    
    Attributes:
        reason: Human-readable explanation of the rate limit
        code: Error code for programmatic handling
        details: Additional context including retry_after if available
    
    Example:
        try:
            response = wrapped_client.chat.completions.create(...)
        except RateLimitExceededError as e:
            retry_after = e.details.get('retry_after', 60)
            await asyncio.sleep(retry_after)
    """
    
    CODE = "RATE_LIMIT_EXCEEDED"
    
    def __init__(self, reason: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(f"Rate limit exceeded: {reason}", details)
        self.reason = reason
        self.code = self.CODE


class PolicyViolationError(AgentBillError):
    """
    Raised when a request violates a Cost Guard policy.
    
    This covers violations other than budget/rate limits, such as:
    - Maximum token limits exceeded
    - Blocked model usage
    - Customer-specific restrictions
    
    Attributes:
        reason: Human-readable explanation of the policy violation
        code: Error code for programmatic handling
        details: Additional context about the violated policy
    
    Example:
        try:
            response = wrapped_client.chat.completions.create(
                model="gpt-4-turbo",  # Might be blocked by policy
                messages=[...]
            )
        except PolicyViolationError as e:
            print(f"Policy violation: {e.reason}")
            # Fall back to allowed model
    """
    
    CODE = "POLICY_VIOLATION"
    
    def __init__(self, reason: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(f"Policy violation: {reason}", details)
        self.reason = reason
        self.code = self.CODE


class ValidationError(AgentBillError):
    """
    Raised when input validation fails.
    
    Attributes:
        field: The field that failed validation
        code: Error code for programmatic handling
    
    Example:
        try:
            signal("purchase", revenue=-10)  # Invalid: negative revenue
        except ValidationError as e:
            print(f"Invalid field '{e.field}': {e.message}")
    """
    
    CODE = "VALIDATION_ERROR"
    
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(f"Validation error: {message}")
        self.field = field
        self.code = self.CODE


class TracingError(AgentBillError):
    """
    Raised when tracing operations fail.
    
    This is typically non-fatal and can be caught and logged
    without affecting the main application flow.
    
    Attributes:
        code: Error code for programmatic handling
    
    Example:
        try:
            ctx.add_span("custom_operation", {...})
        except TracingError as e:
            logger.warning(f"Tracing failed: {e.message}")
            # Continue without tracing
    """
    
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
