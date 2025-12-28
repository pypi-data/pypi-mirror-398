import os
import pytest
from grucli import tools

def test_edit_file_deletion_args(tmp_path):
    tools.WORKING_DIR = str(tmp_path)
    path = "deletion_test.txt"
    content = "Line 1\nLine 2\nLine 3"
    
    # Create file
    tools.create_file(path, content)
    
    # Edit with new_string=None (simulating the behavior)
    res = tools.edit_file(path, "Line 2\n", None)
    
    assert "success" in res
    new_content = tools.read_file(path)
    # Expect Line 2 to be removed
    assert new_content == "Line 1\nLine 3"
    assert "Line 2" not in new_content
