"""AgentBill Signals

Signal function for tracking business events and linking revenue to AI traces.
"""
import httpx
from typing import Optional, Dict, Any
from .distributed import get_trace_context


# Global configuration - set by AgentBill.init() or agentbill_tracing
_global_config: Dict[str, Any] = {}


def set_signal_config(config: Dict[str, Any]) -> None:
    """Set global configuration for signal() function."""
    global _global_config
    _global_config = config


def get_signal_config() -> Dict[str, Any]:
    """Get current global configuration."""
    return _global_config


def signal(
    event_name: str,
    revenue: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None,
    *,
    customer_id: Optional[str] = None,
    session_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    span_id: Optional[str] = None,
    parent_span_id: Optional[str] = None,  # v6.8.10: Links to predecessor span
    currency: str = "USD",
    event_type: Optional[str] = None,
    event_value: Optional[float] = None,
    order_id: Optional[str] = None,  # v7.8.0: Link signal to an order
    order_external_id: Optional[str] = None,  # v7.8.0: Link via external order ID
) -> Dict[str, Any]:
    """
    Emit a business signal/event and link it to AI traces.
    
    This function posts to /otel-collector to record business events
    (conversions, purchases, signups) and link them to the AI traces
    via trace_id for revenue attribution.
    
    Args:
        event_name: Name of the business event (e.g., "purchase", "signup", "conversion")
        revenue: Revenue amount associated with this event
        metadata: Additional metadata for the event
        customer_id: Customer ID (uses global config if not provided)
        session_id: Session ID for attribution
        trace_id: Trace ID to link to (auto-detected from context if not provided)
        span_id: Span ID to link to (auto-detected from context if not provided)
        currency: Currency for revenue (default: USD)
        event_type: Type of event for categorization
        event_value: Numeric value of the event
        order_id: Order ID to link this signal to (for order-level attribution)
        order_external_id: External order ID to link this signal to
        
    Returns:
        Dict with status and any response data
        
    Example:
        >>> # After a successful purchase
        >>> signal(
        ...     event_name="purchase",
        ...     revenue=99.99,
        ...     metadata={"product_id": "prod-123", "quantity": 1}
        ... )
        
        >>> # Track a conversion with explicit trace linking
        >>> signal(
        ...     event_name="signup_complete",
        ...     event_type="conversion",
        ...     event_value=1,
        ...     trace_id="abc123"  # Links to the AI call that led to signup
        ... )
    """
    config = get_signal_config()
    
    # Get API key from config
    api_key = config.get("api_key")
    if not api_key:
        raise ValueError("AgentBill not initialized. Call AgentBill.init() first or use agentbill_tracing context.")
    
    # Use provided customer_id or fall back to config
    effective_customer_id = customer_id or config.get("customer_id")
    
    import time
    import uuid
    
    # Auto-detect trace context if not provided (v7.0.4: Fix span_id collision)
    ctx = get_trace_context()
    if ctx:
        trace_id = trace_id or ctx.get("trace_id")
        # v7.0.4 FIX: The signal span MUST have its own unique span_id
        # The context's span_id becomes our parent_span_id (linking signal to the AI call)
        # Previously this was reusing the same span_id which caused duplicate key errors
        if not parent_span_id:
            parent_span_id = ctx.get("span_id")  # Link to the AI call span
    
    # Build the OTEL span payload for signal (v7.0.0: Unified OTEL approach)
    base_url = config.get("base_url", "https://bgwyprqxtdreuutzpbgw.supabase.co")
    url = f"{base_url}/functions/v1/otel-collector"
    
    # v7.0.4: Signal ALWAYS gets a unique span_id, never reuses from context
    generated_span_id = span_id or uuid.uuid4().hex[:16]
    generated_trace_id = trace_id or uuid.uuid4().hex
    now_ns = int(time.time() * 1_000_000_000)
    
    # Build OTEL-compliant span attributes
    attributes = [
        {"key": "agentbill.event_name", "value": {"stringValue": event_name}},
        {"key": "agentbill.is_business_event", "value": {"boolValue": True}},
    ]
    
    if effective_customer_id:
        attributes.append({"key": "agentbill.customer_id", "value": {"stringValue": effective_customer_id}})
    
    if config.get("agent_id"):
        attributes.append({"key": "agentbill.agent_id", "value": {"stringValue": config.get("agent_id")}})
    
    if revenue is not None:
        attributes.append({"key": "agentbill.revenue", "value": {"doubleValue": revenue}})
        attributes.append({"key": "agentbill.currency", "value": {"stringValue": currency}})
    
    if event_value is not None:
        attributes.append({"key": "agentbill.event_value", "value": {"doubleValue": event_value}})
    
    if event_type:
        attributes.append({"key": "agentbill.event_type", "value": {"stringValue": event_type}})
    
    if session_id:
        attributes.append({"key": "agentbill.session_id", "value": {"stringValue": session_id}})
    
    if parent_span_id:
        attributes.append({"key": "agentbill.parent_span_id", "value": {"stringValue": parent_span_id}})
    
    # v7.8.0: Order linking
    if order_id:
        attributes.append({"key": "agentbill.order_id", "value": {"stringValue": order_id}})
    
    if order_external_id:
        attributes.append({"key": "agentbill.order_external_id", "value": {"stringValue": order_external_id}})
    
    if metadata:
        import json
        attributes.append({"key": "agentbill.metadata", "value": {"stringValue": json.dumps(metadata)}})
    
    # Build OTEL payload with signal span name
    payload = {
        "resourceSpans": [{
            "resource": {
                "attributes": [
                    {"key": "service.name", "value": {"stringValue": "agentbill-python-sdk"}},
                    {"key": "agentbill.customer_id", "value": {"stringValue": effective_customer_id or ""}},
                    {"key": "agentbill.agent_id", "value": {"stringValue": config.get("agent_id", "")}},
                ]
            },
            "scopeSpans": [{
                "scope": {"name": "agentbill.signals", "version": "7.0.4"},
                "spans": [{
                    "traceId": generated_trace_id,
                    "spanId": generated_span_id,
                    "parentSpanId": parent_span_id or "",
                    "name": "agentbill.trace.signal",  # v7.0.0: Unified signal span name
                    "kind": 1,
                    "startTimeUnixNano": str(now_ns),
                    "endTimeUnixNano": str(now_ns),
                    "attributes": attributes,
                    "status": {"code": 1}
                }]
            }]
        }]
    }
    
    debug = config.get("debug", False)
    
    try:
        with httpx.Client(timeout=10) as client:
            response = client.post(
                url,
                json=payload,
                headers={"x-api-key": api_key, "Content-Type": "application/json"}
            )
            
            # v7.0.3 fix: Check response body for success, not just HTTP status
            response_data = {}
            body_success = True
            try:
                response_data = response.json()
                # Backend returns {success: false} with HTTP 200 on validation errors
                body_success = response_data.get("success", True)
            except Exception:
                pass  # If can't parse JSON, fall back to HTTP status check
            
            is_success = response.status_code == 200 and body_success
            
            if debug:
                if is_success:
                    print(f"[AgentBill] ✓ Signal '{event_name}' tracked via OTEL")
                    if revenue:
                        print(f"[AgentBill]   Revenue: ${revenue:.2f} {currency}")
                    if generated_trace_id:
                        print(f"[AgentBill]   Trace ID: {generated_trace_id}")
                else:
                    error_msg = response_data.get("error", response.text)
                    errors = response_data.get("errors", [])
                    print(f"[AgentBill] ⚠️ Signal tracking failed: {error_msg}")
                    if errors:
                        for err in errors:
                            print(f"[AgentBill]   - {err}")
            
            return {
                "success": is_success,
                "status_code": response.status_code,
                "trace_id": generated_trace_id,
                "span_id": generated_span_id,
                "error": response_data.get("error") if not is_success else None,
                "errors": response_data.get("errors") if not is_success else None,
            }
            
    except Exception as e:
        if debug:
            print(f"[AgentBill] ⚠️ Signal tracking error: {e}")
        
        return {
            "success": False,
            "error": str(e),
            "trace_id": generated_trace_id,
        }


def track_conversion(
    event_type: str,
    event_value: float,
    *,
    currency: str = "USD",
    session_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Track a conversion event for revenue attribution.
    
    Convenience wrapper around signal() for conversion tracking.
    
    Args:
        event_type: Type of conversion (e.g., "purchase", "signup", "subscription")
        event_value: Value of the conversion
        currency: Currency for the value
        session_id: Session ID for attribution window
        metadata: Additional conversion metadata
        
    Returns:
        Dict with status and response data
        
    Example:
        >>> track_conversion(
        ...     event_type="purchase",
        ...     event_value=49.99,
        ...     metadata={"plan": "pro", "billing": "monthly"}
        ... )
    """
    return signal(
        event_name=f"conversion_{event_type}",
        revenue=event_value,
        event_type=event_type,
        event_value=event_value,
        currency=currency,
        session_id=session_id,
        metadata=metadata,
    )
