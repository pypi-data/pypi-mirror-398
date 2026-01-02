"""OpenTelemetry Tracer for AgentBill"""
import json
import time
import uuid
import httpx
from typing import Dict, Any, Optional
from .types import AgentBillConfig


class Span:
    """Represents an OpenTelemetry span"""
    
    def __init__(self, name: str, trace_id: str, span_id: str, parent_span_id: Optional[str], attributes: Dict[str, Any]):
        self.name = name
        self.trace_id = trace_id
        self.span_id = span_id
        self.parent_span_id = parent_span_id
        self.attributes = attributes
        self.start_time = time.time_ns()
        self.end_time: Optional[int] = None
        self.status = {"code": 0}
    
    def set_attributes(self, attributes: Dict[str, Any]):
        self.attributes.update(attributes)
    
    def set_status(self, code: int, message: str = ""):
        self.status = {"code": code, "message": message}
    
    def end(self):
        self.end_time = time.time_ns()


class AgentBillTracer:
    """OpenTelemetry tracer for AgentBill
    
    IMPORTANT: This tracer integrates with distributed.py for trace context.
    - If a trace context exists (via get_trace_context()), it reuses the trace_id
    - Always generates a new span_id for each span
    - Updates the global trace context so get_trace_context() returns correct values
    
    This ensures that:
    1. get_trace_context() always returns the trace_id that matches what's sent to the portal
    2. Distributed tracing works correctly across services
    3. Parent-child span relationships are properly maintained
    """
    
    def __init__(self, config: AgentBillConfig):
        self.config = config
        self.base_url = config.get("base_url", "https://bgwyprqxtdreuutzpbgw.supabase.co")
        self.api_key = config["api_key"]
        self.customer_id = config.get("customer_id")
        self.debug = config.get("debug", False)
        self.spans = []
    
    def start_span(self, name: str, attributes: Dict[str, Any]) -> Span:
        """Start a new span and return it with trace_id and span_id for correlation.
        
        IMPORTANT: Uses distributed.py as the single source of truth for trace context.
        - Reuses existing trace_id if available (for span correlation within same trace)
        - Always generates new span_id (each span is unique)
        - Updates global trace context so get_trace_context() returns correct values
        """
        from .distributed import get_trace_context, set_trace_context
        
        # Check for existing trace context
        ctx = get_trace_context()
        parent_span_id = None
        
        if ctx:
            # Reuse existing trace_id for correlation
            trace_id = ctx.get("trace_id")
            # Store parent span_id for proper OTEL hierarchy
            parent_span_id = ctx.get("span_id")
            if self.debug:
                print(f"[AgentBill Tracer] Using existing trace context: trace_id={trace_id[:8]}...")
        else:
            # Generate new trace_id for new trace
            trace_id = uuid.uuid4().hex
            if self.debug:
                print(f"[AgentBill Tracer] Creating new trace: trace_id={trace_id[:8]}...")
        
        # Always generate new span_id for this span
        span_id = uuid.uuid4().hex[:16]
        
        # Update global trace context so get_trace_context() returns correct values
        set_trace_context(trace_id, span_id)
        
        attributes["service.name"] = "agentbill-python-sdk"
        if self.customer_id:
            attributes["customer.id"] = self.customer_id
        
        span = Span(name, trace_id, span_id, parent_span_id, attributes)
        self.spans.append(span)
        
        if self.debug:
            print(f"[AgentBill Tracer] Started span: {name}, trace_id={trace_id[:8]}..., span_id={span_id[:8]}...")
        
        # Return span which has trace_id and span_id as properties
        return span
    
    def flush_sync(self):
        """Synchronous flush for non-async contexts"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, schedule the task
                asyncio.create_task(self.flush())
            else:
                # If no loop, run it
                loop.run_until_complete(self.flush())
        except RuntimeError:
            # No event loop exists, create one
            asyncio.run(self.flush())
    
    async def flush(self):
        """Flush spans to AgentBill"""
        if not self.spans:
            if self.debug:
                print("AgentBill: No spans to flush")
            return
        
        payload = self._build_otlp_payload()
        url = f"{self.base_url}/functions/v1/otel-collector"
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        if self.debug:
            print(f"AgentBill: Flushing {len(self.spans)} spans to {url}")
            print(f"AgentBill: API Key: {self.api_key[:12]}...")
            print(f"AgentBill: Full headers being sent: {headers}")
            print(f"AgentBill: Payload preview: {str(payload)[:200]}...")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                
                if self.debug:
                    print(f"AgentBill flush response code: {response.status_code}")
                    print(f"AgentBill response headers: {dict(response.headers)}")
                    print(f"AgentBill response body: {response.text[:500]}")
                
                if response.status_code == 200:
                    self.spans.clear()
                    if self.debug:
                        print("AgentBill: ✅ Spans successfully flushed")
                else:
                    if self.debug:
                        print(f"AgentBill: ❌ Flush failed with status {response.status_code}")
            except Exception as e:
                if self.debug:
                    print(f"AgentBill flush error: {type(e).__name__}: {e}")
    
    def _build_otlp_payload(self) -> Dict[str, Any]:
        """Build OTLP export payload
        
        IMPORTANT: agent_id and customer_id must be sent as resource attributes
        for the otel-collector to extract them correctly.
        
        v6.8.6 FIX: Check signal config for agent_id set by @agentbill_traced decorator,
        falling back to AgentBill config. This fixes the issue where agent_id passed
        to the decorator wasn't being propagated to wrap_openai() spans.
        """
        from .signals import get_signal_config
        
        resource_attributes = [
            {"key": "service.name", "value": {"stringValue": "agentbill-python-sdk"}},
            {"key": "service.version", "value": {"stringValue": "7.2.0"}}
        ]
        
        # Get signal config which may have agent_id from @agentbill_traced decorator
        signal_config = get_signal_config() or {}
        
        # Add customer_id: prefer signal config, then check external_customer_id as alias, fallback to tracer config
        customer_id = (
            signal_config.get("customer_id") or 
            signal_config.get("external_customer_id") or 
            self.customer_id or 
            self.config.get("external_customer_id")
        )
        if customer_id:
            resource_attributes.append(
                {"key": "customer.id", "value": {"stringValue": customer_id}}
            )
        
        # Add external_customer_id as separate attribute for lookup (always send if configured)
        external_customer_id = (
            signal_config.get("external_customer_id") or 
            self.config.get("external_customer_id")
        )
        if external_customer_id:
            resource_attributes.append(
                {"key": "customer.external_id", "value": {"stringValue": external_customer_id}}
            )
        
        # Add agent_id: prefer signal config (from decorator), fallback to tracer config
        # This is the CRITICAL fix - decorator's agent_id now propagates to wrap_openai spans
        agent_id = signal_config.get("agent_id") or self.config.get("agent_id")
        if agent_id:
            resource_attributes.append(
                {"key": "agent.id", "value": {"stringValue": agent_id}}
            )
        
        return {
            "resourceSpans": [{
                "resource": {
                    "attributes": resource_attributes
                },
                "scopeSpans": [{
                    "scope": {"name": "agentbill", "version": "7.0.4"},
                    "spans": [self._span_to_otlp(span) for span in self.spans]
                }]
            }]
        }
    
    def _span_to_otlp(self, span: Span) -> Dict[str, Any]:
        """Convert span to OTLP format"""
        otlp_span = {
            "traceId": span.trace_id,
            "spanId": span.span_id,
            "name": span.name,
            "kind": 1,  # CLIENT
            "startTimeUnixNano": str(span.start_time),
            "endTimeUnixNano": str(span.end_time or time.time_ns()),
            "attributes": [
                {"key": k, "value": self._value_to_otlp(v)}
                for k, v in span.attributes.items()
            ],
            "status": span.status
        }
        
        # Add parent span ID if this is a child span
        if span.parent_span_id:
            otlp_span["parentSpanId"] = span.parent_span_id
        
        return otlp_span
    
    def _value_to_otlp(self, value: Any) -> Dict[str, Any]:
        """Convert value to OTLP format"""
        if isinstance(value, str):
            return {"stringValue": value}
        elif isinstance(value, (int, float)):
            return {"intValue": int(value)}
        elif isinstance(value, bool):
            return {"boolValue": value}
        else:
            return {"stringValue": str(value)}