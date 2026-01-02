"""Tests for AgentBill Tracer"""
import pytest
from unittest.mock import patch, Mock
from agentbill.tracer import AgentBillTracer


class TestTracerInit:
    """Test Tracer initialization"""

    def test_tracer_init(self):
        """Test tracer initialization"""
        config = {"api_key": "test-key"}
        tracer = AgentBillTracer(config)
        assert tracer is not None
        assert tracer.config["api_key"] == "test-key"


class TestSpanOperations:
    """Test span operations"""

    def test_start_span(self):
        """Test starting a span"""
        config = {"api_key": "test-key"}
        tracer = AgentBillTracer(config)
        span = tracer.start_span("test.operation", {"test": "attr"})
        assert span is not None
        assert "span_id" in span
        assert "trace_id" in span

    def test_set_span_attribute(self):
        """Test setting span attributes"""
        config = {"api_key": "test-key"}
        tracer = AgentBillTracer(config)
        span = tracer.start_span("test.operation")
        tracer.set_span_attribute(span["span_id"], "key", "value")
        # Should not raise any errors

    def test_set_span_status(self):
        """Test setting span status"""
        config = {"api_key": "test-key"}
        tracer = AgentBillTracer(config)
        span = tracer.start_span("test.operation")
        tracer.set_span_status(span["span_id"], 0)  # OK status
        # Should not raise any errors

    def test_end_span(self):
        """Test ending a span"""
        config = {"api_key": "test-key"}
        tracer = AgentBillTracer(config)
        span = tracer.start_span("test.operation")
        tracer.end_span(span["span_id"])
        # Should not raise any errors


class TestFlush:
    """Test flushing spans"""

    @patch('agentbill.tracer.requests.post')
    def test_flush(self, mock_post):
        """Test flushing collected spans"""
        mock_post.return_value.status_code = 200
        
        config = {"api_key": "test-key", "base_url": "https://test.com"}
        tracer = AgentBillTracer(config)
        
        span = tracer.start_span("test.operation")
        tracer.end_span(span["span_id"])
        tracer.flush()
        
        assert mock_post.called
