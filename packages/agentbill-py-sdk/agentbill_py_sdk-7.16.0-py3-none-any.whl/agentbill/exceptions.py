"""AgentBill SDK Exceptions

Custom exceptions for Cost Guard budget enforcement and validation errors.
"""


class AgentBillError(Exception):
    """Base exception for AgentBill SDK"""
    pass


class BudgetExceededError(AgentBillError):
    """
    Raised when Cost Guard blocks a request due to budget limits.
    
    This error is thrown BEFORE any AI call is made when:
    - Daily budget would be exceeded
    - Monthly budget would be exceeded
    - Customer-specific budget limits are reached
    
    Example:
        >>> try:
        ...     with agentbill_tracing(customer_id="cust-123", daily_budget=0.01):
        ...         response = openai.chat.completions.create(...)
        ... except BudgetExceededError as e:
        ...     print(f"Budget exceeded: {e.reason}")
        ...     # Handle gracefully - show user a message, queue for later, etc.
    """
    
    def __init__(self, reason: str, details: dict = None):
        self.reason = reason
        self.details = details or {}
        self.code = "BUDGET_EXCEEDED"
        super().__init__(f"Budget exceeded: {reason}")


class RateLimitExceededError(AgentBillError):
    """
    Raised when Cost Guard blocks a request due to rate limits.
    
    This error is thrown when:
    - Requests per minute limit exceeded
    - Requests per hour limit exceeded
    - Token rate limits exceeded
    """
    
    def __init__(self, reason: str, details: dict = None):
        self.reason = reason
        self.details = details or {}
        self.code = "RATE_LIMIT_EXCEEDED"
        super().__init__(f"Rate limit exceeded: {reason}")


class PolicyViolationError(AgentBillError):
    """
    Raised when Cost Guard blocks a request due to policy violations.
    
    This error is thrown when:
    - Model not allowed by policy
    - Token limits exceeded
    - Other policy constraints violated
    """
    
    def __init__(self, reason: str, details: dict = None):
        self.reason = reason
        self.details = details or {}
        self.code = "POLICY_VIOLATION"
        super().__init__(f"Policy violation: {reason}")


class ValidationError(AgentBillError):
    """
    Raised when input validation fails.
    
    This error is thrown when:
    - Invalid API key format
    - Missing required parameters
    - Invalid configuration
    """
    
    def __init__(self, reason: str, field: str = None):
        self.reason = reason
        self.field = field
        self.code = "VALIDATION_ERROR"
        super().__init__(f"Validation error: {reason}")


class TracingError(AgentBillError):
    """
    Raised when tracing operations fail.
    
    This error is thrown when:
    - Failed to start/end span
    - Failed to export spans
    - Invalid trace context
    """
    
    def __init__(self, reason: str, details: dict = None):
        self.reason = reason
        self.details = details or {}
        self.code = "TRACING_ERROR"
        super().__init__(f"Tracing error: {reason}")
