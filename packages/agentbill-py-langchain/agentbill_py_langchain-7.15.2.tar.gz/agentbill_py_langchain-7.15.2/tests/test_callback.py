"""Tests for AgentBill LangChain callback handler."""

import pytest
from unittest.mock import Mock, patch
from agentbill_langchain import AgentBillCallback


@pytest.fixture
def callback():
    """Create a callback instance for testing."""
    return AgentBillCallback(
        api_key="test-api-key",
        base_url="https://test.agentbill.com",
        customer_id="test-customer",
        debug=False
    )


def test_callback_initialization(callback):
    """Test callback is initialized correctly."""
    assert callback is not None
    assert callback.api_key == "test-api-key"
    assert callback.base_url == "https://test.agentbill.com"
    assert callback.customer_id == "test-customer"


def test_callback_on_llm_start(callback):
    """Test callback handles LLM start event."""
    serialized = {"name": "OpenAI"}
    prompts = ["Test prompt"]
    
    # Should not raise exception
    callback.on_llm_start(serialized, prompts)


def test_callback_on_llm_end(callback):
    """Test callback handles LLM end event."""
    response = Mock()
    response.llm_output = {
        "token_usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        },
        "model_name": "gpt-4"
    }
    
    # Should not raise exception
    callback.on_llm_end(response)


def test_callback_on_llm_error(callback):
    """Test callback handles LLM error event."""
    error = Exception("Test error")
    
    # Should not raise exception
    callback.on_llm_error(error)


def test_callback_on_chain_start(callback):
    """Test callback handles chain start event."""
    serialized = {"name": "LLMChain"}
    inputs = {"input": "test"}
    
    # Should not raise exception
    callback.on_chain_start(serialized, inputs)


def test_callback_on_chain_end(callback):
    """Test callback handles chain end event."""
    outputs = {"output": "test"}
    
    # Should not raise exception
    callback.on_chain_end(outputs)


def test_callback_on_tool_start(callback):
    """Test callback handles tool start event."""
    serialized = {"name": "Calculator"}
    input_str = "2+2"
    
    # Should not raise exception
    callback.on_tool_start(serialized, input_str)


def test_callback_on_tool_end(callback):
    """Test callback handles tool end event."""
    output = "4"
    
    # Should not raise exception
    callback.on_tool_end(output)


@patch('requests.post')
def test_callback_flush(mock_post, callback):
    """Test callback flushes data correctly."""
    mock_post.return_value.status_code = 200
    
    # Simulate some activity
    callback.on_llm_start({"name": "OpenAI"}, ["test"])
    
    response = Mock()
    response.llm_output = {
        "token_usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        },
        "model_name": "gpt-4"
    }
    callback.on_llm_end(response)
    
    # Should not raise exception
    callback.flush()


def test_callback_context_manager(callback):
    """Test callback works as context manager."""
    with callback as cb:
        assert cb is callback
    # Should clean up properly
