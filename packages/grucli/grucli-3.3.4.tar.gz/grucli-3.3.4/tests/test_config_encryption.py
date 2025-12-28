import pytest
import os
from grucli import config

def test_encryption_decryption():
    password = "secret_password"
    data = "my-secret-api-key"
    
    encrypted, salt = config.encrypt_data(data, password)
    assert isinstance(encrypted, bytes)
    assert isinstance(salt, bytes)
    
    decrypted = config.decrypt_data(encrypted, password, salt)
    assert decrypted == data

def test_decryption_wrong_password():
    password = "secret_password"
    data = "my-secret-api-key"
    
    encrypted, salt = config.encrypt_data(data, password)
    
    with pytest.raises(Exception):
        config.decrypt_data(encrypted, "wrong_password", salt)

def test_prune_history(tmp_path):
    history_file = tmp_path / "history.txt"
    content = ""
    for i in range(10):
        content += f"# Entry {i}\nmessage {i}\n"
    
    history_file.write_text(content)
    
    # Prune to 5 entries
    config.prune_history(str(history_file), max_entries=5)
    
    with open(history_file, 'r') as f:
        lines = f.readlines()
    
    # Count entries (lines starting with #)
    entry_count = sum(1 for line in lines if line.startswith('#'))
    assert entry_count == 5
    assert "# Entry 9" in lines[-2]
