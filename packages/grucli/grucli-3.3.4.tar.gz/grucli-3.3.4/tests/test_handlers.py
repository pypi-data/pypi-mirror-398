import pytest
from unittest.mock import MagicMock
from grucli.handlers import get_chat_bindings
from prompt_toolkit.keys import Keys

class MockCompleteState:
    def __init__(self, current_completion=None):
        self.current_completion = current_completion

class MockBuffer:
    def __init__(self):
        self.complete_state = None
        self.text = ""
        self.apply_completion = MagicMock()
        self.validate_and_handle = MagicMock()

class MockEvent:
    def __init__(self, buffer):
        self.current_buffer = buffer
        self.app = MagicMock()

def test_enter_handler_with_no_selection():
    """
    Test that pressing Enter when completion menu is open but no item is selected
    does NOT try to apply None completion (which crashes) but submits the buffer.
    """
    # 1. Setup mocks
    buffer = MockBuffer()
    # Simulate the state where completion menu is active (complete_state is not None)
    # but no item is selected (current_completion is None)
    buffer.complete_state = MockCompleteState(current_completion=None)
    event = MockEvent(buffer)
    
    # 2. Get bindings
    state = {'toolbar': None}
    kb = get_chat_bindings(state)
    
    # 3. Find the Enter handler
    enter_handlers = [b for b in kb.bindings if b.keys == (Keys.Enter,)]
    assert len(enter_handlers) > 0, "Could not find Enter handler"
    
    handler = enter_handlers[0].handler
    
    # 4. Call handler
    handler(event)
    
    # 5. Verify CORRECT behavior
    # It should NOT call apply_completion because current_completion is None
    buffer.apply_completion.assert_not_called()
    
    # It SHOULD call validate_and_handle (submit the buffer)
    buffer.validate_and_handle.assert_called_once()

def test_enter_handler_with_selection():
    """
    Test that pressing Enter when an item IS selected applies that completion.
    """
    # 1. Setup mocks
    buffer = MockBuffer()
    mock_completion = MagicMock()
    buffer.complete_state = MockCompleteState(current_completion=mock_completion)
    event = MockEvent(buffer)
    
    # 2. Get bindings
    state = {'toolbar': None}
    kb = get_chat_bindings(state)
    
    # 3. Find handler
    enter_handlers = [b for b in kb.bindings if b.keys == (Keys.Enter,)]
    handler = enter_handlers[0].handler
    
    # 4. Call handler
    handler(event)
    
    # 5. Verify behavior
    buffer.apply_completion.assert_called_once_with(mock_completion)
    buffer.validate_and_handle.assert_not_called()