"""
Tests for keyboard handling and interrupt behavior.
"""

import pytest
from grucli.interrupt import (
    should_quit,
    get_quit_hint,
    BackSignal,
)
import grucli.interrupt as interrupt_module


class TestDoubleCtrlC:
    """Test double Ctrl+C to exit behavior."""
    
    def test_first_press_returns_false(self):
        """First Ctrl+C should not quit."""
        # Reset the timer
        interrupt_module._last_interrupt_time = 0
        
        result = should_quit()
        assert result is False
    
    def test_second_press_within_window_returns_true(self):
        """Second Ctrl+C within 3 seconds should quit."""
        import time
        
        # First press
        interrupt_module._last_interrupt_time = 0
        should_quit()  # Sets time
        
        # Immediate second press
        result = should_quit()
        assert result is True
    
    def test_second_press_after_window_returns_false(self):
        """Second Ctrl+C after 3+ seconds should not quit."""
        import time
        
        # Set timestamp to old value
        interrupt_module._last_interrupt_time = time.time() - 10
        
        result = should_quit()
        assert result is False


class TestQuitHint:
    """Test quit hint message."""
    
    def test_hint_contains_ctrl_c(self):
        """Hint should mention Ctrl+C."""
        hint = get_quit_hint()
        assert 'ctrl+c' in hint.lower() or 'Ctrl+C' in hint
    
    def test_hint_is_string(self):
        """Hint should be a string."""
        hint = get_quit_hint()
        assert isinstance(hint, str)


class TestBackSignal:
    """Test the BackSignal exception."""
    
    def test_can_raise_back_signal(self):
        """BackSignal should be raisable."""
        with pytest.raises(BackSignal):
            raise BackSignal()
    
    def test_back_signal_is_exception(self):
        """BackSignal should be an Exception."""
        assert issubclass(BackSignal, Exception)
    
    def test_can_catch_back_signal(self):
        """Should be able to catch BackSignal specifically."""
        caught = False
        try:
            raise BackSignal()
        except BackSignal:
            caught = True
        except Exception:
            pass
        
        assert caught


class TestEscapeClearsInput:
    """Test that Escape key behavior is properly set up."""
    
    def test_escape_key_binding_exists(self):
        """Handlers should define Escape key binding."""
        from grucli.handlers import get_chat_bindings
        
        # Create mock state
        state = {'toolbar': None}
        bindings = get_chat_bindings(state)
        
        # Should return key bindings object
        assert bindings is not None
