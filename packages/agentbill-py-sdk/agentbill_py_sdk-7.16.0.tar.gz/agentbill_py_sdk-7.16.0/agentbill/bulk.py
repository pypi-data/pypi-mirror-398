"""AgentBill Bulk Operations

Batch recording of signals and usage data for improved efficiency.
"""
import httpx
from typing import Optional, Dict, Any, List
from .signals import get_signal_config
import time
import uuid
import json


def record_bulk(
    records: List[Dict[str, Any]],
    *,
    customer_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Record multiple signals/events in a single batch request.
    
    This is more efficient than calling signal() multiple times
    when you have many events to record at once.
    
    Args:
        records: List of record dictionaries, each containing:
            - event_name (str, required): Name of the event
            - revenue (float, optional): Revenue amount
            - metadata (dict, optional): Additional metadata
            - trace_id (str, optional): Trace ID to link to
            - span_id (str, optional): Span ID to link to
            - order_id (str, optional): Order ID to link to
            - order_external_id (str, optional): External order ID
            - event_type (str, optional): Event type
            - event_value (float, optional): Event value
        customer_id: Default customer ID for all records (can be overridden per-record)
        
    Returns:
        Dict with success status and results per record
        
    Example:
        >>> record_bulk([
        ...     {"event_name": "page_view", "metadata": {"page": "/home"}},
        ...     {"event_name": "purchase", "revenue": 99.99, "order_id": "ord-123"},
        ...     {"event_name": "signup", "event_type": "conversion", "event_value": 1},
        ... ], customer_id="cust-456")
    """
    config = get_signal_config()
    
    api_key = config.get("api_key")
    if not api_key:
        raise ValueError("AgentBill not initialized. Call AgentBill.init() first.")
    
    if not records:
        return {"success": True, "processed": 0, "results": []}
    
    default_customer_id = customer_id or config.get("customer_id")
    base_url = config.get("base_url", "https://bgwyprqxtdreuutzpbgw.supabase.co")
    url = f"{base_url}/functions/v1/otel-collector"
    debug = config.get("debug", False)
    
    # Build spans for all records
    spans = []
    results = []
    
    for i, record in enumerate(records):
        event_name = record.get("event_name")
        if not event_name:
            results.append({
                "index": i,
                "success": False,
                "error": "event_name is required"
            })
            continue
        
        record_customer_id = record.get("customer_id", default_customer_id)
        generated_trace_id = record.get("trace_id") or uuid.uuid4().hex
        generated_span_id = record.get("span_id") or uuid.uuid4().hex[:16]
        now_ns = int(time.time() * 1_000_000_000)
        
        # Build attributes
        attributes = [
            {"key": "agentbill.event_name", "value": {"stringValue": event_name}},
            {"key": "agentbill.is_business_event", "value": {"boolValue": True}},
            {"key": "agentbill.bulk_index", "value": {"intValue": str(i)}},
        ]
        
        if record_customer_id:
            attributes.append({"key": "agentbill.customer_id", "value": {"stringValue": record_customer_id}})
        
        if config.get("agent_id"):
            attributes.append({"key": "agentbill.agent_id", "value": {"stringValue": config.get("agent_id")}})
        
        if record.get("revenue") is not None:
            attributes.append({"key": "agentbill.revenue", "value": {"doubleValue": record["revenue"]}})
            attributes.append({"key": "agentbill.currency", "value": {"stringValue": record.get("currency", "USD")}})
        
        if record.get("event_value") is not None:
            attributes.append({"key": "agentbill.event_value", "value": {"doubleValue": record["event_value"]}})
        
        if record.get("event_type"):
            attributes.append({"key": "agentbill.event_type", "value": {"stringValue": record["event_type"]}})
        
        if record.get("session_id"):
            attributes.append({"key": "agentbill.session_id", "value": {"stringValue": record["session_id"]}})
        
        if record.get("order_id"):
            attributes.append({"key": "agentbill.order_id", "value": {"stringValue": record["order_id"]}})
        
        if record.get("order_external_id"):
            attributes.append({"key": "agentbill.order_external_id", "value": {"stringValue": record["order_external_id"]}})
        
        if record.get("metadata"):
            attributes.append({"key": "agentbill.metadata", "value": {"stringValue": json.dumps(record["metadata"])}})
        
        spans.append({
            "traceId": generated_trace_id,
            "spanId": generated_span_id,
            "parentSpanId": record.get("parent_span_id", ""),
            "name": "agentbill.trace.signal",
            "kind": 1,
            "startTimeUnixNano": str(now_ns),
            "endTimeUnixNano": str(now_ns),
            "attributes": attributes,
            "status": {"code": 1}
        })
        
        results.append({
            "index": i,
            "success": True,  # Will be updated if request fails
            "trace_id": generated_trace_id,
            "span_id": generated_span_id,
        })
    
    if not spans:
        return {"success": False, "processed": 0, "results": results, "error": "No valid records to process"}
    
    # Build OTEL payload with all spans
    payload = {
        "resourceSpans": [{
            "resource": {
                "attributes": [
                    {"key": "service.name", "value": {"stringValue": "agentbill-python-sdk"}},
                    {"key": "agentbill.customer_id", "value": {"stringValue": default_customer_id or ""}},
                    {"key": "agentbill.agent_id", "value": {"stringValue": config.get("agent_id", "")}},
                    {"key": "agentbill.bulk_request", "value": {"boolValue": True}},
                ]
            },
            "scopeSpans": [{
                "scope": {"name": "agentbill.signals.bulk", "version": "7.8.0"},
                "spans": spans
            }]
        }]
    }
    
    try:
        with httpx.Client(timeout=30) as client:
            response = client.post(
                url,
                json=payload,
                headers={"x-api-key": api_key, "Content-Type": "application/json"}
            )
            
            response_data = {}
            body_success = True
            try:
                response_data = response.json()
                body_success = response_data.get("success", True)
            except Exception:
                pass
            
            is_success = response.status_code == 200 and body_success
            
            if debug:
                if is_success:
                    print(f"[AgentBill] ✓ Bulk recorded {len(spans)} signals")
                else:
                    print(f"[AgentBill] ⚠️ Bulk recording failed: {response_data.get('error', response.text)}")
            
            # Update results on failure
            if not is_success:
                for r in results:
                    if r.get("success"):
                        r["success"] = False
                        r["error"] = response_data.get("error", "Bulk request failed")
            
            return {
                "success": is_success,
                "processed": len(spans),
                "results": results,
                "error": response_data.get("error") if not is_success else None,
            }
            
    except Exception as e:
        if debug:
            print(f"[AgentBill] ⚠️ Bulk recording error: {e}")
        
        for r in results:
            if r.get("success"):
                r["success"] = False
                r["error"] = str(e)
        
        return {
            "success": False,
            "processed": 0,
            "results": results,
            "error": str(e),
        }
