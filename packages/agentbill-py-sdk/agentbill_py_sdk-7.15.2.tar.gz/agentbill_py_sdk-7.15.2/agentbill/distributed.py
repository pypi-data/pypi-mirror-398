"""AgentBill Distributed Tracing

Functions for cross-service trace propagation and correlation.
Allows linking AI calls across multiple services/processes.
"""
import os
import uuid
import secrets
import contextvars
from typing import Optional, Dict, Any

# Context variable to store the current tracing token
_tracing_token: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    'agentbill_tracing_token', default=None
)

# Context variable to store trace context (trace_id, span_id, parent_span_id)
_trace_context: contextvars.ContextVar[Optional[Dict[str, str]]] = contextvars.ContextVar(
    'agentbill_trace_context', default=None
)


def generate_tracing_token() -> str:
    """
    Generate a new tracing token for distributed trace propagation.
    
    This token can be passed to downstream services to link traces
    across service boundaries. The token encodes the current trace_id
    and span_id for correlation.
    
    Returns:
        str: A tracing token that can be passed to downstream services
        
    Example:
        >>> # In the calling service
        >>> token = generate_tracing_token()
        >>> response = requests.post(
        ...     "https://downstream-service/api",
        ...     headers={"X-AgentBill-Trace": token}
        ... )
        
        >>> # In the downstream service
        >>> token = request.headers.get("X-AgentBill-Trace")
        >>> set_tracing_token(token)
        >>> # Now all AI calls will be linked to the parent trace
    """
    ctx = _trace_context.get()
    
    if ctx:
        # Encode existing context into token
        trace_id = ctx.get("trace_id", "")
        span_id = ctx.get("span_id", "")
        # Format: agentbill-v1-{trace_id}-{span_id}-{random}
        random_suffix = secrets.token_hex(4)
        token = f"agentbill-v1-{trace_id}-{span_id}-{random_suffix}"
    else:
        # Generate new trace context
        trace_id = uuid.uuid4().hex
        span_id = uuid.uuid4().hex[:16]
        random_suffix = secrets.token_hex(4)
        token = f"agentbill-v1-{trace_id}-{span_id}-{random_suffix}"
        
        # Store the new context
        _trace_context.set({
            "trace_id": trace_id,
            "span_id": span_id
        })
    
    _tracing_token.set(token)
    return token


def set_tracing_token(token: str) -> bool:
    """
    Set the tracing token received from an upstream service.
    
    This establishes the trace context for all subsequent AI calls,
    linking them to the parent trace from the upstream service.
    
    Args:
        token: The tracing token from the upstream service
        
    Returns:
        bool: True if token was valid and context was set
        
    Example:
        >>> # In a FastAPI endpoint
        >>> @app.post("/api/process")
        >>> async def process(request: Request):
        ...     token = request.headers.get("X-AgentBill-Trace")
        ...     if token:
        ...         set_tracing_token(token)
        ...     
        ...     # All AI calls now linked to parent trace
        ...     response = await openai.chat.completions.create(...)
    """
    if not token or not token.startswith("agentbill-v1-"):
        return False
    
    try:
        parts = token.split("-")
        if len(parts) >= 5:
            # agentbill-v1-{trace_id}-{span_id}-{random}
            trace_id = parts[2]
            span_id = parts[3]
            
            _trace_context.set({
                "trace_id": trace_id,
                "span_id": span_id,
                "parent_token": token
            })
            _tracing_token.set(token)
            return True
    except Exception:
        pass
    
    return False


def get_tracing_token() -> Optional[str]:
    """
    Get the current tracing token.
    
    Returns:
        Optional[str]: The current tracing token or None
    """
    return _tracing_token.get()


def get_trace_context() -> Optional[Dict[str, str]]:
    """
    Get the current trace context (trace_id, span_id).
    
    Returns:
        Optional[Dict[str, str]]: Dict with trace_id and span_id, or None
        
    Example:
        >>> ctx = get_trace_context()
        >>> if ctx:
        ...     print(f"Trace ID: {ctx['trace_id']}")
        ...     print(f"Span ID: {ctx['span_id']}")
    """
    return _trace_context.get()


def clear_trace_context() -> None:
    """
    Clear the current trace context.
    
    Call this when you want to start a new trace that is not
    linked to the current context.
    """
    _trace_context.set(None)
    _tracing_token.set(None)


def set_trace_context(trace_id: str, span_id: str, parent_span_id: Optional[str] = None) -> None:
    """
    Manually set the trace context.
    
    Args:
        trace_id: The trace ID to set
        span_id: The span ID to set
        parent_span_id: Optional parent span ID for linking to predecessor span
        
    Example:
        >>> # Link to an existing OTEL trace with parent
        >>> set_trace_context(
        ...     trace_id="abc123",
        ...     span_id="def456",
        ...     parent_span_id="ghi789"
        ... )
    """
    ctx = {
        "trace_id": trace_id,
        "span_id": span_id
    }
    if parent_span_id:
        ctx["parent_span_id"] = parent_span_id
    _trace_context.set(ctx)


def propagate_trace_headers() -> Dict[str, str]:
    """
    Get HTTP headers for trace propagation.
    
    Returns headers that can be added to outgoing HTTP requests
    to propagate the trace context to downstream services.
    
    Returns:
        Dict[str, str]: Headers to add to HTTP requests
        
    Example:
        >>> headers = propagate_trace_headers()
        >>> response = requests.post(
        ...     "https://api.example.com/endpoint",
        ...     headers={**headers, "Content-Type": "application/json"}
        ... )
    """
    headers = {}
    
    token = get_tracing_token()
    if token:
        headers["X-AgentBill-Trace"] = token
    
    ctx = get_trace_context()
    if ctx:
        # Also include standard W3C trace context headers
        trace_id = ctx.get("trace_id", "")
        span_id = ctx.get("span_id", "")
        if trace_id and span_id:
            # W3C Trace Context format
            headers["traceparent"] = f"00-{trace_id}-{span_id}-01"
    
    return headers


def extract_trace_from_headers(headers: Dict[str, str]) -> bool:
    """
    Extract and set trace context from incoming HTTP headers.
    
    Supports both AgentBill tokens and W3C traceparent format.
    
    Args:
        headers: HTTP headers dict
        
    Returns:
        bool: True if trace context was extracted and set
        
    Example:
        >>> # In Flask
        >>> @app.route("/api/endpoint", methods=["POST"])
        >>> def endpoint():
        ...     extract_trace_from_headers(dict(request.headers))
        ...     # Now all AI calls are linked to the incoming trace
    """
    # Try AgentBill token first
    token = headers.get("X-AgentBill-Trace") or headers.get("x-agentbill-trace")
    if token and set_tracing_token(token):
        return True
    
    # Fall back to W3C traceparent
    traceparent = headers.get("traceparent") or headers.get("Traceparent")
    if traceparent:
        try:
            parts = traceparent.split("-")
            if len(parts) >= 4:
                trace_id = parts[1]
                span_id = parts[2]
                set_trace_context(trace_id, span_id)
                return True
        except Exception:
            pass
    
    return False
