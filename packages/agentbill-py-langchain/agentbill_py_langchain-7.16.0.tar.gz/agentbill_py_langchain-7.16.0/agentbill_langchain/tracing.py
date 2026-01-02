"""AgentBill LangChain Tracing - v7.6.11

Full standalone tracing context manager with Cost Guard protection.
Implements the complete flow from the sequence diagram:
1. Pre-validate with ai-cost-guard-router
2. If blocked, raise BudgetExceededError
3. If allowed, execute AI calls
4. After completion, send spans to otel-collector
"""

import os
import time
import hashlib
import secrets
from typing import Optional, Dict, Any, List, TypeVar, Callable, AsyncGenerator
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
import json

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False
    import urllib.request
    import urllib.error

from .exceptions import (
    BudgetExceededError,
    RateLimitExceededError,
    PolicyViolationError,
    TracingError,
)

# Type variable for generic return types
T = TypeVar('T')

# Global configuration
_config: Dict[str, Any] = {}

BASE_URL = "https://bgwyprqxtdreuutzpbgw.supabase.co"
VERSION = "7.6.11"


@dataclass
class TracingOptions:
    """Configuration options for tracing context."""
    api_key: Optional[str] = None
    customer_id: Optional[str] = None
    daily_budget: Optional[float] = None
    monthly_budget: Optional[float] = None
    agent_id: Optional[str] = None
    base_url: str = BASE_URL
    debug: bool = False
    model: str = "gpt-4"
    estimated_tokens: int = 1000


@dataclass
class TracingContext:
    """Tracing context that holds state during AI operations."""
    options: TracingOptions
    trace_id: str = ""
    span_id: str = ""
    parent_span_id: Optional[str] = None
    request_id: Optional[str] = None
    start_time: float = 0.0
    validation_result: Dict[str, Any] = field(default_factory=dict)
    spans: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_span(
        self,
        name: str,
        attributes: Dict[str, Any],
        start_time_ns: int,
        end_time_ns: int,
        status: int = 0
    ) -> None:
        """Add a span to the trace."""
        span = {
            "trace_id": self.trace_id,
            "span_id": _generate_hex_id(8),
            "parent_span_id": self.span_id,
            "name": name,
            "attributes": attributes,
            "start_time_unix_nano": start_time_ns,
            "end_time_unix_nano": end_time_ns,
            "status": {"code": status}
        }
        self.spans.append(span)
    
    def cache_response(
        self,
        model: str,
        messages: Any,
        response_content: str,
        input_tokens: int,
        output_tokens: int
    ) -> None:
        """Cache an AI response for semantic caching."""
        prompt_hash = _hash_prompt(messages)
        url = f"{self.options.base_url}/functions/v1/cache-ai-response"
        
        payload = {
            "api_key": self.options.api_key,
            "prompt_hash": prompt_hash,
            "response_content": response_content,
            "model": model,
            "prompt_content": messages if isinstance(messages, str) else json.dumps(messages),
            "tokens_used": input_tokens + output_tokens,
            "cacheable": True,
            "ttl_hours": 24,
            "customer_id": self.options.customer_id,
            "request_id": self.request_id
        }
        
        try:
            _http_post(url, payload, timeout=5.0)
            _log(self.options.debug, "✓ Cached response")
        except Exception as e:
            _log(self.options.debug, f"⚠️ Cache error (non-blocking): {e}")


def _generate_hex_id(num_bytes: int) -> str:
    """Generate a random hex ID."""
    return secrets.token_hex(num_bytes)


def _hash_prompt(messages: Any) -> str:
    """Hash prompt content for caching."""
    content = messages if isinstance(messages, str) else json.dumps(messages, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()


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
                return {"status_code": response.status_code, "body": response.text}
            return {"status_code": response.status_code, "body": response.json() if response.text else {}}
    else:
        # Fallback to urllib
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=all_headers, method='POST')
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                body = response.read().decode('utf-8')
                return {"status_code": response.status, "body": json.loads(body) if body else {}}
        except urllib.error.HTTPError as e:
            return {"status_code": e.code, "body": e.read().decode('utf-8')}


def _validate_budget(options: TracingOptions) -> Dict[str, Any]:
    """Pre-validate request against Cost Guard policies."""
    url = f"{options.base_url}/functions/v1/ai-cost-guard-router"
    
    payload = {
        "api_key": options.api_key,
        "customer_id": options.customer_id,
        "model": options.model,
        "messages": [],
        "estimated_tokens": options.estimated_tokens
    }
    
    if options.daily_budget is not None:
        payload["daily_budget_override"] = options.daily_budget
    if options.monthly_budget is not None:
        payload["monthly_budget_override"] = options.monthly_budget
    if options.agent_id:
        payload["agent_id"] = options.agent_id
    
    try:
        result = _http_post(url, payload, timeout=10.0)
        status_code = result.get("status_code", 500)
        body = result.get("body", {})
        
        if status_code >= 500:
            _log(options.debug, "⚠️ Router server error (failing open)")
            return {"allowed": True, "reason": "Router server error (failed open)"}
        
        if status_code >= 400:
            _log(options.debug, f"❌ Router rejected: {body}")
            return {"allowed": False, "reason": str(body)}
        
        if isinstance(body, dict):
            if options.debug:
                if body.get("allowed"):
                    _log(options.debug, "✓ Budget validation passed")
                else:
                    _log(options.debug, f"❌ Budget validation failed: {body.get('reason')}")
            return body
        
        return {"allowed": True, "reason": "Unknown response format"}
        
    except Exception as e:
        _log(options.debug, f"⚠️ Router network error: {e} (failing open)")
        return {"allowed": True, "reason": "Router network error (failed open)"}


def _export_spans(ctx: TracingContext) -> None:
    """Export spans to OTEL collector."""
    if not ctx.spans:
        return
    
    url = f"{ctx.options.base_url}/functions/v1/otel-collector"
    
    # Build OTLP-compliant payload
    resource_attributes = [
        {"key": "service.name", "value": {"stringValue": "agentbill-langchain-sdk"}},
        {"key": "service.version", "value": {"stringValue": VERSION}},
    ]
    
    if ctx.options.customer_id:
        resource_attributes.append({
            "key": "customer.id",
            "value": {"stringValue": ctx.options.customer_id}
        })
    if ctx.options.agent_id:
        resource_attributes.append({
            "key": "agent.id",
            "value": {"stringValue": ctx.options.agent_id}
        })
    
    otlp_spans = []
    for span in ctx.spans:
        attrs = span.get("attributes", {})
        attr_list = []
        for k, v in attrs.items():
            if v is not None:
                if isinstance(v, str):
                    attr_list.append({"key": k, "value": {"stringValue": v}})
                elif isinstance(v, (int, float)):
                    attr_list.append({"key": k, "value": {"doubleValue": v}})
                else:
                    attr_list.append({"key": k, "value": {"stringValue": str(v)}})
        
        otlp_span = {
            "traceId": span["trace_id"],
            "spanId": span["span_id"],
            "name": span["name"],
            "kind": 1,
            "startTimeUnixNano": str(span["start_time_unix_nano"]),
            "endTimeUnixNano": str(span["end_time_unix_nano"]),
            "attributes": attr_list,
            "status": span["status"]
        }
        
        if span.get("parent_span_id"):
            otlp_span["parentSpanId"] = span["parent_span_id"]
        
        otlp_spans.append(otlp_span)
    
    payload = {
        "resourceSpans": [{
            "resource": {"attributes": resource_attributes},
            "scopeSpans": [{
                "scope": {"name": "agentbill", "version": VERSION},
                "spans": otlp_spans
            }]
        }]
    }
    
    headers = {"X-API-Key": ctx.options.api_key or ""}
    
    try:
        result = _http_post(url, payload, timeout=10.0, headers=headers)
        if ctx.options.debug:
            if result.get("status_code") == 200:
                _log(ctx.options.debug, f"✓ Exported {len(ctx.spans)} spans to otel-collector")
            else:
                _log(ctx.options.debug, f"⚠️ Span export failed: {result.get('status_code')}")
    except Exception as e:
        _log(ctx.options.debug, f"⚠️ Span export error: {e}")


# Thread-local storage for distributed tracing context
import threading
_trace_context = threading.local()


def get_trace_context() -> Optional[Dict[str, str]]:
    """Get the current trace context."""
    return getattr(_trace_context, 'context', None)


def set_trace_context(trace_id: str, span_id: str, parent_span_id: Optional[str] = None) -> None:
    """Set the current trace context."""
    _trace_context.context = {
        "trace_id": trace_id,
        "span_id": span_id,
        "parent_span_id": parent_span_id
    }


def clear_trace_context() -> None:
    """Clear the current trace context."""
    _trace_context.context = None


@asynccontextmanager
async def agentbill_tracing(
    api_key: Optional[str] = None,
    customer_id: Optional[str] = None,
    daily_budget: Optional[float] = None,
    monthly_budget: Optional[float] = None,
    agent_id: Optional[str] = None,
    base_url: str = BASE_URL,
    debug: bool = False,
    model: str = "gpt-4",
    estimated_tokens: int = 1000
) -> AsyncGenerator[TracingContext, None]:
    """
    Async context manager for tracking AI operations with Cost Guard protection.
    
    CRITICAL: This validates against ai-cost-guard-router BEFORE allowing AI calls.
    If validation fails, BudgetExceededError is raised BEFORE any AI call is made.
    
    Example:
        async with agentbill_tracing(
            customer_id="cust_123",
            daily_budget=5.00
        ) as ctx:
            # Make AI calls - they will be tracked
            response = await client.chat.completions.create(...)
    
    Args:
        api_key: AgentBill API key (or set AGENTBILL_API_KEY env var)
        customer_id: Customer identifier for billing
        daily_budget: Maximum daily spend limit
        monthly_budget: Maximum monthly spend limit
        agent_id: Agent identifier for tracking
        base_url: API base URL (default: production)
        debug: Enable debug logging
        model: Model name for cost estimation
        estimated_tokens: Estimated tokens for pre-validation
    
    Raises:
        BudgetExceededError: If daily/monthly budget would be exceeded
        RateLimitExceededError: If rate limits would be exceeded
        PolicyViolationError: If other policy constraints are violated
    """
    # Get API key from env if not provided
    resolved_api_key = api_key or os.environ.get("AGENTBILL_API_KEY")
    if not resolved_api_key:
        raise ValueError("api_key is required. Provide it or set AGENTBILL_API_KEY env var.")
    
    options = TracingOptions(
        api_key=resolved_api_key,
        customer_id=customer_id,
        daily_budget=daily_budget,
        monthly_budget=monthly_budget,
        agent_id=agent_id,
        base_url=base_url,
        debug=debug,
        model=model,
        estimated_tokens=estimated_tokens
    )
    
    ctx = TracingContext(options=options)
    
    # Generate trace/span IDs
    existing = get_trace_context()
    if existing and existing.get("trace_id"):
        ctx.trace_id = existing["trace_id"]
        ctx.parent_span_id = existing.get("span_id")
    else:
        ctx.trace_id = _generate_hex_id(16)
        ctx.parent_span_id = None
    
    ctx.span_id = _generate_hex_id(8)
    set_trace_context(ctx.trace_id, ctx.span_id, ctx.parent_span_id)
    
    ctx.start_time = time.time()
    
    # CRITICAL: Pre-validate with Cost Guard
    ctx.validation_result = _validate_budget(options)
    
    # CRITICAL: Throw exception if not allowed
    if not ctx.validation_result.get("allowed", False):
        reason = ctx.validation_result.get("reason", "Request blocked by Cost Guard")
        reason_lower = reason.lower()
        
        if "budget" in reason_lower:
            raise BudgetExceededError(reason, ctx.validation_result)
        elif "rate" in reason_lower:
            raise RateLimitExceededError(reason, ctx.validation_result)
        else:
            raise PolicyViolationError(reason, ctx.validation_result)
    
    ctx.request_id = ctx.validation_result.get("request_id")
    
    error = None
    try:
        yield ctx
    except Exception as e:
        error = e
        raise
    finally:
        end_time = time.time()
        
        # Add root span
        attrs = {
            "customer_id": customer_id,
            "agent_id": agent_id,
            "request_id": ctx.request_id
        }
        if error:
            attrs["error"] = str(error)
        
        ctx.add_span(
            "agentbill_tracing",
            attrs,
            int(ctx.start_time * 1_000_000_000),
            int(end_time * 1_000_000_000),
            1 if error else 0
        )
        
        # Export spans
        _export_spans(ctx)
        
        # Clear context
        clear_trace_context()


@contextmanager
def agentbill_tracing_sync(
    api_key: Optional[str] = None,
    customer_id: Optional[str] = None,
    daily_budget: Optional[float] = None,
    monthly_budget: Optional[float] = None,
    agent_id: Optional[str] = None,
    base_url: str = BASE_URL,
    debug: bool = False,
    model: str = "gpt-4",
    estimated_tokens: int = 1000
):
    """
    Synchronous context manager for tracking AI operations with Cost Guard protection.
    
    Same as agentbill_tracing but for synchronous code.
    """
    # Get API key from env if not provided
    resolved_api_key = api_key or os.environ.get("AGENTBILL_API_KEY")
    if not resolved_api_key:
        raise ValueError("api_key is required. Provide it or set AGENTBILL_API_KEY env var.")
    
    options = TracingOptions(
        api_key=resolved_api_key,
        customer_id=customer_id,
        daily_budget=daily_budget,
        monthly_budget=monthly_budget,
        agent_id=agent_id,
        base_url=base_url,
        debug=debug,
        model=model,
        estimated_tokens=estimated_tokens
    )
    
    ctx = TracingContext(options=options)
    
    # Generate trace/span IDs
    existing = get_trace_context()
    if existing and existing.get("trace_id"):
        ctx.trace_id = existing["trace_id"]
        ctx.parent_span_id = existing.get("span_id")
    else:
        ctx.trace_id = _generate_hex_id(16)
        ctx.parent_span_id = None
    
    ctx.span_id = _generate_hex_id(8)
    set_trace_context(ctx.trace_id, ctx.span_id, ctx.parent_span_id)
    
    ctx.start_time = time.time()
    
    # CRITICAL: Pre-validate with Cost Guard
    ctx.validation_result = _validate_budget(options)
    
    # CRITICAL: Throw exception if not allowed
    if not ctx.validation_result.get("allowed", False):
        reason = ctx.validation_result.get("reason", "Request blocked by Cost Guard")
        reason_lower = reason.lower()
        
        if "budget" in reason_lower:
            raise BudgetExceededError(reason, ctx.validation_result)
        elif "rate" in reason_lower:
            raise RateLimitExceededError(reason, ctx.validation_result)
        else:
            raise PolicyViolationError(reason, ctx.validation_result)
    
    ctx.request_id = ctx.validation_result.get("request_id")
    
    error = None
    try:
        yield ctx
    except Exception as e:
        error = e
        raise
    finally:
        end_time = time.time()
        
        # Add root span
        attrs = {
            "customer_id": customer_id,
            "agent_id": agent_id,
            "request_id": ctx.request_id
        }
        if error:
            attrs["error"] = str(error)
        
        ctx.add_span(
            "agentbill_tracing",
            attrs,
            int(ctx.start_time * 1_000_000_000),
            int(end_time * 1_000_000_000),
            1 if error else 0
        )
        
        # Export spans
        _export_spans(ctx)
        
        # Clear context
        clear_trace_context()


def agentbill_traced(
    func: Optional[Callable[..., T]] = None,
    *,
    api_key: Optional[str] = None,
    customer_id: Optional[str] = None,
    daily_budget: Optional[float] = None,
    monthly_budget: Optional[float] = None,
    agent_id: Optional[str] = None,
    debug: bool = False
) -> Callable[..., T]:
    """
    Decorator for wrapping functions with Cost Guard protection.
    
    Example:
        @agentbill_traced(customer_id="cust_123", daily_budget=5.00)
        def generate_response(prompt: str):
            return client.chat.completions.create(...)
    """
    import functools
    import asyncio
    
    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(fn)
        def sync_wrapper(*args, **kwargs) -> T:
            with agentbill_tracing_sync(
                api_key=api_key,
                customer_id=customer_id,
                daily_budget=daily_budget,
                monthly_budget=monthly_budget,
                agent_id=agent_id,
                debug=debug
            ):
                return fn(*args, **kwargs)
        
        @functools.wraps(fn)
        async def async_wrapper(*args, **kwargs) -> T:
            async with agentbill_tracing(
                api_key=api_key,
                customer_id=customer_id,
                daily_budget=daily_budget,
                monthly_budget=monthly_budget,
                agent_id=agent_id,
                debug=debug
            ):
                return await fn(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(fn):
            return async_wrapper
        return sync_wrapper
    
    if func is not None:
        return decorator(func)
    return decorator


__all__ = [
    "agentbill_tracing",
    "agentbill_tracing_sync",
    "agentbill_traced",
    "TracingContext",
    "TracingOptions",
    "get_trace_context",
    "set_trace_context",
    "clear_trace_context",
]
