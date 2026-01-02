"""AgentBill CrewAI Tracing - v7.6.11

Full standalone implementation of OpenTelemetry tracing with Cost Guard validation.
Designed specifically for CrewAI agent orchestration.
"""

import os
import time
import uuid
import json
import hashlib
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, Callable, TypeVar, List
from contextlib import contextmanager
from functools import wraps
from dataclasses import dataclass, field
from datetime import datetime

from .exceptions import (
    BudgetExceededError,
    RateLimitExceededError,
    PolicyViolationError,
    ValidationError,
    TracingError,
)


# Type variable for generic function wrapping
F = TypeVar('F', bound=Callable[..., Any])

# Version
VERSION = "7.6.11"

# Default endpoints
DEFAULT_COST_GUARD_URL = "https://api.agentbill.dev/v1/ai-cost-guard-router"
DEFAULT_OTEL_COLLECTOR_URL = "https://api.agentbill.dev/v1/otel-collector"


@dataclass
class Span:
    """Represents an OpenTelemetry span."""
    name: str
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    start_time_ns: int
    end_time_ns: Optional[int] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    status: int = 0  # 0=UNSET, 1=OK, 2=ERROR
    status_message: str = ""
    
    def set_attributes(self, attrs: Dict[str, Any]) -> None:
        """Add attributes to the span."""
        self.attributes.update(attrs)
    
    def set_status(self, status: int, message: str = "") -> None:
        """Set span status."""
        self.status = status
        self.status_message = message
    
    def end(self) -> None:
        """End the span."""
        if self.end_time_ns is None:
            self.end_time_ns = time.time_ns()


@dataclass
class TracingOptions:
    """Configuration options for tracing."""
    customer_id: str
    api_key: Optional[str] = None
    agent_id: Optional[str] = None
    daily_budget: Optional[float] = None
    monthly_budget: Optional[float] = None
    model: Optional[str] = None
    provider: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    enable_caching: bool = True
    cost_guard_url: Optional[str] = None
    otel_collector_url: Optional[str] = None
    timeout_seconds: float = 30.0


class TracingContext:
    """
    Full CrewAI tracing context with Cost Guard validation.
    
    This class manages the complete tracing lifecycle:
    1. Pre-validates requests against Cost Guard before AI calls
    2. Tracks spans with OpenTelemetry-compliant format
    3. Exports spans to the OTEL collector on exit
    4. Raises appropriate exceptions when budget/rate limits are exceeded
    
    Example:
        with TracingContext(TracingOptions(customer_id="cust-123", daily_budget=10.0)) as ctx:
            # Your CrewAI agent code here
            crew = Crew(agents=[...], tasks=[...])
            result = crew.kickoff()
    """
    
    def __init__(self, options: TracingOptions):
        self.options = options
        self.api_key = options.api_key or os.environ.get("AGENTBILL_API_KEY")
        
        if not self.api_key:
            raise ValidationError("API key required. Set AGENTBILL_API_KEY or pass api_key option.", "api_key")
        
        self.customer_id = options.customer_id
        self.agent_id = options.agent_id
        self.daily_budget = options.daily_budget
        self.monthly_budget = options.monthly_budget
        self.model = options.model
        self.provider = options.provider
        self.session_id = options.session_id or str(uuid.uuid4())
        self.metadata = options.metadata or {}
        self.enable_caching = options.enable_caching
        
        self.cost_guard_url = options.cost_guard_url or os.environ.get(
            "AGENTBILL_COST_GUARD_URL", DEFAULT_COST_GUARD_URL
        )
        self.otel_collector_url = options.otel_collector_url or os.environ.get(
            "AGENTBILL_OTEL_COLLECTOR_URL", DEFAULT_OTEL_COLLECTOR_URL
        )
        self.timeout = options.timeout_seconds
        
        # Generate trace/span IDs
        self.trace_id = self._generate_trace_id()
        self.span_id = self._generate_span_id()
        self.parent_span_id: Optional[str] = None
        
        # Timing
        self.start_time_ns: Optional[int] = None
        self.end_time_ns: Optional[int] = None
        
        # Span collection
        self.spans: List[Span] = []
        
        # Validation result
        self.validation_result: Optional[Dict[str, Any]] = None
        
        # Accumulated usage
        self.total_tokens = 0
        self.total_cost = 0.0
        self.request_count = 0
    
    def _generate_trace_id(self) -> str:
        """Generate a 32-character hex trace ID."""
        return uuid.uuid4().hex
    
    def _generate_span_id(self) -> str:
        """Generate a 16-character hex span ID."""
        return uuid.uuid4().hex[:16]
    
    def _compute_prompt_hash(self, prompt: Any) -> str:
        """Compute SHA-256 hash of prompt for caching."""
        if isinstance(prompt, str):
            content = prompt
        else:
            content = json.dumps(prompt, separators=(',', ':'))
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _http_request(self, url: str, data: Dict[str, Any], method: str = "POST") -> Dict[str, Any]:
        """Make HTTP request with proper headers."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": f"agentbill-crewai-sdk/{VERSION}",
            "X-AgentBill-SDK": "crewai",
            "X-AgentBill-Version": VERSION,
        }
        
        body = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else str(e)
            raise TracingError(f"HTTP {e.code}: {error_body}", {"url": url, "status": e.code})
        except urllib.error.URLError as e:
            raise TracingError(f"Network error: {e.reason}", {"url": url})
        except Exception as e:
            raise TracingError(f"Request failed: {str(e)}", {"url": url})
    
    def validate_budget(self) -> Dict[str, Any]:
        """
        Pre-validate request against Cost Guard.
        
        CRITICAL: This MUST be called before any AI operation.
        If validation.allowed is False, raises appropriate exception.
        """
        payload = {
            "customer_id": self.customer_id,
            "action": "validate",
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "session_id": self.session_id,
            "sdk": "crewai",
            "sdk_version": VERSION,
        }
        
        if self.agent_id:
            payload["agent_id"] = self.agent_id
        if self.daily_budget is not None:
            payload["daily_budget"] = self.daily_budget
        if self.monthly_budget is not None:
            payload["monthly_budget"] = self.monthly_budget
        if self.model:
            payload["model"] = self.model
        if self.provider:
            payload["provider"] = self.provider
        if self.metadata:
            payload["metadata"] = self.metadata
        
        result = self._http_request(self.cost_guard_url, payload)
        self.validation_result = result
        
        # CRITICAL: Check if request is allowed
        if not result.get("allowed", True):
            reason = result.get("reason", "Budget limit exceeded")
            code = result.get("code", "BUDGET_EXCEEDED")
            details = {
                "customer_id": self.customer_id,
                "daily_budget": self.daily_budget,
                "monthly_budget": self.monthly_budget,
                "current_usage": result.get("current_usage"),
                "trace_id": self.trace_id,
            }
            
            if code == "RATE_LIMIT_EXCEEDED":
                raise RateLimitExceededError(reason, details)
            elif code == "POLICY_VIOLATION":
                raise PolicyViolationError(reason, details)
            else:
                raise BudgetExceededError(reason, details)
        
        return result
    
    def create_span(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
        parent_span_id: Optional[str] = None
    ) -> Span:
        """Create a new span."""
        span = Span(
            name=name,
            trace_id=self.trace_id,
            span_id=self._generate_span_id(),
            parent_span_id=parent_span_id or self.span_id,
            start_time_ns=time.time_ns(),
            attributes=attributes or {},
        )
        self.spans.append(span)
        return span
    
    def add_span(
        self,
        name: str,
        attributes: Dict[str, Any],
        start_time_ns: int,
        end_time_ns: int,
        status: int = 0
    ) -> Span:
        """Add a completed span."""
        span = Span(
            name=name,
            trace_id=self.trace_id,
            span_id=self._generate_span_id(),
            parent_span_id=self.span_id,
            start_time_ns=start_time_ns,
            end_time_ns=end_time_ns,
            attributes=attributes,
            status=status,
        )
        self.spans.append(span)
        return span
    
    def record_usage(
        self,
        tokens: int = 0,
        cost: float = 0.0,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
    ) -> None:
        """Record AI usage for this context."""
        self.total_tokens += tokens
        self.total_cost += cost
        self.request_count += 1
        
        # Update model/provider if provided
        if model:
            self.model = model
        if provider:
            self.provider = provider
    
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
        
        Call this after receiving an AI response to populate the semantic cache
        for future cache hits on similar prompts.
        
        Args:
            model: The AI model used (e.g., "gpt-4", "claude-3-opus")
            messages: The prompt messages sent to the AI
            response_content: The AI's response text
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens used
        
        Example:
            with agentbill_tracing(customer_id="cust-123") as ctx:
                response = crew.kickoff()
                ctx.cache_response(
                    model="gpt-4",
                    messages=[{"role": "user", "content": "Hello!"}],
                    response_content=response.raw,
                    input_tokens=100,
                    output_tokens=50
                )
        """
        prompt_hash = self._compute_prompt_hash(messages)
        cache_url = os.environ.get(
            "AGENTBILL_CACHE_URL",
            "https://api.agentbill.dev/v1/cache-ai-response"
        )
        
        payload = {
            "api_key": self.api_key,
            "prompt_hash": prompt_hash,
            "response_content": response_content,
            "model": model,
            "prompt_content": messages if isinstance(messages, str) else json.dumps(messages),
            "tokens_used": input_tokens + output_tokens,
            "cacheable": True,
            "ttl_hours": 24,
            "customer_id": self.customer_id,
            "trace_id": self.trace_id,
        }
        
        if self.session_id:
            payload["session_id"] = self.session_id
        
        try:
            self._http_request(cache_url, payload)
        except Exception:
            # Cache errors are non-blocking
            pass
    
    def check_cache(
        self,
        model: str,
        messages: Any,
    ) -> Optional[Dict[str, Any]]:
        """
        Check if a cached response exists for the given prompt.
        
        This is automatically called during budget validation, but can be
        called manually for explicit cache lookups.
        
        Args:
            model: The AI model to check cache for
            messages: The prompt messages to check
        
        Returns:
            Cached response data if found, None otherwise
        """
        if self.validation_result and self.validation_result.get("cached"):
            return self.validation_result.get("response_data")
        return None
    
    def _build_otlp_payload(self) -> Dict[str, Any]:
        """Build OTLP-compliant payload for span export."""
        resource_attributes = [
            {"key": "service.name", "value": {"stringValue": "agentbill-crewai"}},
            {"key": "service.version", "value": {"stringValue": VERSION}},
            {"key": "customer.id", "value": {"stringValue": self.customer_id}},
        ]
        
        if self.agent_id:
            resource_attributes.append({
                "key": "agent.id",
                "value": {"stringValue": self.agent_id}
            })
        
        return {
            "resourceSpans": [{
                "resource": {"attributes": resource_attributes},
                "scopeSpans": [{
                    "scope": {
                        "name": "agentbill-crewai-sdk",
                        "version": VERSION,
                    },
                    "spans": [self._span_to_otlp(span) for span in self.spans],
                }],
            }],
        }
    
    def _span_to_otlp(self, span: Span) -> Dict[str, Any]:
        """Convert internal span to OTLP format."""
        otlp_span = {
            "traceId": span.trace_id,
            "spanId": span.span_id,
            "name": span.name,
            "kind": 1,  # SPAN_KIND_INTERNAL
            "startTimeUnixNano": str(span.start_time_ns),
            "endTimeUnixNano": str(span.end_time_ns or time.time_ns()),
            "attributes": [
                self._attr_to_otlp(k, v)
                for k, v in span.attributes.items()
            ],
            "status": {
                "code": span.status,
                "message": span.status_message,
            },
        }
        
        if span.parent_span_id:
            otlp_span["parentSpanId"] = span.parent_span_id
        
        return otlp_span
    
    def _attr_to_otlp(self, key: str, value: Any) -> Dict[str, Any]:
        """Convert attribute to OTLP format."""
        if isinstance(value, bool):
            return {"key": key, "value": {"boolValue": value}}
        elif isinstance(value, int):
            return {"key": key, "value": {"intValue": str(value)}}
        elif isinstance(value, float):
            return {"key": key, "value": {"doubleValue": value}}
        elif isinstance(value, (list, tuple)):
            return {"key": key, "value": {"arrayValue": {"values": [
                self._value_to_otlp(v) for v in value
            ]}}}
        else:
            return {"key": key, "value": {"stringValue": str(value)}}
    
    def _value_to_otlp(self, value: Any) -> Dict[str, Any]:
        """Convert value to OTLP format."""
        if isinstance(value, bool):
            return {"boolValue": value}
        elif isinstance(value, int):
            return {"intValue": str(value)}
        elif isinstance(value, float):
            return {"doubleValue": value}
        else:
            return {"stringValue": str(value)}
    
    def export_spans(self) -> None:
        """Export all collected spans to OTEL collector."""
        if not self.spans:
            return
        
        payload = self._build_otlp_payload()
        
        try:
            self._http_request(self.otel_collector_url, payload)
        except TracingError:
            # Log but don't fail on export errors
            pass
    
    def __enter__(self) -> "TracingContext":
        """Enter tracing context - validates budget first."""
        self.start_time_ns = time.time_ns()
        
        # CRITICAL: Pre-validate before any AI calls
        self.validate_budget()
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit tracing context - exports spans."""
        self.end_time_ns = time.time_ns()
        
        # Create root span
        status = 2 if exc_type else 1  # ERROR if exception, OK otherwise
        root_span = Span(
            name="crewai.trace",
            trace_id=self.trace_id,
            span_id=self.span_id,
            parent_span_id=None,
            start_time_ns=self.start_time_ns,
            end_time_ns=self.end_time_ns,
            attributes={
                "customer.id": self.customer_id,
                "session.id": self.session_id,
                "total_tokens": self.total_tokens,
                "total_cost": self.total_cost,
                "request_count": self.request_count,
                "sdk": "crewai",
                "sdk.version": VERSION,
            },
            status=status,
            status_message=str(exc_val) if exc_val else "",
        )
        
        if self.agent_id:
            root_span.attributes["agent.id"] = self.agent_id
        if self.model:
            root_span.attributes["model"] = self.model
        if self.provider:
            root_span.attributes["provider"] = self.provider
        
        self.spans.insert(0, root_span)
        
        # Export all spans
        self.export_spans()


@contextmanager
def agentbill_tracing(
    customer_id: str,
    *,
    api_key: Optional[str] = None,
    agent_id: Optional[str] = None,
    daily_budget: Optional[float] = None,
    monthly_budget: Optional[float] = None,
    model: Optional[str] = None,
    provider: Optional[str] = None,
    session_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    enable_caching: bool = True,
):
    """
    Context manager for CrewAI tracing with Cost Guard protection.
    
    CRITICAL: This validates budget BEFORE allowing any AI operations.
    If budget is exceeded, BudgetExceededError is raised immediately.
    
    Example:
        with agentbill_tracing(customer_id="cust-123", daily_budget=10.0) as ctx:
            crew = Crew(agents=[agent], tasks=[task])
            result = crew.kickoff()
    
    Args:
        customer_id: Required customer identifier for billing
        api_key: AgentBill API key (or set AGENTBILL_API_KEY env var)
        agent_id: Optional agent identifier
        daily_budget: Daily spending limit in USD
        monthly_budget: Monthly spending limit in USD
        model: AI model being used
        provider: AI provider (openai, anthropic, etc.)
        session_id: Session identifier for grouping traces
        metadata: Additional metadata to attach to traces
        enable_caching: Whether to enable response caching
    
    Raises:
        BudgetExceededError: When daily/monthly budget would be exceeded
        RateLimitExceededError: When rate limits are exceeded
        PolicyViolationError: When Cost Guard policy is violated
        ValidationError: When input validation fails
    """
    options = TracingOptions(
        customer_id=customer_id,
        api_key=api_key,
        agent_id=agent_id,
        daily_budget=daily_budget,
        monthly_budget=monthly_budget,
        model=model,
        provider=provider,
        session_id=session_id,
        metadata=metadata,
        enable_caching=enable_caching,
    )
    
    ctx = TracingContext(options)
    
    try:
        yield ctx.__enter__()
    finally:
        ctx.__exit__(None, None, None)


def agentbill_traced(
    customer_id: Optional[str] = None,
    *,
    api_key: Optional[str] = None,
    agent_id: Optional[str] = None,
    daily_budget: Optional[float] = None,
    monthly_budget: Optional[float] = None,
) -> Callable[[F], F]:
    """
    Decorator for tracing CrewAI functions with Cost Guard protection.
    
    Example:
        @agentbill_traced(customer_id="cust-123", daily_budget=5.0)
        def run_crew():
            crew = Crew(agents=[agent], tasks=[task])
            return crew.kickoff()
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cid = customer_id or kwargs.pop('customer_id', None)
            if not cid:
                raise ValidationError("customer_id is required", "customer_id")
            
            with agentbill_tracing(
                customer_id=cid,
                api_key=api_key,
                agent_id=agent_id,
                daily_budget=daily_budget,
                monthly_budget=monthly_budget,
            ):
                return func(*args, **kwargs)
        
        return wrapper  # type: ignore
    
    return decorator


__all__ = [
    "TracingContext",
    "TracingOptions",
    "Span",
    "agentbill_tracing",
    "agentbill_traced",
    "VERSION",
]
