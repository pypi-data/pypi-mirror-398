"""Tests for AgentBill SDK"""
import pytest
from unittest.mock import Mock, patch
from agentbill import AgentBill


class TestAgentBillInit:
    """Test AgentBill initialization"""

    def test_init_with_minimal_config(self):
        """Test initialization with minimal configuration"""
        config = {"api_key": "test-key"}
        agentbill = AgentBill.init(config)
        assert agentbill is not None
        assert agentbill.config["api_key"] == "test-key"

    def test_init_with_full_config(self):
        """Test initialization with full configuration"""
        config = {
            "api_key": "test-key",
            "base_url": "https://test.com",
            "customer_id": "test-customer",
            "debug": True
        }
        agentbill = AgentBill.init(config)
        assert agentbill.config["api_key"] == "test-key"
        assert agentbill.config["base_url"] == "https://test.com"
        assert agentbill.config["customer_id"] == "test-customer"
        assert agentbill.config["debug"] is True


class TestOpenAIWrapper:
    """Test OpenAI client wrapping"""

    def test_wrap_openai(self):
        """Test wrapping OpenAI client"""
        agentbill = AgentBill.init({"api_key": "test-key"})
        mock_client = Mock()
        wrapped = agentbill.wrap_openai(mock_client)
        assert wrapped is not None


class TestAnthropicWrapper:
    """Test Anthropic client wrapping"""

    def test_wrap_anthropic(self):
        """Test wrapping Anthropic client"""
        agentbill = AgentBill.init({"api_key": "test-key"})
        mock_client = Mock()
        wrapped = agentbill.wrap_anthropic(mock_client)
        assert wrapped is not None


class TestBedrockWrapper:
    """Test Bedrock client wrapping"""

    def test_wrap_bedrock(self):
        """Test wrapping Bedrock client"""
        agentbill = AgentBill.init({"api_key": "test-key"})
        mock_client = Mock()
        wrapped = agentbill.wrap_bedrock(mock_client)
        assert wrapped is not None


class TestAzureOpenAIWrapper:
    """Test Azure OpenAI client wrapping"""

    def test_wrap_azure_openai(self):
        """Test wrapping Azure OpenAI client"""
        agentbill = AgentBill.init({"api_key": "test-key"})
        mock_client = Mock()
        wrapped = agentbill.wrap_azure_openai(mock_client)
        assert wrapped is not None


class TestMistralWrapper:
    """Test Mistral client wrapping"""

    def test_wrap_mistral(self):
        """Test wrapping Mistral client"""
        agentbill = AgentBill.init({"api_key": "test-key"})
        mock_client = Mock()
        wrapped = agentbill.wrap_mistral(mock_client)
        assert wrapped is not None


class TestGoogleAIWrapper:
    """Test Google AI client wrapping"""

    def test_wrap_google_ai(self):
        """Test wrapping Google AI client"""
        agentbill = AgentBill.init({"api_key": "test-key"})
        mock_client = Mock()
        wrapped = agentbill.wrap_google_ai(mock_client)
        assert wrapped is not None


class TestTrackSignal:
    """Test custom signal tracking"""

    @patch('agentbill.client.requests.post')
    def test_track_signal(self, mock_post):
        """Test tracking custom signal"""
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"success": True}
        
        agentbill = AgentBill.init({"api_key": "test-key"})
        result = agentbill.track_signal(
            event_name="test_event",
            revenue=100,
            data={"key": "value"}
        )
        
        assert mock_post.called
        assert result is not None
