import json
import pytest
from grucli import api

def test_parse_openai_chunk():
    # Normal content
    line = 'data: ' + json.dumps({
        "choices": [{"delta": {"content": "hello"}}]
    })
    content, reasoning, done = api._parse_openai_chunk(line)
    assert content == "hello"
    assert reasoning == ""
    assert done is False
    
    # Reasoning
    line = 'data: ' + json.dumps({
        "choices": [{"delta": {"reasoning_content": "thinking..."}}]
    })
    content, reasoning, done = api._parse_openai_chunk(line)
    assert content == ""
    assert reasoning == "thinking..."
    assert done is False
    
    # Done
    assert api._parse_openai_chunk("data: [DONE]") == ("", "", True)

def test_parse_anthropic_chunk():
    # Text delta
    line = 'data: ' + json.dumps({
        "type": "content_block_delta",
        "delta": {"type": "text_delta", "text": "hi"}
    })
    content, reasoning, done = api._parse_anthropic_chunk(line)
    assert content == "hi"
    assert done is False
    
    # Thinking delta
    line = 'data: ' + json.dumps({
        "type": "content_block_delta",
        "delta": {"type": "thinking_delta", "thinking": "hm..."}
    })
    content, reasoning, done = api._parse_anthropic_chunk(line)
    assert reasoning == "hm..."
    
    # Message stop
    line = 'data: ' + json.dumps({"type": "message_stop"})
    _, _, done = api._parse_anthropic_chunk(line)
    assert done is True

def test_parse_gemini_chunk():
    line = 'data: ' + json.dumps({
        "candidates": [{"content": {"parts": [{"text": "Gemini response"}]}}]
    })
    content, reasoning, done = api._parse_gemini_chunk(line)
    assert content == "Gemini response"
    assert done is False

def test_get_system_prompt(tmp_path, monkeypatch):
    # Mock sysprompts/main_sysprompt.txt location
    mock_dir = tmp_path / "sysprompts"
    mock_dir.mkdir()
    prompt_file = mock_dir / "main_sysprompt.txt"
    prompt_file.write_text("System: <auto_inject_file_tree>")
    
    def mock_realpath(path):
        return str(tmp_path / "api.py")
        
    import os
    monkeypatch.setattr(os.path, "realpath", mock_realpath)
    monkeypatch.setattr(api.tools, "get_file_tree", lambda: "file1.txt\nfile2.txt")
    
    prompt = api.get_system_prompt()
    assert "System:" in prompt
    assert "file1.txt" in prompt
