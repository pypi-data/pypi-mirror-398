import pytest
import time
import os
from unittest.mock import MagicMock, patch
from AnosysLoggers.tracing import (
    setup_tracing,
    extract_span_info,
    AnosysHttpExporter
)
from opentelemetry.sdk.trace import TracerProvider, ReadableSpan
from opentelemetry.trace import SpanContext, TraceFlags, SpanKind
from opentelemetry.sdk.resources import Resource
from opentelemetry import trace

# --- Helper to create a dummy span ---
def create_dummy_span(
    name="test_span",
    trace_id=0xabcdef1234567890abcdef1234567890, # Use hex chars to avoid auto-int conversion in utils
    span_id=0xabcdef1234567890,
    start_time=1672531200000000000, # 2023-01-01 00:00:00 UTC (ns)
    end_time=1672531201000000000,   # + 1 second
    attributes=None
):
    context = SpanContext(
        trace_id=trace_id,
        span_id=span_id,
        is_remote=True,
        trace_flags=TraceFlags.SAMPLED
    )
    resource = Resource(attributes={"service.name": "test_service"})
    
    mock_span = MagicMock(spec=ReadableSpan)
    mock_span.name = name
    mock_span.context = context
    # Create parent if needed, for now mostly None
    mock_span.parent = None 
    mock_span.kind = SpanKind.CLIENT
    mock_span.start_time = start_time
    mock_span.end_time = end_time
    mock_span.attributes = attributes or {}
    mock_span.resource = resource
    return mock_span

# --- Tests ---

def test_extract_span_info():
    attributes = {
        "llm.model_name": "gpt-4",
        "llm.token_count": 42,
        "input.value": "hello",
    }
    span = create_dummy_span(attributes=attributes)
    
    data = extract_span_info(span)
    
    # Check basics
    assert data["otel_name"] == "test_span"
    assert data["otel_record_type"] == "AnoSys Trace"
    # Duration: 1 second = 1000 ms
    assert data["otel_duration_ms"] == 1000
    
    # Old assertions removed

    
    # Check logic for attributes
    # The keys might be remapped to 'cvsXXX' or 'cvnXXX' in reality, 
    # but the test checks the values mapped to internal keys first?
    # Wait, extract_span_info calls `reassign`, which REMAPS keys to cvs/cvn!
    # So `data` keys will be `cvs100`, `otel_trace_id`, etc.
    # The `key_to_cvs` in tracing.py maps known keys.
    # "name" -> "otel_name"
    # "trace_id" -> "otel_trace_id"
    # "span_id" -> "otel_span_id"
    # "model_name" via 'llm_model' -> 'llm_model'
    
    # Check mapped keys presence
    # from key_to_cvs in tracing.py:
    # "name": "otel_name"
    # "trace_id": "otel_trace_id"
    # "llm_model": "llm_model"
    
    assert data["otel_name"] == "test_span"
    assert data["otel_trace_id"] == "abcdef1234567890abcdef1234567890"
    assert data["otel_span_id"] == "abcdef1234567890"
    assert data["llm_model"] == "gpt-4"
    assert "42" in str(data.values()) # 42 matches token count (might be stringified)

@patch("requests.post")
def test_anosys_http_exporter(mock_post):
    mock_post.return_value.status_code = 200
    
    exporter = AnosysHttpExporter()
    span = create_dummy_span()
    
    # Export expects an iterable
    exporter.export([span])
    
    assert mock_post.called
    args, kwargs = mock_post.call_args
    payload = kwargs['json']
    
    assert payload["otel_name"] == "test_span"

def test_setup_tracing_with_new_provider():
    # Mock trace.get_tracer_provider returning default (ProxyTracerProvider)
    # or something that is NOT an SDK TracerProvider
    
    with patch("opentelemetry.trace.get_tracer_provider") as mock_get_provider, \
         patch("opentelemetry.trace.set_tracer_provider") as mock_set_provider, \
         patch("traceai_openai_agents.OpenAIAgentsInstrumentor") as mock_instrumentor, \
         patch.dict(os.environ, {"ANOSYS_API_KEY": "test"}):
         
         # Assume current provider is just a proxy (not instance of sdk.TracerProvider)
         mock_get_provider.return_value = MagicMock() 
         
         setup_tracing("http://test.com")
         
         # Should have called set_tracer_provider with a NEW provider
         assert mock_set_provider.called
         new_provider = mock_set_provider.call_args[0][0]
         assert isinstance(new_provider, TracerProvider)

def test_setup_tracing_with_existing_provider():
    # Simulate an existing SDK TracerProvider
    existing_provider = TracerProvider()
    
    with patch("opentelemetry.trace.get_tracer_provider", return_value=existing_provider), \
         patch("opentelemetry.trace.set_tracer_provider") as mock_set_provider, \
         patch("traceai_openai_agents.OpenAIAgentsInstrumentor") as mock_instrumentor:

         # Add a spy to add_span_processor
         with patch.object(existing_provider, "add_span_processor") as mock_add_processor:
             setup_tracing("http://test.com")
             
             # Should NOT replace the global provider
             mock_set_provider.assert_not_called()
             
             # Should have added processor to EXISTING provider
             assert mock_add_processor.called
             
