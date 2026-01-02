"""AgentBill CrewAI Signals - v7.6.11

Full standalone implementation of business signal tracking for revenue attribution.
Links CrewAI agent interactions to business outcomes.
"""

import os
import time
import uuid
import json
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime


# Version
VERSION = "7.6.11"

# Default endpoints
DEFAULT_SIGNAL_URL = "https://api.agentbill.dev/v1/otel-collector"


# Global configuration
_global_config: Dict[str, Any] = {}


def set_signal_config(config: Dict[str, Any]) -> None:
    """Set global signal configuration."""
    global _global_config
    _global_config.update(config)


def get_signal_config() -> Dict[str, Any]:
    """Get current global signal configuration."""
    return _global_config.copy()


@dataclass
class SignalResult:
    """Result of a signal emission."""
    success: bool
    signal_id: str
    trace_id: Optional[str]
    span_id: Optional[str]
    timestamp: str
    error: Optional[str] = None


def _generate_id() -> str:
    """Generate a unique identifier."""
    return uuid.uuid4().hex


def _http_post(url: str, data: Dict[str, Any], api_key: str, timeout: float = 30.0) -> Dict[str, Any]:
    """Make HTTP POST request."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "User-Agent": f"agentbill-crewai-sdk/{VERSION}",
        "X-AgentBill-SDK": "crewai",
        "X-AgentBill-Version": VERSION,
    }
    
    body = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else str(e)
        return {"success": False, "error": f"HTTP {e.code}: {error_body}"}
    except urllib.error.URLError as e:
        return {"success": False, "error": f"Network error: {e.reason}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def signal(
    event_name: str,
    *,
    revenue: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None,
    customer_id: Optional[str] = None,
    session_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    span_id: Optional[str] = None,
    parent_span_id: Optional[str] = None,
    currency: str = "USD",
    event_type: Optional[str] = None,
    event_value: Optional[float] = None,
    api_key: Optional[str] = None,
) -> SignalResult:
    """
    Emit a business signal for revenue attribution.
    
    Links CrewAI agent interactions to business outcomes like purchases,
    signups, conversions, etc.
    
    Example:
        # Track a purchase after AI-assisted checkout
        signal(
            "purchase_completed",
            revenue=99.99,
            customer_id="cust-123",
            metadata={"product_id": "prod-456", "agent": "sales-agent"}
        )
    
    Args:
        event_name: Name of the business event (e.g., "purchase", "signup")
        revenue: Revenue amount in the specified currency
        metadata: Additional event metadata
        customer_id: Customer identifier (required for billing attribution)
        session_id: Session identifier for grouping events
        trace_id: Trace ID to link to (auto-detected if in tracing context)
        span_id: Span ID to link to
        parent_span_id: Parent span ID
        currency: Currency code (default: USD)
        event_type: Type of conversion event
        event_value: Numeric value of the event
        api_key: AgentBill API key (or set AGENTBILL_API_KEY env var)
    
    Returns:
        SignalResult with success status and identifiers
    """
    # Get configuration
    config = get_signal_config()
    
    # Resolve API key
    resolved_api_key = api_key or config.get("api_key") or os.environ.get("AGENTBILL_API_KEY")
    if not resolved_api_key:
        return SignalResult(
            success=False,
            signal_id="",
            trace_id=None,
            span_id=None,
            timestamp=datetime.utcnow().isoformat() + "Z",
            error="API key required. Set AGENTBILL_API_KEY or pass api_key parameter.",
        )
    
    # Resolve customer_id
    resolved_customer_id = customer_id or config.get("customer_id")
    if not resolved_customer_id:
        return SignalResult(
            success=False,
            signal_id="",
            trace_id=None,
            span_id=None,
            timestamp=datetime.utcnow().isoformat() + "Z",
            error="customer_id is required",
        )
    
    # Generate IDs
    signal_id = _generate_id()
    resolved_trace_id = trace_id or config.get("trace_id") or _generate_id()
    resolved_span_id = span_id or config.get("span_id") or _generate_id()[:16]
    resolved_session_id = session_id or config.get("session_id") or _generate_id()
    
    # Build timestamp
    now_ns = time.time_ns()
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    # Build attributes
    attributes: List[Dict[str, Any]] = [
        {"key": "event.name", "value": {"stringValue": event_name}},
        {"key": "event.domain", "value": {"stringValue": "business"}},
        {"key": "customer.id", "value": {"stringValue": resolved_customer_id}},
        {"key": "session.id", "value": {"stringValue": resolved_session_id}},
        {"key": "signal.id", "value": {"stringValue": signal_id}},
        {"key": "sdk", "value": {"stringValue": "crewai"}},
        {"key": "sdk.version", "value": {"stringValue": VERSION}},
    ]
    
    if revenue is not None:
        attributes.append({"key": "revenue", "value": {"doubleValue": revenue}})
        attributes.append({"key": "currency", "value": {"stringValue": currency}})
    
    if event_type:
        attributes.append({"key": "event.type", "value": {"stringValue": event_type}})
    
    if event_value is not None:
        attributes.append({"key": "event.value", "value": {"doubleValue": event_value}})
    
    # Add metadata as attributes
    if metadata:
        for key, value in metadata.items():
            attr_key = f"metadata.{key}"
            if isinstance(value, bool):
                attributes.append({"key": attr_key, "value": {"boolValue": value}})
            elif isinstance(value, int):
                attributes.append({"key": attr_key, "value": {"intValue": str(value)}})
            elif isinstance(value, float):
                attributes.append({"key": attr_key, "value": {"doubleValue": value}})
            else:
                attributes.append({"key": attr_key, "value": {"stringValue": str(value)}})
    
    # Build OTLP payload
    payload = {
        "resourceSpans": [{
            "resource": {
                "attributes": [
                    {"key": "service.name", "value": {"stringValue": "agentbill-crewai-signals"}},
                    {"key": "service.version", "value": {"stringValue": VERSION}},
                    {"key": "customer.id", "value": {"stringValue": resolved_customer_id}},
                ]
            },
            "scopeSpans": [{
                "scope": {
                    "name": "agentbill-crewai-signals",
                    "version": VERSION,
                },
                "spans": [{
                    "traceId": resolved_trace_id,
                    "spanId": resolved_span_id,
                    "parentSpanId": parent_span_id or "",
                    "name": f"signal.{event_name}",
                    "kind": 1,  # SPAN_KIND_INTERNAL
                    "startTimeUnixNano": str(now_ns),
                    "endTimeUnixNano": str(now_ns),
                    "attributes": attributes,
                    "status": {"code": 1, "message": ""},  # OK
                }],
            }],
        }],
    }
    
    # Get endpoint
    signal_url = config.get("signal_url") or os.environ.get(
        "AGENTBILL_SIGNAL_URL", DEFAULT_SIGNAL_URL
    )
    
    # Send signal
    result = _http_post(signal_url, payload, resolved_api_key)
    
    if result.get("success", True) and not result.get("error"):
        return SignalResult(
            success=True,
            signal_id=signal_id,
            trace_id=resolved_trace_id,
            span_id=resolved_span_id,
            timestamp=timestamp,
        )
    else:
        return SignalResult(
            success=False,
            signal_id=signal_id,
            trace_id=resolved_trace_id,
            span_id=resolved_span_id,
            timestamp=timestamp,
            error=result.get("error", "Unknown error"),
        )


def track_conversion(
    event_type: str,
    event_value: float,
    *,
    currency: str = "USD",
    customer_id: Optional[str] = None,
    session_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    api_key: Optional[str] = None,
) -> SignalResult:
    """
    Convenience function to track conversion events.
    
    Example:
        track_conversion(
            event_type="purchase",
            event_value=149.99,
            customer_id="cust-123",
            metadata={"order_id": "ord-789"}
        )
    
    Args:
        event_type: Type of conversion (purchase, signup, etc.)
        event_value: Monetary or numeric value of conversion
        currency: Currency code (default: USD)
        customer_id: Customer identifier
        session_id: Session identifier
        metadata: Additional metadata
        api_key: AgentBill API key
    
    Returns:
        SignalResult with success status
    """
    return signal(
        event_name=f"conversion.{event_type}",
        revenue=event_value,
        event_type=event_type,
        event_value=event_value,
        currency=currency,
        customer_id=customer_id,
        session_id=session_id,
        metadata=metadata,
        api_key=api_key,
    )


__all__ = [
    "signal",
    "track_conversion",
    "set_signal_config",
    "get_signal_config",
    "SignalResult",
    "VERSION",
]
