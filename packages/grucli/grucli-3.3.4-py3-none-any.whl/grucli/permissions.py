"""
Permission system for tool execution.
"""

from enum import Enum
from typing import Set, Dict, Optional, Tuple
from .theme import Colors, Borders, Icons, Styles, get_terminal_width


class PermissionGroup(Enum):
    """Permission categories for tool operations."""
    READ = "read"           # read_file, get_current_directory_structure
    WRITE = "write"         # create_file, edit_file
    DESTRUCTIVE = "delete"  # delete_file


# Tool-to-permission-group mapping
TOOL_PERMISSION_MAP: Dict[str, PermissionGroup] = {
    'read_file': PermissionGroup.READ,
    'get_current_directory_structure': PermissionGroup.READ,
    'create_file': PermissionGroup.WRITE,
    'edit_file': PermissionGroup.WRITE,
    'delete_file': PermissionGroup.DESTRUCTIVE,
}


# Human-readable descriptions for permission groups
PERMISSION_DESCRIPTIONS: Dict[str, PermissionGroup] = {
    PermissionGroup.READ: "Read files and directories",
    PermissionGroup.WRITE: "Create and modify files",
    PermissionGroup.DESTRUCTIVE: "Delete files",
}


# Colors for permission groups
PERMISSION_COLORS: Dict[PermissionGroup, str] = {
    PermissionGroup.READ: Colors.READ_OP,
    PermissionGroup.WRITE: Colors.WRITE_OP,
    PermissionGroup.DESTRUCTIVE: Colors.DESTRUCTIVE_OP,
}


# Icons for permission groups
PERMISSION_ICONS: Dict[PermissionGroup, str] = {
    PermissionGroup.READ: Icons.READ,
    PermissionGroup.WRITE: Icons.WRITE,
    PermissionGroup.DESTRUCTIVE: Icons.DELETE,
}


class PermissionStore:
    """Session-scoped permission storage."""
    
    def __init__(self):
        self._allowed_always: Set[PermissionGroup] = set()
    
    def is_allowed(self, group: PermissionGroup) -> bool:
        return group in self._allowed_always
    
    def allow_always(self, group: PermissionGroup) -> None:
        self._allowed_always.add(group)
        if group == PermissionGroup.WRITE:
            self._allowed_always.add(PermissionGroup.READ)

    def revoke_always(self, group: PermissionGroup) -> None:
        self._allowed_always.discard(group)
    
    def reset(self) -> None:
        self._allowed_always.clear()
    
    def get_allowed_groups(self) -> Set[PermissionGroup]:
        return self._allowed_always.copy()


# Global permission store instance
PERMISSION_STORE = PermissionStore()


def get_tool_permission_group(tool_name: str) -> Optional[PermissionGroup]:
    """Get the permission group for a tool."""
    return TOOL_PERMISSION_MAP.get(tool_name)


def format_tool_for_permission(tool_name: str, args: dict) -> str:
    """Format tool for permission display."""
    group = get_tool_permission_group(tool_name)
    if not group:
        return f"{tool_name}(...)"
    
    color = PERMISSION_COLORS.get(group, Colors.WHITE)
    icon = PERMISSION_ICONS.get(group, "")
    
    arg_parts = []
    for key, value in args.items():
        if isinstance(value, str) and len(value) > 50:
            value = value[:47] + "..."
        arg_parts.append(f"{Colors.MUTED}{key}={Colors.RESET}{repr(value)}")
    
    args_str = ", ".join(arg_parts) if arg_parts else ""
    
    return f"{color}{icon} {tool_name}{Colors.RESET}({args_str})"


def prompt_permission(tool_name: str, args: dict) -> str:
    """Display permission prompt."""
    from . import interrupt
    
    group = get_tool_permission_group(tool_name)
    if not group:
        group = PermissionGroup.WRITE
    
    if PERMISSION_STORE.is_allowed(group):
        return 'always'
    
    color = PERMISSION_COLORS.get(group, Colors.WHITE)
    
    print(f"  {Colors.SUCCESS}1{Colors.RESET}) Allow once")
    print(f"  {Colors.PRIMARY}2{Colors.RESET}) Allow always {Colors.MUTED}({group.value} ops, this session){Colors.RESET}")
    print(f"  {Colors.ERROR}3{Colors.RESET}) Deny")
    print()
    
    while True:
        try:
            choice = interrupt.safe_input(f"{color}[1/2/3]: {Colors.RESET}").strip()
            if choice in ['1', '2', '3']:
                print("\033[A\033[K" * 5, end="", flush=True)
            if choice == '1':
                return 'once'
            elif choice == '2':
                PERMISSION_STORE.allow_always(group)
                print(f"{Colors.SUCCESS}{Icons.CHECK} {group.value} operations allowed{Colors.RESET}")
                return 'always'
            elif choice == '3':
                print(f"{Colors.WARNING}{Icons.WARNING} Denied{Colors.RESET}")
                return 'deny'
            else:
                print(f"{Colors.ERROR}Enter 1, 2, or 3{Colors.RESET}")
        except KeyboardInterrupt:
            print(f"\n{Colors.WARNING}{Icons.WARNING} Cancelled{Colors.RESET}")
            return 'deny'


def check_permission(tool_name: str, args: dict) -> Tuple[bool, str]:
    """Check if a tool has permission to execute."""
    group = get_tool_permission_group(tool_name)
    
    if group and PERMISSION_STORE.is_allowed(group):
        return True, 'always'
    
    decision = prompt_permission(tool_name, args)
    return decision != 'deny', decision
