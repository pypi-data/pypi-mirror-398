"""
AgentBill Python SDK
OpenTelemetry-based SDK for tracking AI agent usage and billing

Features:
- Context manager (@agentbill_tracing) for Cost Guard protected AI calls
- signal() function for business event tracking and revenue attribution
- Auto-instrumentation for OpenAI, Anthropic, Cohere, Google AI
- Distributed tracing for cross-service trace propagation
"""

from .client import AgentBill
from .tracer import AgentBillTracer
from .types import AgentBillConfig, TraceContext
from .validation import (
    validate_api_key,
    validate_base_url,
    validate_customer_id,
    validate_event_name,
    validate_metadata,
    validate_revenue,
    ValidationError as InputValidationError
)

# New v6.6.0 features
from .exceptions import (
    AgentBillError,
    BudgetExceededError,
    RateLimitExceededError,
    PolicyViolationError,
    ValidationError,
    TracingError,
)
from .tracing import (
    agentbill_tracing,
    agentbill_traced,
    TracingContext,
)
from .signals import (
    signal,
    track_conversion,
    set_signal_config,
    get_signal_config,
)
from .bulk import record_bulk
from .autoinstrument import (
    agentbill_autoinstrument,
    initialize_tracing,
)
from .distributed import (
    generate_tracing_token,
    set_tracing_token,
    get_tracing_token,
    get_trace_context,
    set_trace_context,
    clear_trace_context,
    propagate_trace_headers,
    extract_trace_from_headers,
)
from .wrappers import (
    AgentBillOpenAI,
    AgentBillAnthropic,
    AgentBillCohere,
    AgentBillGoogleAI,
    AgentBillBedrock,
)

__version__ = "7.15.0"
__all__ = [
    # Core
    "AgentBill", 
    "AgentBillTracer", 
    "AgentBillConfig", 
    "TraceContext",
    
    # Exceptions
    "AgentBillError",
    "BudgetExceededError",
    "RateLimitExceededError",
    "PolicyViolationError",
    "ValidationError",
    "TracingError",
    
    # Input Validation (legacy)
    "InputValidationError",
    "validate_api_key",
    "validate_base_url",
    "validate_customer_id",
    "validate_event_name",
    "validate_metadata",
    "validate_revenue",
    
    # Context Manager / Decorator
    "agentbill_tracing",
    "agentbill_traced",
    "TracingContext",
    
    # Signals
    "signal",
    "track_conversion",
    "set_signal_config",
    "get_signal_config",
    "record_bulk",
    
    # Auto-instrumentation
    "agentbill_autoinstrument",
    "initialize_tracing",
    
    # Distributed Tracing
    "generate_tracing_token",
    "set_tracing_token",
    "get_tracing_token",
    "get_trace_context",
    "set_trace_context",
    "clear_trace_context",
    "propagate_trace_headers",
    "extract_trace_from_headers",
    
    # Wrapper Classes (Hybrid Approach)
    "AgentBillOpenAI",
    "AgentBillAnthropic",
    "AgentBillCohere",
    "AgentBillGoogleAI",
    "AgentBillBedrock",
]
