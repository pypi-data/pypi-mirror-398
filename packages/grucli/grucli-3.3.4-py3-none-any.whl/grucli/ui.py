"""
Terminal UI components.
"""
import re
import sys
import time
import shutil
import threading

from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.styles import Style
from . import interrupt
from .theme import Colors, Borders, Icons, Styles, get_terminal_width


def print_messages(messages):
    """Print chat history to the terminal."""
    from . import tools # avoid circular import
    
    for msg in messages:
        role = msg.get('role')
        content = msg.get('content', '')
        reasoning = msg.get('reasoning')
        
        if role == 'system':
            continue
            
        if role == 'user':
            # Remove the attached files part for display if it exists
            display_content = content
            if "--- ATTACHED FILES ---" in content:
                display_content = content.split("--- ATTACHED FILES ---")[0].strip()
            
            print(f"\n{Colors.PRIMARY}> {Colors.RESET}{display_content}")
        
        elif role == 'assistant':
            ai_prefix = f"{Colors.SECONDARY}{Icons.DIAMOND}{Colors.RESET} "
            print(f"\n{ai_prefix}", end="")
            
            # Show reasoning duration if available
            duration = msg.get('thinking_duration')
            if duration:
                print(f"{Colors.MUTED}[Thought for {duration:.0f}s]{Colors.RESET}")
            elif reasoning:
                print(f"{Colors.MUTED}[Thought for history]{Colors.RESET}")
            
            # Clean content from <think> tags if they exist (some models output them in text)
            display_content = content
            if "<think>" in content and "</think>" in content:
                # Remove everything between and including <think> tags
                display_content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
            
            # Find tool calls in content
            cmds = tools.parse_commands(display_content)
            
            if not cmds:
                print(display_content)
            else:
                # Split content by tool calls to print them with their boxes
                last_idx = 0
                for cmd in cmds:
                    tool_str = cmd['original']
                    start_pos = display_content.find(tool_str, last_idx)
                    
                    if start_pos != -1:
                        # Print text before tool
                        pre_text = display_content[last_idx:start_pos]
                        if pre_text:
                            print(pre_text)
                        
                        # Handle tool display
                        if 'error' in cmd:
                            # Show failed tool calls
                            print(f"{Colors.MUTED}{tool_str}{Colors.RESET}")
                            print(f"{Colors.ERROR}Error parsing tool: {cmd['error']}{Colors.RESET}")
                        else:
                            # Hide valid tool calls (do nothing but skip the text)
                            pass
                        
                        last_idx = start_pos + len(tool_str)
                
                # Print remaining text
                remaining = display_content[last_idx:]
                if remaining:
                    print(remaining)
    print()


def print_ascii_art():
    """Print the logo with gradient."""
    logo = [
        " ██████╗ ██████╗ ██╗   ██╗ ██████╗██╗     ██╗",
        "██╔════╝ ██╔══██╗██║   ██║██╔════╝██║     ██║",
        "██║  ███╗██████╔╝██║   ██║██║     ██║     ██║",
        "██║   ██║██╔══██╗██║   ██║██║     ██║     ██║",
        "╚██████╔╝██║  ██║╚██████╔╝╚██████╗███████╗██║",
        " ╚═════╝ ╚═╝  ╚═╝ ╚═════╝  ╚═════╝╚══════╝╚═╝"
    ]
    
    gradient = [
        "\033[38;5;39m",   # Blue
        "\033[38;5;75m",   # Light blue
        "\033[38;5;111m",  # Sky
        "\033[38;5;147m",  # Lavender
        "\033[38;5;183m",  # Pink
        "\033[38;5;183m"   # Pink
    ]
    
    print()
    for i, line in enumerate(logo):
        color = gradient[i] if i < len(gradient) else gradient[-1]
        print(f"  {color}{line}{Colors.RESET}")
    
    from . import __version__
    print(f"  {Colors.MUTED}v{__version__}{Colors.RESET}")
    print()


def select_option(options, title="Select an option:", is_root=False):
    """Display selection menu with keyboard navigation."""
    if not options:
        raise ValueError("No options provided")

    selected_index = 0
    result = None

    from prompt_toolkit.formatted_text import ANSI, to_formatted_text
    
    def get_text():
        text = []
        text.extend(to_formatted_text(ANSI(f"  {Colors.BOLD}{title}{Colors.RESET}\n\n")))
        
        for i, option in enumerate(options):
            opt_text = option[1] if isinstance(option, tuple) else option

            if i == selected_index:
                line = f"\033[38;5;255;48;5;61;1m  {Icons.ARROW_RIGHT} {opt_text}\033[0m\n"
                text.extend(to_formatted_text(ANSI(line)))
            else:
                text.extend(to_formatted_text(ANSI(f"    {opt_text}\n")))
        
        text.extend(to_formatted_text(ANSI(f"\n  {Colors.MUTED}↑↓ navigate · enter select{Colors.RESET}\n")))
        
        return text

    kb = KeyBindings()

    @kb.add(Keys.Up)
    @kb.add('k')  # vim-style
    def _(event):
        nonlocal selected_index
        selected_index = (selected_index - 1) % len(options)

    @kb.add(Keys.Down)
    @kb.add('j')  # vim-style
    def _(event):
        nonlocal selected_index
        selected_index = (selected_index + 1) % len(options)

    @kb.add(Keys.Enter)
    def _(event):
        nonlocal result
        val = options[selected_index][1] if isinstance(options[selected_index], tuple) else options[selected_index]
        result = (val, selected_index)
        event.app.exit()

    @kb.add(Keys.ControlC)
    @kb.add(Keys.Escape, eager=True)
    def _(event):
        if not is_root:
            event.app.exit(exception=interrupt.BackSignal)
            return

        if interrupt.should_quit():
            interrupt.clear_bottom_warning()
            event.app.exit(exception=KeyboardInterrupt)
        else:
            interrupt.show_bottom_warning()

    style = Style.from_dict({
        '': '#eeeeee bg:#1c1c1c',          # Default: light gray on dark gray
        'title': '#af5fff bold',           # Purple, bold
        'selected': '#ffffff bg:#5f5faf',  # White on purple
        'option': '#eeeeee',               # Near white
        'cloud': '#0087ff',                # Blue for cloud
        'hint': '#8a8a8a',                 # Medium gray
    })

    app = Application(
        layout=Layout(Window(content=FormattedTextControl(get_text))),
        key_bindings=kb,
        style=style,
        full_screen=True,
    )

    app.run()
    return result


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes for length calculation."""
    return re.sub(r'\033\[[0-9;]*m', '', text)


def get_visible_len(text: str) -> int:
    """Get the visible length of a string containing ANSI escape codes."""
    return len(strip_ansi(text))


def print_header(title: str, subtitle: str = None):
    """Print a styled header."""
    print()
    print(f"{Colors.BOLD}{title}{Colors.RESET}")
    if subtitle:
        print(f"{Colors.MUTED}{subtitle}{Colors.RESET}")
    print()


def print_box(content: str, style: str = "info", title: str = None):
    """Print content in a styled box."""
    width = min(get_terminal_width() - 4, 70)
    
    style_colors = {
        "info": Colors.INFO,
        "success": Colors.SUCCESS,
        "warning": Colors.WARNING,
        "error": Colors.ERROR,
    }
    color = style_colors.get(style, Colors.INFO)
    
    lines = content.split('\n')
    
    if title:
        title_text = f" {title} "
        padding = width - len(title_text) - 2
        print(f"{color}{Borders.TOP_LEFT}{Borders.HORIZONTAL}{title_text}{Borders.HORIZONTAL * padding}{Borders.TOP_RIGHT}{Colors.RESET}")
    else:
        print(f"{color}{Borders.TOP_LEFT}{Borders.HORIZONTAL * width}{Borders.TOP_RIGHT}{Colors.RESET}")
    
    for line in lines:
        visible = strip_ansi(line)
        if len(visible) > width - 2:
            line = line[:width - 5] + "..."
            visible = strip_ansi(line)
        padding = " " * (width - len(visible) - 2)
        print(f"{color}{Borders.VERTICAL}{Colors.RESET} {line}{padding}{color}{Borders.VERTICAL}{Colors.RESET}")
    
    print(f"{color}{Borders.BOTTOM_LEFT}{Borders.HORIZONTAL * width}{Borders.BOTTOM_RIGHT}{Colors.RESET}")


def print_divider(char: str = None, color: str = None):
    """Print a divider line."""
    width = min(get_terminal_width() - 4, 50)
    c = char or Borders.HORIZONTAL
    col = color or Colors.MUTED
    print(f"{col}{c * width}{Colors.RESET}")


def print_tips():
    """Print getting started tips."""
    print(f"{Colors.MUTED}Quick start:{Colors.RESET}")
    print(f"{Colors.MUTED}  1. Ask questions, edit files, or run commands{Colors.RESET}")
    print(f"{Colors.MUTED}  2. Use {Colors.SECONDARY}@file{Colors.MUTED} to attach files{Colors.RESET}")
    print(f"{Colors.MUTED}  3. Type {Colors.SECONDARY}/help{Colors.MUTED} for commands{Colors.RESET}")
    print()


def format_tool_call_block(name: str, args: dict, category: str = "read") -> str:
    """Format a tool call as a styled block."""
    width = min(get_terminal_width() - 4, 65)
    
    colors = {
        "read": Colors.READ_OP,
        "write": Colors.WRITE_OP,
        "destructive": Colors.DESTRUCTIVE_OP,
    }
    icons = {
        "read": Icons.READ,
        "write": Icons.WRITE,
        "destructive": Icons.DELETE,
    }
    
    color = colors.get(category, Colors.INFO)
    icon = icons.get(category, Icons.INFO)
    
    lines = []
    
    header = f" [{icon}] {category.upper()} "
    padding = width - len(header) - 2
    lines.append(f"{color}{Borders.TOP_LEFT}{Borders.HORIZONTAL}{header}{Borders.HORIZONTAL * padding}{Borders.TOP_RIGHT}{Colors.RESET}")
    
    tool_line_content = f"  {Colors.BOLD}{name}{Colors.RESET}"
    visible_tool_len = get_visible_len(tool_line_content)
    padding_tool = " " * (width - visible_tool_len)
    lines.append(f"{color}{Borders.VERTICAL}{Colors.RESET}{tool_line_content}{padding_tool}{color}{Borders.VERTICAL}{Colors.RESET}")
    
    display_args = args.copy()
    if name == 'edit_file' and not display_args.get('new_string'):
        display_args['new_string'] = "(empty)"

    for key, value in display_args.items():
        if isinstance(value, str):
            if name == 'create_file' and key == 'content':
                content_lines = value.split('\n')
                display_lines = content_lines[:15]
                has_more = len(content_lines) > 15
                
                arg_label = f"  {Colors.MUTED}{key}:{Colors.RESET}"
                visible_label_len = get_visible_len(arg_label)
                padding_label = " " * (width - visible_label_len)
                lines.append(f"{color}{Borders.VERTICAL}{Colors.RESET}{arg_label}{padding_label}{color}{Borders.VERTICAL}{Colors.RESET}")
                
                for subline in display_lines:
                    if len(subline) > width - 6:
                        subline = subline[:width - 9] + "..."
                    
                    row = f"    {Colors.MUTED}{subline}{Colors.RESET}"
                    visible_row_len = get_visible_len(row)
                    padding_row = " " * (width - visible_row_len)
                    lines.append(f"{color}{Borders.VERTICAL}{Colors.RESET}{row}{padding_row}{color}{Borders.VERTICAL}{Colors.RESET}")
                
                if has_more:
                    more_row = f"    {Colors.MUTED}+{len(content_lines) - 15} more lines{Colors.RESET}"
                    visible_more_len = get_visible_len(more_row)
                    padding_more = " " * (width - visible_more_len)
                    lines.append(f"{color}{Borders.VERTICAL}{Colors.RESET}{more_row}{padding_more}{color}{Borders.VERTICAL}{Colors.RESET}")
                continue

            display = value[:width - 15] + "..." if len(value) > width - 12 else value
            if '\n' in display:
                display = display.split('\n')[0] + "..."
        else:
            display = repr(value)
        
        arg_line_content = f"  {Colors.MUTED}{key}:{Colors.RESET} {display}"
        visible_arg_len = get_visible_len(arg_line_content)
        
        if visible_arg_len > width - 2:
            arg_line_content = arg_line_content[:width - 5] + "..."
            visible_arg_len = get_visible_len(arg_line_content)
            
        padding_arg = " " * (width - visible_arg_len)
        lines.append(f"{color}{Borders.VERTICAL}{Colors.RESET}{arg_line_content}{padding_arg}{color}{Borders.VERTICAL}{Colors.RESET}")
    
    lines.append(f"{color}{Borders.BOTTOM_LEFT}{Borders.HORIZONTAL * width}{Borders.BOTTOM_RIGHT}{Colors.RESET}")
    
    return "\n".join(lines)


def format_diff(old_content: str, new_content: str, filename: str) -> str:
    """Format file changes as a diff."""
    width = min(get_terminal_width() - 4, 70)
    
    lines = []
    
    header = f" EDIT: {filename} "
    padding = max(0, width - len(header) - 2)
    lines.append(f"{Colors.WRITE_OP}{Borders.TOP_LEFT}{Borders.HORIZONTAL}{header}{Borders.HORIZONTAL * padding}{Borders.TOP_RIGHT}{Colors.RESET}")
    
    old_lines = old_content.split('\n')
    for old_line in old_lines[:8]:
        display = old_line[:width - 6] if len(old_line) > width - 6 else old_line
        lines.append(f"{Colors.WRITE_OP}{Borders.VERTICAL}{Colors.RESET} {Colors.ERROR}- {display}{Colors.RESET}")
    if len(old_lines) > 8:
        lines.append(f"{Colors.WRITE_OP}{Borders.VERTICAL}{Colors.RESET} {Colors.MUTED}  +{len(old_lines) - 8} more{Colors.RESET}")
    
    lines.append(f"{Colors.WRITE_OP}{Borders.VERTICAL}{Colors.MUTED}{Borders.HORIZONTAL * (width - 1)}{Colors.RESET}")
    
    if new_content is None:
        new_content = ""
        
    new_lines = new_content.split('\n')
    for new_line in new_lines[:8]:
        display = new_line[:width - 6] if len(new_line) > width - 6 else new_line
        lines.append(f"{Colors.WRITE_OP}{Borders.VERTICAL}{Colors.RESET} {Colors.SUCCESS}+ {display}{Colors.RESET}")
    if len(new_lines) > 8:
        lines.append(f"{Colors.WRITE_OP}{Borders.VERTICAL}{Colors.RESET} {Colors.MUTED}  +{len(new_lines) - 8} more{Colors.RESET}")
    
    lines.append(f"{Colors.WRITE_OP}{Borders.BOTTOM_LEFT}{Borders.HORIZONTAL * width}{Borders.BOTTOM_RIGHT}{Colors.RESET}")
    
    return "\n".join(lines)


class Spinner:
    """Loading spinner."""
    
    def __init__(self, message: str = "Loading"):
        self.message = message
        self.frames = Icons.SPINNER_FRAMES
        self.frame_idx = 0
        self._running = False
        self._thread = None
    
    def _animate(self):
        while self._running:
            frame = self.frames[self.frame_idx % len(self.frames)]
            sys.stdout.write(f"\r{Colors.SECONDARY}{frame}{Colors.RESET} {Colors.MUTED}{self.message}{Colors.RESET}  ")
            sys.stdout.flush()
            self.frame_idx += 1
            time.sleep(0.08)
    
    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._thread.start()
    
    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=0.2)
        sys.stdout.write(f"\r{' ' * 50}\r")
        sys.stdout.flush()
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, *args):
        self.stop()