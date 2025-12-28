"""
Theme configuration for grucli.
"""

import shutil


class Colors:
    """ANSI color codes for terminal output."""
    
    # Core palette
    PRIMARY = "\033[38;5;39m"       # Bright blue
    SECONDARY = "\033[38;5;141m"    # Soft purple
    ACCENT = "\033[38;5;214m"       # Warm gold
    
    # Status colors
    SUCCESS = "\033[38;5;78m"       # Soft green
    WARNING = "\033[38;5;214m"      # Warm gold
    ERROR = "\033[38;5;203m"        # Soft red
    INFO = "\033[38;5;75m"          # Light blue
    MUTED = "\033[38;5;243m"        # Neutral gray
    WHITE = "\033[97m"
    THINK_COLOR = "\033[38;5;183m"  # Soft pink
    
    # Operation colors
    READ_OP = "\033[38;5;81m"       # Cyan
    WRITE_OP = "\033[38;5;214m"     # Gold
    DESTRUCTIVE_OP = "\033[38;5;203m"  # Red
    
    # UI elements
    PROMPT = "\033[38;5;39m"
    HEADER = "\033[1m"
    TITLE = "\033[38;5;39;1m"
    SUBTITLE = "\033[38;5;243m"
    
    # Modifiers
    DIM = "\033[2m"
    BOLD = "\033[1m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    REVERSE = "\033[7m"
    RESET = "\033[0m"
    
    # Input
    INPUT_ACTIVE = "\033[38;5;39m"
    INPUT_DISABLED = "\033[38;5;240m"
    INPUT_CONFIRM = "\033[38;5;221m"
    INPUT_ERROR = "\033[38;5;203m"


class Borders:
    """Box drawing characters."""
    
    TOP_LEFT = "╭"
    TOP_RIGHT = "╮"
    BOTTOM_LEFT = "╰"
    BOTTOM_RIGHT = "╯"
    HORIZONTAL = "─"
    VERTICAL = "│"
    T_LEFT = "├"
    T_RIGHT = "┤"
    T_TOP = "┬"
    T_BOTTOM = "┴"
    CROSS = "┼"


class Icons:
    """Unicode symbols."""
    
    CHECK = "✓"
    CROSS = "✗"
    WARNING = "!"
    INFO = "i"
    
    READ = "READ"
    WRITE = "WRITE"
    DELETE = "DELETE"
    FOLDER = "DIR"
    
    ARROW_RIGHT = "›"
    ARROW_DOWN = "↓"
    BULLET = "·"
    DIAMOND = "◆"
    CIRCLE = "○"
    CIRCLE_FILLED = "●"
    
    SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


class Styles:
    """Style helpers."""
    
    @staticmethod
    def success(text: str) -> str:
        return f"{Colors.SUCCESS}{text}{Colors.RESET}"
    
    @staticmethod
    def error(text: str) -> str:
        return f"{Colors.ERROR}{text}{Colors.RESET}"
    
    @staticmethod
    def warning(text: str) -> str:
        return f"{Colors.WARNING}{text}{Colors.RESET}"
    
    @staticmethod
    def info(text: str) -> str:
        return f"{Colors.INFO}{text}{Colors.RESET}"
    
    @staticmethod
    def muted(text: str) -> str:
        return f"{Colors.MUTED}{text}{Colors.RESET}"
    
    @staticmethod
    def bold(text: str) -> str:
        return f"{Colors.BOLD}{text}{Colors.RESET}"
    
    @staticmethod
    def primary(text: str) -> str:
        return f"{Colors.PRIMARY}{text}{Colors.RESET}"
    
    @staticmethod
    def accent(text: str) -> str:
        return f"{Colors.ACCENT}{text}{Colors.RESET}"


def get_terminal_width() -> int:
    """Get terminal width."""
    try:
        return shutil.get_terminal_size().columns
    except Exception:
        return 80
