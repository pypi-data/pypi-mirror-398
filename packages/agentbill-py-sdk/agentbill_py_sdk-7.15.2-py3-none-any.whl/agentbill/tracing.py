"""AgentBill Tracing Context Manager

Context manager and decorator for tracking AI operations with Cost Guard protection.
Implements the flow from the sequence diagram:
1. Pre-validate with ai-cost-guard-router
2. If blocked, raise BudgetExceededError
3. If allowed, execute AI calls
4. After completion, send spans to otel-collector
"""
import time
import uuid
import httpx
import functools
from typing import Optional, Dict, Any, Callable, TypeVar, Union
from contextlib import contextmanager

from .exceptions import BudgetExceededError, RateLimitExceededError, PolicyViolationError
from .distributed import set_trace_context, get_trace_context, clear_trace_context
from .signals import set_signal_config


F = TypeVar('F', bound=Callable[..., Any])


class TracingContext:
    """
    Internal class to manage tracing state within a context.
    """
    
    def __init__(
        self,
        api_key: str,
        customer_id: str,
        *,
        daily_budget: Optional[float] = None,
        monthly_budget: Optional[float] = None,
        agent_id: Optional[str] = None,
        base_url: str = "https://bgwyprqxtdreuutzpbgw.supabase.co",
        debug: bool = False,
        model: Optional[str] = None,
        estimated_tokens: int = 1000,
    ):
        self.api_key = api_key
        self.customer_id = customer_id
        self.daily_budget = daily_budget
        self.monthly_budget = monthly_budget
        self.agent_id = agent_id
        self.base_url = base_url
        self.debug = debug
        self.model = model
        self.estimated_tokens = estimated_tokens
        
        # Tracing state
        self.trace_id: Optional[str] = None
        self.span_id: Optional[str] = None
        self._parent_span_id: Optional[str] = None  # For nested context correlation
        self.start_time: Optional[float] = None
        self.validation_result: Optional[Dict] = None
        self.request_id: Optional[str] = None
        
        # Collected spans for OTEL export
        self.spans: list = []
    
    def _generate_ids(self) -> None:
        """Generate trace and span IDs, respecting existing context (v6.8.2 fix)."""
        existing = get_trace_context()
        
        if existing and existing.get("trace_id"):
            # Reuse existing trace_id for correlation (nested contexts)
            self.trace_id = existing["trace_id"]
            self._parent_span_id = existing.get("span_id")
        else:
            # Generate new trace_id only if no context exists
            self.trace_id = uuid.uuid4().hex
            self._parent_span_id = None
        
        # Always generate new span_id for this context
        self.span_id = uuid.uuid4().hex[:16]
        set_trace_context(self.trace_id, self.span_id)
    
    def _validate_budget(self) -> Dict:
        """
        Call ai-cost-guard-router for pre-validation.
        
        CRITICAL: This MUST be called before any AI calls.
        """
        url = f"{self.base_url}/functions/v1/ai-cost-guard-router"
        
        payload = {
            "api_key": self.api_key,
            "customer_id": self.customer_id,
            "model": self.model or "gpt-4",  # Default model for estimation
            "messages": [],  # Empty for pre-validation
            "estimated_tokens": self.estimated_tokens,
        }
        
        # Add optional budget overrides
        if self.daily_budget is not None:
            payload["daily_budget_override"] = self.daily_budget
        if self.monthly_budget is not None:
            payload["monthly_budget_override"] = self.monthly_budget
        if self.agent_id:
            payload["agent_id"] = self.agent_id
        
        try:
            with httpx.Client(timeout=10) as client:
                response = client.post(url, json=payload)
                
                if response.status_code >= 500:
                    # Server error - fail open (temporary issue)
                    if self.debug:
                        print(f"[AgentBill] ⚠️ Router server error {response.status_code} (failing open)")
                    return {"allowed": True, "reason": "Router server error (failed open)"}
                
                if response.status_code >= 400:
                    # Client error - fail closed
                    error_text = response.text
                    if self.debug:
                        print(f"[AgentBill] ❌ Router rejected: {error_text}")
                    return {"allowed": False, "reason": error_text}
                
                result = response.json()
                self.request_id = result.get("request_id")
                
                if self.debug:
                    if result.get("allowed"):
                        print(f"[AgentBill] ✓ Budget validation passed")
                    else:
                        print(f"[AgentBill] ❌ Budget validation failed: {result.get('reason')}")
                
                return result
                
        except Exception as e:
            if self.debug:
                print(f"[AgentBill] ⚠️ Router network error: {e} (failing open)")
            return {"allowed": True, "reason": "Router network error (failed open)"}
    
    def _export_spans(self) -> None:
        """
        Export collected spans to otel-collector.
        
        CRITICAL: Must send proper OTLP format with agent_id and customer_id
        as resource attributes for the otel-collector to extract them correctly.
        """
        if not self.spans:
            return
        
        url = f"{self.base_url}/functions/v1/otel-collector"
        
        # Build resource attributes - agent_id and customer_id MUST be here
        resource_attributes = [
            {"key": "service.name", "value": {"stringValue": "agentbill-python-sdk"}},
            {"key": "service.version", "value": {"stringValue": "6.8.10"}}
        ]
        
        if self.customer_id:
            resource_attributes.append(
                {"key": "customer.id", "value": {"stringValue": self.customer_id}}
            )
        
        if self.agent_id:
            resource_attributes.append(
                {"key": "agent.id", "value": {"stringValue": self.agent_id}}
            )
        
        # Convert spans to proper OTLP format
        otlp_spans = []
        for span in self.spans:
            otlp_span = {
                "traceId": span.get("trace_id", self.trace_id),
                "spanId": span.get("span_id", uuid.uuid4().hex[:16]),
                "name": span.get("name", "unknown"),
                "kind": 1,
                "startTimeUnixNano": str(span.get("start_time_unix_nano", int(time.time() * 1e9))),
                "endTimeUnixNano": str(span.get("end_time_unix_nano", int(time.time() * 1e9))),
                "attributes": [
                    {"key": k, "value": {"stringValue": str(v)} if isinstance(v, str) else {"intValue": int(v)} if isinstance(v, (int, float)) else {"stringValue": str(v)}}
                    for k, v in span.get("attributes", {}).items() if v is not None
                ],
                "status": span.get("status", {"code": 0})
            }
            if span.get("parent_span_id"):
                otlp_span["parentSpanId"] = span["parent_span_id"]
            otlp_spans.append(otlp_span)
        
        # Build proper OTLP payload
        payload = {
            "resourceSpans": [{
                "resource": {
                    "attributes": resource_attributes
                },
                "scopeSpans": [{
                    "scope": {"name": "agentbill", "version": "6.8.10"},
                    "spans": otlp_spans
                }]
            }]
        }
        
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        try:
            with httpx.Client(timeout=10) as client:
                response = client.post(url, json=payload, headers=headers)
                
                if self.debug:
                    if response.status_code == 200:
                        print(f"[AgentBill] ✓ Exported {len(self.spans)} spans to otel-collector")
                    else:
                        print(f"[AgentBill] ⚠️ Span export failed: {response.status_code} - {response.text}")
                        
        except Exception as e:
            if self.debug:
                print(f"[AgentBill] ⚠️ Span export error: {e}")
    
    def add_span(
        self,
        name: str,
        attributes: Dict[str, Any],
        start_time_ns: int,
        end_time_ns: int,
        status: int = 0,
    ) -> None:
        """Add a span to be exported."""
        span = {
            "trace_id": self.trace_id,
            "span_id": uuid.uuid4().hex[:16],
            "parent_span_id": self.span_id,
            "name": name,
            "attributes": attributes,
            "start_time_unix_nano": start_time_ns,
            "end_time_unix_nano": end_time_ns,
            "status": {"code": status},
        }
        self.spans.append(span)
    
    def cache_response(
        self,
        model: str,
        messages: Any,
        response_content: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
    ) -> None:
        """
        Cache AI response for semantic cache population.
        
        Call this after receiving an AI response within the context manager
        to populate the semantic cache.
        
        Args:
            model: AI model name (e.g., "gpt-4", "claude-3-sonnet")
            messages: The messages/prompt sent to the AI
            response_content: The AI's response text
            input_tokens: Number of input tokens (optional)
            output_tokens: Number of output tokens (optional)
            
        Example:
            >>> with agentbill_tracing(customer_id="cust-123", api_key="ab_xxx") as ctx:
            ...     response = openai.chat.completions.create(...)
            ...     ctx.cache_response(
            ...         model="gpt-4",
            ...         messages=[{"role": "user", "content": "Hello!"}],
            ...         response_content=response.choices[0].message.content,
            ...         input_tokens=response.usage.prompt_tokens,
            ...         output_tokens=response.usage.completion_tokens,
            ...     )
        """
        import hashlib
        import json
        
        # Generate prompt hash matching backend algorithm
        try:
            content = json.dumps(messages, separators=(',', ':'), default=str)
            prompt_hash = hashlib.sha256(content.encode()).hexdigest()
        except Exception:
            import uuid
            prompt_hash = uuid.uuid4().hex
        
        url = f"{self.base_url}/functions/v1/cache-ai-response"
        
        payload = {
            "api_key": self.api_key,
            "prompt_hash": prompt_hash,
            "response_content": response_content,
            "model": model,
            "prompt_content": json.dumps(messages, default=str) if not isinstance(messages, str) else messages,
            "tokens_used": input_tokens + output_tokens,
            "cacheable": True,
            "ttl_hours": 24,
        }
        
        if self.customer_id:
            payload["customer_id"] = self.customer_id
        if self.request_id:
            payload["request_id"] = self.request_id
        
        try:
            with httpx.Client(timeout=5) as client:
                response = client.post(url, json=payload)
                
                if self.debug:
                    if response.status_code == 200:
                        result = response.json()
                        print(f"[AgentBill] ✓ Cached response: {result.get('cached', False)}")
                    else:
                        print(f"[AgentBill] ⚠️ Cache failed: {response.status_code}")
                        
        except Exception as e:
            if self.debug:
                print(f"[AgentBill] ⚠️ Cache error (non-blocking): {e}")
    
    def enter(self) -> "TracingContext":
        """Enter the tracing context."""
        self._generate_ids()
        self.start_time = time.time()
        
        # Set global config for signal() function
        set_signal_config({
            "api_key": self.api_key,
            "customer_id": self.customer_id,
            "agent_id": self.agent_id,
            "base_url": self.base_url,
            "debug": self.debug,
        })
        
        # CRITICAL: Pre-validate with Cost Guard
        self.validation_result = self._validate_budget()
        
        # CRITICAL: Raise exception if not allowed
        if not self.validation_result.get("allowed"):
            reason = self.validation_result.get("reason", "Request blocked by Cost Guard")
            
            # Determine error type based on reason
            reason_lower = reason.lower()
            if "budget" in reason_lower:
                raise BudgetExceededError(reason, self.validation_result)
            elif "rate" in reason_lower:
                raise RateLimitExceededError(reason, self.validation_result)
            else:
                raise PolicyViolationError(reason, self.validation_result)
        
        return self
    
    def exit(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the tracing context."""
        end_time = time.time()
        
        # Add a root span for the entire context
        if self.start_time:
            self.add_span(
                name="agentbill_tracing",
                attributes={
                    "customer_id": self.customer_id,
                    "agent_id": self.agent_id,
                    "request_id": self.request_id,
                    "error": str(exc_val) if exc_val else None,
                },
                start_time_ns=int(self.start_time * 1e9),
                end_time_ns=int(end_time * 1e9),
                status=1 if exc_val else 0,
            )
        
        # Export spans to otel-collector
        self._export_spans()
        
        # Clear trace context
        clear_trace_context()


@contextmanager
def agentbill_tracing(
    customer_id: str,
    *,
    api_key: Optional[str] = None,
    daily_budget: Optional[float] = None,
    monthly_budget: Optional[float] = None,
    agent_id: Optional[str] = None,
    base_url: str = "https://bgwyprqxtdreuutzpbgw.supabase.co",
    debug: bool = False,
    model: Optional[str] = None,
    estimated_tokens: int = 1000,
):
    """
    Context manager for tracking AI operations with Cost Guard protection.
    
    This implements the full flow from the sequence diagram:
    1. Pre-validates with ai-cost-guard-router BEFORE any AI calls
    2. If budget exceeded, raises BudgetExceededError (blocks AI call)
    3. If allowed, executes the wrapped code
    4. After completion, exports spans to otel-collector
    
    Args:
        customer_id: Customer ID for budget tracking (REQUIRED)
        api_key: AgentBill API key (can also be set via AGENTBILL_API_KEY env var)
        daily_budget: Optional daily budget override (stricter than DB policy)
        monthly_budget: Optional monthly budget override (stricter than DB policy)
        agent_id: Optional agent ID for multi-agent tracking
        base_url: AgentBill backend URL
        debug: Enable debug logging
        model: Model hint for cost estimation
        estimated_tokens: Estimated tokens for pre-validation
        
    Raises:
        BudgetExceededError: If daily/monthly budget would be exceeded
        RateLimitExceededError: If rate limits would be exceeded
        PolicyViolationError: If other policy constraints are violated
        
    Example:
        >>> from agentbill import agentbill_tracing, signal, BudgetExceededError
        >>> import openai
        >>> 
        >>> try:
        ...     with agentbill_tracing(
        ...         customer_id="cust-123",
        ...         api_key="ab_xxx",
        ...         daily_budget=10.00
        ...     ):
        ...         # Cost Guard validates BEFORE this runs
        ...         response = openai.chat.completions.create(
        ...             model="gpt-4",
        ...             messages=[{"role": "user", "content": "Hello!"}]
        ...         )
        ...         
        ...         # Track business event linked to this trace
        ...         signal("chat_completed", revenue=0.50)
        ...         
        ... except BudgetExceededError as e:
        ...     print(f"Budget exceeded: {e.reason}")
        ...     # Handle gracefully - queue for later, show user message, etc.
    """
    import os
    
    # Get API key from argument or environment
    effective_api_key = api_key or os.environ.get("AGENTBILL_API_KEY")
    if not effective_api_key:
        raise ValueError("api_key is required. Provide it as argument or set AGENTBILL_API_KEY env var.")
    
    ctx = TracingContext(
        api_key=effective_api_key,
        customer_id=customer_id,
        daily_budget=daily_budget,
        monthly_budget=monthly_budget,
        agent_id=agent_id,
        base_url=base_url,
        debug=debug,
        model=model,
        estimated_tokens=estimated_tokens,
    )
    
    try:
        yield ctx.enter()
    except (BudgetExceededError, RateLimitExceededError, PolicyViolationError):
        # Re-raise Cost Guard exceptions without modification
        raise
    except Exception as e:
        ctx.exit(type(e), e, e.__traceback__)
        raise
    else:
        ctx.exit(None, None, None)


def agentbill_traced(
    customer_id: str = None,
    *,
    api_key: Optional[str] = None,
    daily_budget: Optional[float] = None,
    monthly_budget: Optional[float] = None,
    agent_id: Optional[str] = None,
    base_url: str = "https://bgwyprqxtdreuutzpbgw.supabase.co",
    debug: bool = False,
    customer_id_arg: str = None,
) -> Callable[[F], F]:
    """
    Decorator for tracking AI operations with Cost Guard protection.
    
    Same as agentbill_tracing but as a decorator for functions.
    
    Args:
        customer_id: Static customer ID (or use customer_id_arg for dynamic)
        api_key: AgentBill API key
        daily_budget: Optional daily budget override
        monthly_budget: Optional monthly budget override
        agent_id: Optional agent ID
        base_url: AgentBill backend URL
        debug: Enable debug logging
        customer_id_arg: Name of function argument containing customer_id (for dynamic)
        
    Example:
        >>> @agentbill_traced(customer_id="cust-123", api_key="ab_xxx")
        ... def process_request(message: str):
        ...     return openai.chat.completions.create(
        ...         model="gpt-4",
        ...         messages=[{"role": "user", "content": message}]
        ...     )
        
        >>> # Or with dynamic customer_id from function argument
        >>> @agentbill_traced(customer_id_arg="user_id", api_key="ab_xxx")
        ... def process_user_request(user_id: str, message: str):
        ...     return openai.chat.completions.create(...)
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Determine customer_id
            effective_customer_id = customer_id
            if customer_id_arg and customer_id_arg in kwargs:
                effective_customer_id = kwargs[customer_id_arg]
            
            if not effective_customer_id:
                raise ValueError("customer_id is required for agentbill_traced decorator")
            
            with agentbill_tracing(
                customer_id=effective_customer_id,
                api_key=api_key,
                daily_budget=daily_budget,
                monthly_budget=monthly_budget,
                agent_id=agent_id,
                base_url=base_url,
                debug=debug,
            ):
                return func(*args, **kwargs)
        
        return wrapper  # type: ignore
    return decorator
