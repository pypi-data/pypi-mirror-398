import pytest
from safecomms import SafeCommsClient
from unittest.mock import Mock, patch

def test_client_init():
    client = SafeCommsClient("test-key")
    assert client.api_key == "test-key"
    assert client.base_url == "https://api.safecomms.dev"

@patch('requests.Session.post')
def test_moderate_text(mock_post):
    # Setup mock response
    mock_response = Mock()
    mock_response.json.return_value = {"isClean": True}
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    client = SafeCommsClient("test-key")
    result = client.moderate_text("test content")

    assert result["isClean"] is True
    mock_post.assert_called_once()
    
    # Verify payload
    args, kwargs = mock_post.call_args
    assert kwargs['json']['content'] == "test content"
    assert kwargs['json']['moderationProfileId'] is None

@patch('requests.Session.get')
def test_get_usage(mock_get):
    # Setup mock response
    mock_response = Mock()
    mock_response.json.return_value = {"tokensUsed": 100}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    client = SafeCommsClient("test-key")
    result = client.get_usage()

    assert result["tokensUsed"] == 100
    mock_get.assert_called_once()
