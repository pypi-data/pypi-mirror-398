"""
Key binding handlers for grucli chat interface.
"""

import sys
import time
import asyncio
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.filters import has_completions
from . import interrupt
from . import permissions
from .theme import Colors


def get_chat_bindings(state):
    """Get key bindings for the chat prompt."""
    kb = KeyBindings()

    @kb.add(Keys.BackTab)
    def _(event):
        # Toggle accepting edits (Shift+Tab)
        store = permissions.PERMISSION_STORE
        if store.is_allowed(permissions.PermissionGroup.WRITE):
            store.revoke_always(permissions.PermissionGroup.WRITE)
            store.revoke_always(permissions.PermissionGroup.READ)
        else:
            store.allow_always(permissions.PermissionGroup.WRITE)
            # allow_always(WRITE) automatically grants READ in permissions.py
        event.app.invalidate()

    @kb.add(Keys.ControlC)
    @kb.add(Keys.Escape)
    def _(event):
        # Clear current input first
        if event.current_buffer.text:
            event.current_buffer.text = ""
            return

        if interrupt.should_quit():
            interrupt.clear_bottom_warning()
            sys.exit(0)
            
        # Show styled warning in bottom toolbar
        state['toolbar'] = HTML(
            f'<style fg="#ffff00">{interrupt.get_quit_hint()}</style>'
        )
        
        # Background task to clear the message after 3 seconds
        async def clear_warning():
            await asyncio.sleep(3)
            # Only clear if it hasn't been set to something else
            if state.get('toolbar') and "ctrl+c" in str(state['toolbar']).lower():
                state['toolbar'] = None
                event.app.invalidate()
        
        event.app.create_background_task(clear_warning())
        
    @kb.add(Keys.ControlJ)
    def _(event):
        # Ctrl+J for newline
        event.current_buffer.insert_text('\n')

    @kb.add(Keys.Enter, filter=has_completions)
    def _(event):
        # If completion menu is open, Enter selects the current item
        buf = event.current_buffer
        if buf.complete_state and buf.complete_state.current_completion:
            buf.apply_completion(buf.complete_state.current_completion)
        else:
            # Fallback in case filter was true but state vanished or no item selected
            event.current_buffer.validate_and_handle()

    return kb