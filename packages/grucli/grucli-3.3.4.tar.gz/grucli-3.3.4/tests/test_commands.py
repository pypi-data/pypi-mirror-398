import pytest
from grucli import commands
from prompt_toolkit.document import Document

def test_handle_command_exit():
    state = {'messages': []}
    result = commands.handle_command('/exit', state)
    assert result == "exit"

def test_handle_command_clear(monkeypatch):
    state = {'messages': [{'role': 'user', 'content': 'hi'}]}
    # Mock api.get_system_prompt
    monkeypatch.setattr(commands.api, "get_system_prompt", lambda: "System Prompt")
    
    result = commands.handle_command('/clear', state)
    assert result == "continue"
    assert len(state['messages']) == 1
    assert state['messages'][0]['content'] == "System Prompt"

def test_chat_completer_commands():
    completer = commands.ChatCompleter()
    doc = Document("/he", cursor_position=3)
    completions = list(completer.get_completions(doc, None))
    assert any(c.text == "/help" for c in completions)

def test_chat_completer_files(monkeypatch):
    completer = commands.ChatCompleter()
    # Mock tools.list_files_recursive
    monkeypatch.setattr(commands.tools, "list_files_recursive", lambda: ["src/main.py", "README.md"])
    
    doc = Document("@src", cursor_position=4)
    completions = list(completer.get_completions(doc, None))
    assert any(c.text == "src/main.py" for c in completions)
