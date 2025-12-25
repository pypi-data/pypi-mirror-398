"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 05, 2025

Distributed Tracing Integration for Enterprise Observability

Provides integration with distributed tracing systems:
- OpenTelemetry standard tracing
- Jaeger tracing backend
- Zipkin tracing backend
- Custom trace correlation
- Performance monitoring
"""

import time
import uuid
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from typing import Any, AsyncContextManager, ContextManager, Optional, Union
from .base import ATracingProvider
from .errors import TracingError
from .defs import SpanKind
from ..version import __version__

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from ..config.logging_setup import get_logger

logger = get_logger("xwsystem.monitoring.tracing")


@dataclass
class SpanContext:
    """Span context information."""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    baggage: dict[str, Any] = field(default_factory=dict)


@dataclass 
class TraceContext:
    """Trace context with correlation information."""
    trace_id: str
    correlation_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    service_name: str = "xwsystem"
    service_version: str = __version__




class OpenTelemetryTracer(ATracingProvider):
    """OpenTelemetry tracing provider."""
    
    def __init__(
        self,
        service_name: str = "xwsystem",
        otlp_endpoint: Optional[str] = None,
        zipkin_endpoint: Optional[str] = None
    ):
        """
        Initialize OpenTelemetry tracer.
        
        Args:
            service_name: Name of the service
            otlp_endpoint: Optional OTLP collector endpoint (modern standard, works with Jaeger/Zipkin)
            zipkin_endpoint: Optional Zipkin endpoint
        """
        # OpenTelemetry is now required
        
        self.service_name = service_name
        self._spans: dict[str, Any] = {}
        
        # Set up tracer provider
        trace.set_tracer_provider(TracerProvider())
        self.tracer = trace.get_tracer(service_name)
        
        # Set up exporters
        if otlp_endpoint:
            self._setup_otlp_exporter(otlp_endpoint)
        
        if zipkin_endpoint:
            self._setup_zipkin_exporter(zipkin_endpoint)
    
    def _setup_otlp_exporter(self, endpoint: str) -> None:
        """Set up OTLP exporter (modern standard, Python 3.8+ only, no legacy deps)."""
        try:
            # Lazy import to avoid pulling in dependencies unless actually used
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
            
            otlp_exporter = OTLPSpanExporter(endpoint=endpoint)
            span_processor = BatchSpanProcessor(otlp_exporter)
            trace.get_tracer_provider().add_span_processor(span_processor)
            logger.info(f"OTLP exporter configured for endpoint: {endpoint}")
            
        except ImportError:
            logger.warning(
                "OTLP exporter not available. Install with: pip install opentelemetry-exporter-otlp-proto-http"
            )
        except Exception as e:
            logger.warning(f"Failed to setup OTLP exporter: {e}")
    
    def _setup_zipkin_exporter(self, endpoint: str) -> None:
        """Set up Zipkin exporter."""
        # Import is explicit - if missing, user should install: pip install exonware-xwsystem[observability]
        from opentelemetry.exporter.zipkin.json import ZipkinExporter
        
        try:
            zipkin_exporter = ZipkinExporter(endpoint=endpoint)
            span_processor = BatchSpanProcessor(zipkin_exporter)
            trace.get_tracer_provider().add_span_processor(span_processor)
            
        except Exception as e:
            logger.warning(f"Failed to setup Zipkin exporter: {e}")
    
    def start_span(
        self, 
        name: str, 
        kind: SpanKind = SpanKind.INTERNAL,
        parent: Optional[SpanContext] = None,
        attributes: Optional[dict[str, Any]] = None
    ) -> SpanContext:
        """Start a new span."""
        span = self.tracer.start_span(name)
        
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        
        span_context = SpanContext(
            trace_id=f"{span.get_span_context().trace_id:032x}",
            span_id=f"{span.get_span_context().span_id:016x}",
            parent_span_id=parent.span_id if parent else None
        )
        
        self._spans[span_context.span_id] = span
        return span_context
    
    def finish_span(self, span: SpanContext, status: str = "OK", error: Optional[Exception] = None) -> None:
        """Finish a span."""
        if span.span_id in self._spans:
            otel_span = self._spans[span.span_id]
            
            if error:
                otel_span.set_status(trace.Status(trace.StatusCode.ERROR, str(error)))
                otel_span.record_exception(error)
            else:
                otel_span.set_status(trace.Status(trace.StatusCode.OK))
            
            otel_span.end()
            del self._spans[span.span_id]
    
    def add_span_attribute(self, span: SpanContext, key: str, value: Any) -> None:
        """Add attribute to span."""
        if span.span_id in self._spans:
            self._spans[span.span_id].set_attribute(key, value)
    
    def add_span_event(self, span: SpanContext, name: str, attributes: Optional[dict[str, Any]] = None) -> None:
        """Add event to span."""
        if span.span_id in self._spans:
            self._spans[span.span_id].add_event(name, attributes or {})


class JaegerTracer(ATracingProvider):
    """Jaeger-specific tracing provider (simplified implementation)."""
    
    def __init__(self, service_name: str = "xwsystem", agent_host: str = "localhost", agent_port: int = 6831):
        """Initialize Jaeger tracer."""
        self.service_name = service_name
        self.agent_host = agent_host
        self.agent_port = agent_port
        self._spans: dict[str, dict[str, Any]] = {}
    
    def start_span(
        self, 
        name: str, 
        kind: SpanKind = SpanKind.INTERNAL,
        parent: Optional[SpanContext] = None,
        attributes: Optional[dict[str, Any]] = None
    ) -> SpanContext:
        """Start a new span."""
        span_id = str(uuid.uuid4())
        trace_id = parent.trace_id if parent else str(uuid.uuid4())
        
        span_context = SpanContext(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent.span_id if parent else None
        )
        
        self._spans[span_id] = {
            'name': name,
            'kind': kind,
            'start_time': time.time(),
            'attributes': attributes or {},
            'events': [],
            'context': span_context
        }
        
        return span_context
    
    def finish_span(self, span: SpanContext, status: str = "OK", error: Optional[Exception] = None) -> None:
        """Finish a span."""
        if span.span_id in self._spans:
            span_data = self._spans[span.span_id]
            span_data['end_time'] = time.time()
            span_data['status'] = status
            span_data['error'] = str(error) if error else None
            
            # In a real implementation, this would send to Jaeger
            logger.debug(f"Finished span: {span_data['name']} ({span_data['end_time'] - span_data['start_time']:.3f}s)")
            
            del self._spans[span.span_id]
    
    def add_span_attribute(self, span: SpanContext, key: str, value: Any) -> None:
        """Add attribute to span."""
        if span.span_id in self._spans:
            self._spans[span.span_id]['attributes'][key] = value
    
    def add_span_event(self, span: SpanContext, name: str, attributes: Optional[dict[str, Any]] = None) -> None:
        """Add event to span."""
        if span.span_id in self._spans:
            self._spans[span.span_id]['events'].append({
                'name': name,
                'timestamp': time.time(),
                'attributes': attributes or {}
            })


class TracingManager:
    """Central tracing manager for XWSystem."""
    
    def __init__(self, provider: Optional[ATracingProvider] = None):
        """
        Initialize tracing manager.
        
        Args:
            provider: Tracing provider to use (defaults to no-op)
        """
        self.provider = provider or NoOpTracingProvider()
        self._current_trace: Optional[TraceContext] = None
    
    def set_provider(self, provider: ATracingProvider) -> None:
        """Set the tracing provider."""
        self.provider = provider
    
    def start_trace(self, operation_name: str, **context_data: Any) -> TraceContext:
        """Start a new trace."""
        trace_context = TraceContext(
            trace_id=str(uuid.uuid4()),
            correlation_id=str(uuid.uuid4()),
            **context_data
        )
        
        self._current_trace = trace_context
        return trace_context
    
    def get_current_trace(self) -> Optional[TraceContext]:
        """Get the current trace context."""
        return self._current_trace
    
    @contextmanager
    def trace_operation(
        self, 
        name: str, 
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Optional[dict[str, Any]] = None
    ) -> ContextManager[SpanContext]:
        """Context manager for tracing an operation."""
        span = self.provider.start_span(name, kind=kind, attributes=attributes)
        
        try:
            yield span
        except Exception as e:
            self.provider.finish_span(span, status="ERROR", error=e)
            raise
        else:
            self.provider.finish_span(span, status="OK")
    
    @asynccontextmanager
    async def trace_async_operation(
        self, 
        name: str, 
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Optional[dict[str, Any]] = None
    ) -> AsyncContextManager[SpanContext]:
        """Async context manager for tracing an operation."""
        span = self.provider.start_span(name, kind=kind, attributes=attributes)
        
        try:
            yield span
        except Exception as e:
            self.provider.finish_span(span, status="ERROR", error=e)
            raise
        else:
            self.provider.finish_span(span, status="OK")
    
    def add_trace_attribute(self, key: str, value: Any) -> None:
        """Add attribute to current trace."""
        if self._current_trace:
            # This would add to the root span in a real implementation
            logger.debug(f"Trace attribute: {key}={value}")
    
    def add_trace_event(self, name: str, attributes: Optional[dict[str, Any]] = None) -> None:
        """Add event to current trace."""
        if self._current_trace:
            # This would add to the current span in a real implementation
            logger.debug(f"Trace event: {name} {attributes or {}}")
    
    def is_tracing_enabled(self) -> bool:
        """Check if tracing is enabled."""
        return not isinstance(self.provider, NoOpTracingProvider)
    
    def get_current_span(self) -> Optional[SpanContext]:
        """Get current active span."""
        # Placeholder - would return active span in full implementation
        return None
    
    def start_span(self, name: str, parent: Optional[SpanContext] = None, attributes: Optional[dict[str, Any]] = None) -> SpanContext:
        """Start a new span."""
        return self.provider.start_span(name, parent=parent, attributes=attributes)
    
    def end_span(self, span: SpanContext) -> None:
        """End a span."""
        self.provider.finish_span(span)
    
    def add_span_attribute(self, span: SpanContext, key: str, value: Any) -> None:
        """Add attribute to span."""
        self.provider.add_span_attribute(span, key, value)
    
    def add_span_event(self, span: SpanContext, name: str, attributes: Optional[dict[str, Any]] = None) -> None:
        """Add event to span."""
        self.provider.add_span_event(span, name, attributes)


class NoOpTracingProvider(ATracingProvider):
    """No-op tracing provider for when tracing is disabled."""
    
    def start_span(
        self, 
        name: str, 
        kind: SpanKind = SpanKind.INTERNAL,
        parent: Optional[SpanContext] = None,
        attributes: Optional[dict[str, Any]] = None
    ) -> SpanContext:
        """Start a no-op span."""
        return SpanContext(
            trace_id="noop",
            span_id="noop"
        )
    
    def finish_span(self, span: SpanContext, status: str = "OK", error: Optional[Exception] = None) -> None:
        """Finish a no-op span."""
        pass
    
    def add_span_attribute(self, span: SpanContext, key: str, value: Any) -> None:
        """Add attribute to no-op span."""
        pass
    
    def add_span_event(self, span: SpanContext, name: str, attributes: Optional[dict[str, Any]] = None) -> None:
        """Add event to no-op span."""
        pass


# Global tracing manager instance
_tracing_manager = TracingManager()


def get_tracing_manager() -> TracingManager:
    """Get the global tracing manager."""
    return _tracing_manager


def configure_tracing(provider: ATracingProvider) -> None:
    """Configure global tracing provider."""
    _tracing_manager.set_provider(provider)


class DistributedTracing:
    """Distributed tracing manager for enterprise applications."""
    
    def __init__(self, provider: Optional[ATracingProvider] = None):
        """Initialize distributed tracing."""
        self.manager = TracingManager()
        if provider:
            self.manager.set_provider(provider)
    
    def start_trace(self, name: str, attributes: Optional[dict[str, Any]] = None) -> TraceContext:
        """Start a new trace."""
        return self.manager.start_trace(name, **(attributes or {}))
    
    def start_span(self, name: str, parent: Optional[SpanContext] = None, attributes: Optional[dict[str, Any]] = None) -> SpanContext:
        """Start a new span."""
        return self.manager.start_span(name, parent, attributes)
    
    def end_span(self, span: SpanContext) -> None:
        """End a span."""
        self.manager.end_span(span)
    
    def add_span_attribute(self, span: SpanContext, key: str, value: Any) -> None:
        """Add attribute to span."""
        self.manager.add_span_attribute(span, key, value)
    
    def add_span_event(self, span: SpanContext, name: str, attributes: Optional[dict[str, Any]] = None) -> None:
        """Add event to span."""
        self.manager.add_span_event(span, name, attributes)
    
    def set_provider(self, provider: ATracingProvider) -> None:
        """Set tracing provider."""
        self.manager.set_provider(provider)
    
    def get_current_span(self) -> Optional[SpanContext]:
        """Get current active span."""
        return self.manager.get_current_span()
    
    def is_tracing_enabled(self) -> bool:
        """Check if tracing is enabled."""
        return self.manager.is_tracing_enabled()

