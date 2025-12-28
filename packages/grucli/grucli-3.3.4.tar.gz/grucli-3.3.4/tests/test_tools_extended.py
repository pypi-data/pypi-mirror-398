import os
import pytest
from grucli import tools

def test_is_safe_path(tmp_path):
    # Setup WORKING_DIR to a temporary directory for testing
    tools.WORKING_DIR = str(tmp_path)
    
    # Safe paths
    safe, full_path = tools.is_safe_path("test.txt")
    assert safe is True
    assert full_path == os.path.abspath(os.path.join(str(tmp_path), "test.txt"))
    
    safe, full_path = tools.is_safe_path("subdir/test.txt")
    assert safe is True
    
    # Unsafe paths
    safe, _ = tools.is_safe_path("../outside.txt")
    assert safe is False
    
    safe, _ = tools.is_safe_path("/public/index.html")
    assert safe is True

def test_parse_commands():
    text = """
    I will read the file now.
    ```python
    read_file(path="test.py", start_line=1, end_line=10)
    ```
    And then edit it.
    edit_file(path='test.py', old_string='old', new_string='new')
    """
    commands = tools.parse_commands(text)
    assert len(commands) == 2
    
    assert commands[0]['name'] == 'read_file'
    assert commands[0]['args']['path'] == 'test.py'
    assert commands[0]['args']['start_line'] == 1
    
    assert commands[1]['name'] == 'edit_file'
    assert commands[1]['args']['old_string'] == 'old'

def test_parse_commands_invalid_syntax():
    text = """
    This call has a syntax error (missing closing quote).
    read_file(path="test.py)
    
    This call is valid.
    read_file(path="valid.py")
    """
    commands = tools.parse_commands(text)
    # The first one should fail to parse but be detected
    # The second one should succeed
    assert len(commands) == 2
    
    error_cmd = next((c for c in commands if 'error' in c), None)
    assert error_cmd is not None
    assert "invalid syntax" in error_cmd['error']
    assert "test.py" in error_cmd['original']
    
    valid_cmd = next((c for c in commands if 'args' in c), None)
    assert valid_cmd is not None
    assert valid_cmd['args']['path'] == 'valid.py'

def test_parse_commands_complex_nesting():
    text = """
    edit_file(path="nested.py", old_string='''def foo():
    pass''', new_string='''def foo():
    print("bar")''')
    """
    commands = tools.parse_commands(text)
    assert len(commands) == 1
    assert "print(\"bar\")" in commands[0]['args']['new_string']

def test_file_operations(tmp_path):
    tools.WORKING_DIR = str(tmp_path)
    path = "test_file.txt"
    content = "Hello World"
    
    # Create
    res = tools.create_file(path, content)
    assert "success" in res
    assert os.path.exists(os.path.join(tmp_path, path))
    
    # Read
    read_res = tools.read_file(path)
    assert read_res == content
    
    # Edit
    edit_res = tools.edit_file(path, "World", "Universe")
    assert "success" in edit_res
    assert tools.read_file(path) == "Hello Universe"
    
    # Delete
    del_res = tools.delete_file(path)
    assert "success" in del_res
    assert not os.path.exists(os.path.join(tmp_path, path))
