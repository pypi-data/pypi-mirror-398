import os
import sys
import json
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.path.abspath('.'))

import responses
from idtap.client import SwaraClient

BASE = 'https://swara.studio/'

@responses.activate
@patch('idtap.client.SwaraClient.has_agreed_to_waiver', return_value=True)
def test_authorization_header(mock_waiver, tmp_path):
    # Use isolated token path to prevent loading existing tokens
    client = SwaraClient(token_path=tmp_path / 'test_token.json', auto_login=False)
    # Directly set token and user to bypass secure storage complexity
    client.token = 'abc'
    client.user = {'_id': 'u1'}
    
    endpoint = BASE + 'api/transcription/1'
    responses.get(endpoint, json={'_id': '1'}, status=200)
    client.get_piece('1')
    assert responses.calls[0].request.headers['Authorization'] == 'Bearer abc'

@responses.activate  
@patch('idtap.client.SecureTokenStorage')
@patch('idtap.client.SwaraClient.has_agreed_to_waiver', return_value=True)
def test_no_token_header(mock_waiver, mock_storage, tmp_path):
    # Mock storage to return no token
    mock_storage_instance = mock_storage.return_value
    mock_storage_instance.get_token.return_value = None
    
    client = SwaraClient(token_path=tmp_path / 'missing.json', auto_login=False)
    # Ensure no token is set
    client.token = None
    client.user = None
    
    endpoint = BASE + 'api/transcription/1'
    responses.get(endpoint, json={'_id': '1'}, status=200)
    client.get_piece('1')
    assert 'Authorization' not in responses.calls[0].request.headers



