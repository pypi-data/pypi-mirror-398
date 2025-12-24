import os
import json
import pytest
import langextract as lx
from unittest.mock import MagicMock, patch

# Ensure plugin is loaded for tests
def setup_module():
    # If using pytest, this runs once for the module.
    # We want to make sure the plugin is registered.
    # We can rely on the plugin being installed or add to path.
    # For now, we assume verify_plugin showed it works or we manually import.
    try:
        import langextract_openrouter
    except ImportError:
        pass

def test_provider_init_and_config():
    from langextract_openrouter.provider import OpenRouterProvider
    
    # Test initialization with default options
    provider = OpenRouterProvider(model_id="openrouter/test-model", api_key="test-key")
    assert provider.model_name == "test-model"
    assert provider.api_key == "test-key"
    assert provider.default_provider_options == {}

    # Test initialization with custom provider options
    custom_options = {"ignore": ["Parasail"], "sort": "throughput"}
    provider = OpenRouterProvider(
        model_id="openrouter/test-model", 
        api_key="test-key", 
        provider_options=custom_options
    )
    assert provider.default_provider_options == custom_options

def test_infer_calls_requests_correctly(monkeypatch):
    from langextract_openrouter.provider import OpenRouterProvider
    
    # Mock requests.post
    mock_post = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Test response"}}],
        "usage": {"total_tokens": 10}
    }
    mock_post.return_value = mock_response
    
    with patch("requests.post", mock_post):
        provider = OpenRouterProvider(
            model_id="openrouter/test-model", 
            api_key="test-key",
            provider_options={"ignore": ["BadProvider"]}
        )
        
        prompts = ["Hello"]
        results = list(provider.infer(prompts))
        
        # Verify result structure
        assert len(results) == 1
        assert results[0][0].output == "Test response"
        
        # Verify API call payload
        args, kwargs = mock_post.call_args
        assert args[0] == "https://openrouter.ai/api/v1/chat/completions"
        
        payload = json.loads(kwargs['data'])
        assert payload['model'] == "test-model"
        assert payload['messages'][0]['content'] == "Hello"
        assert payload['provider']['ignore'] == ["BadProvider"]
        assert payload['provider']['sort'] == "price" # Default retained
        assert payload['reasoning']['effort'] == "minimal" # Default

def test_infer_calls_with_custom_effort(monkeypatch):
    from langextract_openrouter.provider import OpenRouterProvider
    
    mock_post = MagicMock()
    mock_post.return_value.json.return_value = {
        "choices": [{"message": {"content": "Response"}}],
        "usage": {}
    }
    
    with patch("requests.post", mock_post):
        provider = OpenRouterProvider(model_id="openrouter/test", api_key="key")
        
        # Override at call time
        list(provider.infer(["Hi"], provider_options={"effort": "high"}))
        
        payload = json.loads(mock_post.call_args[1]['data'])
        assert payload['reasoning']['effort'] == "high"
        # Verify effort is removed from provider params
        assert "effort" not in payload['provider']

def test_infer_overrides_options(monkeypatch):
    from langextract_openrouter.provider import OpenRouterProvider
    
    mock_post = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Response"}}],
        "usage": {}
    }
    mock_post.return_value = mock_response
    
    with patch("requests.post", mock_post):
        provider = OpenRouterProvider(model_id="openrouter/test", api_key="key")
        
        # Override at call time (if supported by infer kwargs, though abstract base usually defines specific signature)
        # Our provider implementation checks kwargs["provider_options"].
        list(provider.infer(["Hi"], provider_options={"sort": "latency"}))
        
        payload = json.loads(mock_post.call_args[1]['data'])
        assert payload['provider']['sort'] == "latency"

def test_error_handling(monkeypatch):
    from langextract_openrouter.provider import OpenRouterProvider
    
    mock_post = MagicMock()
    mock_post.side_effect = Exception("Network Error")
    
    with patch("requests.post", mock_post):
        provider = OpenRouterProvider(model_id="openrouter/test", api_key="key")
        with pytest.raises(Exception):
            list(provider.infer(["Hi"]))
