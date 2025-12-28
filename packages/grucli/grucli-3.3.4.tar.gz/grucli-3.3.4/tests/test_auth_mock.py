import pytest
import json
import os
from unittest.mock import MagicMock, patch
from grucli import auth

def test_save_oauth_credentials(tmp_path, monkeypatch):
    # Mock config.get_config_dir
    monkeypatch.setattr(auth.config, "get_config_dir", lambda: str(tmp_path))
    
    mock_creds = MagicMock()
    mock_creds.token = "fake-access-token"
    mock_creds.refresh_token = "fake-refresh-token"
    mock_creds.scopes = ["scope1", "scope2"]
    mock_creds.expiry = None
    
    auth.save_oauth_credentials(mock_creds)
    
    auth_file = tmp_path / "google_auth.json"
    assert auth_file.exists()
    
    with open(auth_file, 'r') as f:
        data = json.load(f)
    
    assert data['access_token'] == "fake-access-token"
    assert data['refresh_token'] == "fake-refresh-token"

@patch('grucli.auth.Credentials')
def test_get_oauth_credentials_valid(mock_creds_class, tmp_path, monkeypatch):
    monkeypatch.setattr(auth.config, "get_config_dir", lambda: str(tmp_path))
    
    auth_file = tmp_path / "google_auth.json"
    auth_file.write_text(json.dumps({
        "access_token": "valid-token",
        "refresh_token": "refresh-token"
    }))
    
    mock_creds_instance = MagicMock()
    mock_creds_instance.valid = True
    mock_creds_class.return_value = mock_creds_instance
    
    creds = auth.get_oauth_credentials()
    assert creds is not None
    assert creds.valid is True
