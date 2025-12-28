import os
import pytest
from grucli import tools

def test_missing_path_attribute_error(tmp_path):
    # Setup WORKING_DIR
    tools.WORKING_DIR = str(tmp_path)
    
    # Test read_file with None path (should not crash)
    res = tools.read_file(None)
    assert "Error: path argument is required" in res
    
    # Test create_file with None path
    res = tools.create_file(None, "content")
    assert "Error: path argument is required" in res
    
    # Test edit_file with None path
    res = tools.edit_file(None, "old", "new")
    assert "Error: path argument is required" in res
    
    # Test delete_file with None path
    res = tools.delete_file(None)
    assert "Error: path argument is required" in res

def test_parse_commands_missing_args():
    # Test create_file missing content
    text = 'create_file(path="new.txt")'
    commands = tools.parse_commands(text)
    assert len(commands) == 1
    assert 'error' in commands[0]
    assert "missing required arguments: content" in commands[0]['error']

    # Test edit_file missing old_string
    text = 'edit_file(path="test.txt", new_string="new")'
    commands = tools.parse_commands(text)
    assert len(commands) == 1
    assert 'error' in commands[0]
    assert "missing required arguments: old_string" in commands[0]['error']

def test_parse_commands_valid_syntax_invalid_args():
    # This matches the user's example where it's valid syntax but logically wrong for the tool
    text = 'create_file(path="test.txt")'
    commands = tools.parse_commands(text)
    assert len(commands) == 1
    assert 'error' in commands[0]
    assert "missing required arguments: content" in commands[0]['error']
