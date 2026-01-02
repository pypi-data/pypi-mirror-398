"""AgentBill LangChain Signals - v7.6.11

Full standalone signal tracking for business events.
"""

import os
import time
import secrets
import json
from typing import Optional, Dict, Any

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False
    import urllib.request
    import urllib.error

from .tracing import get_trace_context, VERSION
from .exceptions import ValidationError

BASE_URL = "https://bgwyprqxtdreuutzpbgw.supabase.co"

# Global configuration
_config: Dict[str, Any] = {}


def set_signal_config(
    api_key: Optional[str] = None,
    customer_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    base_url: str = BASE_URL,
    debug: bool = False
) -> None:
    """Set global configuration for signal tracking."""
    global _config
    _config = {
        "api_key": api_key,
        "customer_id": customer_id,
        "agent_id": agent_id,
        "base_url": base_url,
        "debug": debug
    }


def get_signal_config() -> Dict[str, Any]:
    """Get the current signal configuration."""
    return _config.copy()


def _generate_hex_id(num_bytes: int) -> str:
    """Generate a random hex ID."""
    return secrets.token_hex(num_bytes)


def _log(debug: bool, message: str) -> None:
    """Log a debug message if debugging is enabled."""
    if debug:
        print(f"[AgentBill] {message}")


def _http_post(url: str, payload: Dict[str, Any], timeout: float = 10.0, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Make an HTTP POST request."""
    all_headers = {
        "Content-Type": "application/json",
        **(headers or {})
    }
    
    if HAS_HTTPX:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(url, json=payload, headers=all_headers)
            if response.status_code >= 400:
                return {"status_code": response.status_code, "body": response.text, "success": False}
            return {"status_code": response.status_code, "body": response.json() if response.text else {}, "success": True}
    else:
        # Fallback to urllib
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=all_headers, method='POST')
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                body = response.read().decode('utf-8')
                return {"status_code": response.status, "body": json.loads(body) if body else {}, "success": True}
        except urllib.error.HTTPError as e:
            return {"status_code": e.code, "body": e.read().decode('utf-8'), "success": False}


def signal(
    event_name: str,
    *,
    revenue: Optional[float] = None,
    customer_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    span_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    debug: Optional[bool] = None
) -> Dict[str, Any]:
    """
    Emit a business signal for revenue attribution.
    
    Signals are used to track business events (conversions, purchases, etc.)
    and link them back to AI operations for ROI analysis.
    
    Example:
        # Track a conversion event
        signal("purchase_completed", revenue=99.99, customer_id="cust_123")
        
        # Track with trace context for attribution
        signal(
            "subscription_upgraded",
            revenue=49.99,
            trace_id=ctx.trace_id,
            span_id=ctx.span_id
        )
    
    Args:
        event_name: Name of the business event
        revenue: Revenue amount associated with this event
        customer_id: Customer identifier (uses config if not provided)
        agent_id: Agent identifier (uses config if not provided)
        trace_id: OTEL trace ID for attribution (auto-detected if not provided)
        span_id: OTEL span ID for attribution (auto-detected if not provided)
        metadata: Additional event metadata
        api_key: API key (uses config or env if not provided)
        base_url: API base URL (uses config if not provided)
        debug: Enable debug logging (uses config if not provided)
    
    Returns:
        Response from the signal API
    
    Raises:
        ValidationError: If required parameters are missing
    """
    # Merge with global config
    resolved_api_key = api_key or _config.get("api_key") or os.environ.get("AGENTBILL_API_KEY")
    resolved_customer_id = customer_id or _config.get("customer_id")
    resolved_agent_id = agent_id or _config.get("agent_id")
    resolved_base_url = base_url or _config.get("base_url") or BASE_URL
    resolved_debug = debug if debug is not None else _config.get("debug", False)
    
    if not resolved_api_key:
        raise ValidationError("api_key is required. Provide it, use set_signal_config(), or set AGENTBILL_API_KEY env var.", "api_key")
    
    if not event_name:
        raise ValidationError("event_name is required", "event_name")
    
    # Auto-detect trace context if not provided
    if trace_id is None or span_id is None:
        ctx = get_trace_context()
        if ctx:
            trace_id = trace_id or ctx.get("trace_id")
            span_id = span_id or ctx.get("span_id")
    
    # Generate IDs if still not available
    if not trace_id:
        trace_id = _generate_hex_id(16)
    if not span_id:
        span_id = _generate_hex_id(8)
    
    # Build OTEL-compliant signal payload
    url = f"{resolved_base_url}/functions/v1/track-ai-usage"
    
    timestamp_ns = int(time.time() * 1_000_000_000)
    
    resource_attributes = [
        {"key": "service.name", "value": {"stringValue": "agentbill-langchain-sdk"}},
        {"key": "service.version", "value": {"stringValue": VERSION}},
    ]
    
    if resolved_customer_id:
        resource_attributes.append({
            "key": "customer.id",
            "value": {"stringValue": resolved_customer_id}
        })
    if resolved_agent_id:
        resource_attributes.append({
            "key": "agent.id",
            "value": {"stringValue": resolved_agent_id}
        })
    
    span_attributes = [
        {"key": "event.name", "value": {"stringValue": event_name}},
        {"key": "signal.type", "value": {"stringValue": "business_event"}},
    ]
    
    if revenue is not None:
        span_attributes.append({
            "key": "revenue",
            "value": {"doubleValue": revenue}
        })
    
    if metadata:
        for k, v in metadata.items():
            if isinstance(v, str):
                span_attributes.append({"key": f"metadata.{k}", "value": {"stringValue": v}})
            elif isinstance(v, (int, float)):
                span_attributes.append({"key": f"metadata.{k}", "value": {"doubleValue": v}})
            else:
                span_attributes.append({"key": f"metadata.{k}", "value": {"stringValue": str(v)}})
    
    payload = {
        "resourceSpans": [{
            "resource": {"attributes": resource_attributes},
            "scopeSpans": [{
                "scope": {"name": "agentbill", "version": VERSION},
                "spans": [{
                    "traceId": trace_id,
                    "spanId": span_id,
                    "name": f"signal.{event_name}",
                    "kind": 1,
                    "startTimeUnixNano": str(timestamp_ns),
                    "endTimeUnixNano": str(timestamp_ns),
                    "attributes": span_attributes,
                    "status": {"code": 0}
                }]
            }]
        }]
    }
    
    headers = {"X-API-Key": resolved_api_key}
    
    try:
        result = _http_post(url, payload, timeout=10.0, headers=headers)
        
        if result.get("success"):
            _log(resolved_debug, f"✓ Signal '{event_name}' tracked successfully")
        else:
            _log(resolved_debug, f"⚠️ Signal tracking failed: {result.get('body')}")
        
        return {
            "success": result.get("success", False),
            "trace_id": trace_id,
            "span_id": span_id,
            "event_name": event_name
        }
        
    except Exception as e:
        _log(resolved_debug, f"⚠️ Signal tracking error: {e}")
        return {
            "success": False,
            "error": str(e),
            "trace_id": trace_id,
            "span_id": span_id,
            "event_name": event_name
        }


def track_conversion(
    event_type: str,
    event_value: float,
    *,
    customer_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    span_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    debug: Optional[bool] = None
) -> Dict[str, Any]:
    """
    Track a conversion event with revenue attribution.
    
    This is a convenience wrapper around signal() specifically for
    conversion/purchase events.
    
    Example:
        track_conversion("purchase", 99.99, customer_id="cust_123")
    
    Args:
        event_type: Type of conversion event
        event_value: Revenue value of the conversion
        customer_id: Customer identifier
        agent_id: Agent identifier
        trace_id: OTEL trace ID for attribution
        span_id: OTEL span ID for attribution
        metadata: Additional event metadata
        api_key: API key
        base_url: API base URL
        debug: Enable debug logging
    
    Returns:
        Response from the signal API
    """
    return signal(
        event_name=f"conversion.{event_type}",
        revenue=event_value,
        customer_id=customer_id,
        agent_id=agent_id,
        trace_id=trace_id,
        span_id=span_id,
        metadata=metadata,
        api_key=api_key,
        base_url=base_url,
        debug=debug
    )


__all__ = [
    "signal",
    "track_conversion",
    "set_signal_config",
    "get_signal_config",
]
