"""
Interrupt handling and input utilities for grucli.
"""

import sys
import time
import shutil
import threading

try:
    import termios
except ImportError:
    termios = None

_last_interrupt_time = 0
_warning_stop_event = threading.Event()
_warning_stop_event.set()  # Initially stopped
_warning_lock = threading.Lock()


class BackSignal(Exception):
    """Signal to go back to previous menu."""
    pass


def get_quit_hint() -> str:
    """Get the quit hint message."""
    return "Press Ctrl+C again to quit"


def hide_control_chars():
    """Hide control character echo in terminal."""
    try:
        attrs = termios.tcgetattr(sys.stdin)
        attrs[3] &= ~termios.ECHOCTL
        termios.tcsetattr(sys.stdin, termios.TCSANOW, attrs)
    except Exception:
        pass


def show_control_chars():
    """Show control character echo in terminal."""
    try:
        attrs = termios.tcgetattr(sys.stdin)
        attrs[3] |= termios.ECHOCTL
        termios.tcsetattr(sys.stdin, termios.TCSANOW, attrs)
    except Exception:
        pass


def set_echo(enable: bool):
    """Disable or enable terminal echo."""
    if not termios:
        return
    try:
        attrs = termios.tcgetattr(sys.stdin)
        if enable:
            attrs[3] |= termios.ECHO
        else:
            attrs[3] &= ~termios.ECHO
        termios.tcsetattr(sys.stdin, termios.TCSANOW, attrs)
    except Exception:
        pass


def flush_input():
    """Flush pending terminal input."""
    if not termios:
        return
    try:
        termios.tcflush(sys.stdin, termios.TCIFLUSH)
    except Exception:
        pass


def should_quit():
    """Check if user has pressed Ctrl+C twice within 3 seconds."""
    global _last_interrupt_time
    now = time.time()
    if now - _last_interrupt_time < 3:
        return True
    _last_interrupt_time = now
    return False


def _warning_loop():
    """Background thread that displays the quit warning."""
    while not _warning_stop_event.is_set():
        try:
            columns, rows = shutil.get_terminal_size()
            target_row = max(1, rows - 1)
            msg = get_quit_hint()
            # \033[0;93m resets everything and then sets foreground to bright yellow
            sys.stdout.write(f"\0337\033[{target_row};1H\033[0;93m{msg}\033[0m\0338")
            sys.stdout.flush()
        except Exception:
            pass
        
        for _ in range(5):
            if _warning_stop_event.is_set():
                break
            time.sleep(0.1)


def clear_bottom_warning():
    """Clear the bottom warning bar."""
    _warning_stop_event.set()
    try:
        _, rows = shutil.get_terminal_size()
        target_row = max(1, rows - 1)
        sys.stdout.write(f"\0337\033[{target_row};1H\033[K\0338")
        sys.stdout.flush()
    except Exception:
        pass


def show_bottom_warning():
    """Show the bottom warning bar."""
    with _warning_lock:
        if not _warning_stop_event.is_set():
            return
        _warning_stop_event.clear()
    threading.Thread(target=_warning_loop, daemon=True).start()
    
    def stop_later():
        time.sleep(3)
        clear_bottom_warning()
            
    threading.Thread(target=stop_later, daemon=True).start()


def handle_interrupt(exit_msg="\nbye"):
    """Handle keyboard interrupt with double-press detection."""
    if should_quit():
        clear_bottom_warning()
        if exit_msg:
            print(exit_msg)
        sys.exit(0)
    
    show_bottom_warning()
    return get_quit_hint()


def prompt_input(prompt_text, is_password=False):
    """Get user input with styled prompt."""
    from prompt_toolkit import PromptSession
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.keys import Keys
    from prompt_toolkit.formatted_text import ANSI
    
    kb = KeyBindings()
    
    @kb.add(Keys.ControlC)
    @kb.add(Keys.Escape)
    def _(event):
        event.app.exit(exception=KeyboardInterrupt)

    session = PromptSession(key_bindings=kb)
    return session.prompt(ANSI(prompt_text), is_password=is_password)


def safe_input(prompt):
    """Get input with interrupt handling."""
    while True:
        try:
            return prompt_input(prompt)
        except KeyboardInterrupt:
            handle_interrupt()
            print()


def safe_getpass(prompt):
    """Get password input with interrupt handling."""
    while True:
        try:
            return prompt_input(prompt, is_password=True)
        except KeyboardInterrupt:
            handle_interrupt()
            print()