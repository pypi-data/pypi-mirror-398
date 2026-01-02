"""Type definitions for AgentBill SDK"""
from typing import TypedDict, Optional


class AgentBillConfig(TypedDict):
    """Configuration for AgentBill SDK"""
    api_key: str  # Required
    base_url: Optional[str]  # Optional
    customer_id: Optional[str]  # Optional
    customer_external_id: Optional[str]  # Optional
    agent_id: Optional[str]  # Optional
    agent_external_id: Optional[str]  # Optional
    daily_budget: Optional[float]  # Optional
    monthly_budget: Optional[float]  # Optional
    debug: Optional[bool]  # Optional
    account_id: Optional[str]  # Optional


class TraceContext(TypedDict):
    """Trace context information"""
    trace_id: str
    span_id: str
    customer_id: Optional[str]
