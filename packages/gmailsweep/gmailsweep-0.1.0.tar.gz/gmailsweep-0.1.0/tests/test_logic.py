
import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
from src import logic

@pytest.fixture
def mock_gmail_service():
    with patch('src.logic.get_gmail_service') as mock_get:
        yield mock_get

def test_fetch_total_count_success(mock_gmail_service):
    # Setup mock response
    mock_service = list_mock = MagicMock()
    mock_gmail_service.return_value = mock_service
    
    # Mock the chain: service.users().messages().list().execute()
    mock_service.users.return_value.messages.return_value.list.return_value.execute.return_value = {
        'resultSizeEstimate': 42
    }
    
    count = logic.fetch_total_count("test query")
    assert count == 42
    
def test_fetch_total_count_failure(mock_gmail_service):
    # Mock service to return a mock object
    mock_service = MagicMock()
    mock_gmail_service.return_value = mock_service
    
    # Make the execute() call raise an exception
    mock_service.users.return_value.messages.return_value.list.return_value.execute.side_effect = Exception("API Error")
    
    count = logic.fetch_total_count("test query")
    assert count == 0

def test_fetch_messages_success(mock_gmail_service):
    mock_service = MagicMock()
    mock_gmail_service.return_value = mock_service
    
    # Mock response with 2 messages
    mock_response = {
        'messages': [
            {'id': 'msg1', 'threadId': 't1'},
            {'id': 'msg2', 'threadId': 't2'}
        ]
    }
    
    # Mock list().execute()
    mock_service.users.return_value.messages.return_value.list.return_value.execute.return_value = mock_response
    # Mock list_next() to return None (stop pagination)
    mock_service.users.return_value.messages.return_value.list_next.return_value = None
    
    messages = logic.fetch_messages("query", max_results=10)
    assert len(messages) == 2
    assert messages[0]['id'] == 'msg1'

def test_batch_delete_messages(mock_gmail_service):
    mock_service = MagicMock()
    mock_gmail_service.return_value = mock_service
    
    ids = ['id1', 'id2', 'id3']
    deleted_count = logic.batch_delete_messages(ids)
    
    # Verify it called batchDelete
    mock_service.users.return_value.messages.return_value.batchDelete.assert_called()
    assert deleted_count == 3
