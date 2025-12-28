import os
import ast
import shutil
import re
from .theme import Colors

WORKING_DIR = os.getcwd()

# Constant error messages for tools to avoid copy-paste
ERROR_PATH_OUTSIDE_DIR = "Error: Please stay within current directory, your file paths should be relative, not absolute."
ERROR_FILE_DOES_NOT_EXIST = "Error: File {path} does not exist, refer to file tree, file paths should be relative, not absolute"
ERROR_READING_FILE = "Error reading file: {error}"
ERROR_EDITING_FILE_NO_MATCH = "Error: old_string not found in file. Exact match required, use read file tool to analyse."
ERROR_EDITING_FILE_MULTIPLE_MATCHES = "Error: old_string found multiple times in file ({count} occurrences). Please provide a more unique string or include surrounding context."
ERROR_EDITING_FILE_IDENTICAL = "Error: old_string and new_string are identical. No changes made."
ERROR_EDITING_FILE = "Error editing file: {error}"
ERROR_DELETING_FILE = "Error deleting file: {error}"

def is_safe_path(path):
    # resolves symlinks and relative paths for it to stay within current dir
    if path is None:
        return False, None
    
    # Force path to be relative by stripping leading slashes
    # LLMs often try /main.py when they mean main.py
    path = path.lstrip('/')
        
    # If it's absolute, check if it's within WORKING_DIR directly
    if os.path.isabs(path):
        target = os.path.abspath(path)
    else:
        target = os.path.abspath(os.path.join(WORKING_DIR, path))
    
    try:
        is_safe = os.path.commonpath([WORKING_DIR, target]) == WORKING_DIR
    except ValueError:
        return False, None
        
    return is_safe, target

def get_file_tree(startpath='.'):
    """Generate a tree view of the directory structure for context."""
    tree_str = ""
    for root, dirs, files in os.walk(startpath):
        # skip hidden stuff
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * (level)
        tree_str += f"{indent}{os.path.basename(root)}/\n"
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            if not f.startswith('.'):
                tree_str += f"{subindent}{f}\n"
    
    if not tree_str.strip():
        return "Current directory empty"
        
    return tree_str

def read_file(path, start_line=None, end_line=None):
    if path is None:
        return "Error: path argument is required"
    path = path.lstrip('/')
    safe, full_path = is_safe_path(path)
    if not safe:
        return ERROR_PATH_OUTSIDE_DIR
        
    if not os.path.exists(full_path):
        return ERROR_FILE_DOES_NOT_EXIST.format(path=path)
        
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            if start_line is None and end_line is None:
                return f.read()
            
            lines = f.readlines()
            
            # fix for potential NoneType math error
            s = (int(start_line) - 1) if start_line is not None else 0
            e = int(end_line) if end_line is not None else len(lines)
            
            # clamp values
            s = max(0, s)
            e = min(len(lines), e)
            
            return "".join(lines[s:e])
    except Exception as e:
        return ERROR_READING_FILE.format(error=str(e))

def create_file(path, content):
    if path is None:
        return "Error: path argument is required"
    if content is None:
        return "Error: content argument is required"
    path = path.lstrip('/')
    safe, full_path = is_safe_path(path)
    if not safe:
        return ERROR_PATH_OUTSIDE_DIR
        
    try:
        # ensure subdirs exist
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"success: created {path}"
    except Exception as e:
        return f"Error creating file: {e}"

def edit_file(path, old_string, new_string):
    if path is None:
        return "Error: path argument is required"
    if old_string is None:
        return "Error: old_string argument is required"
    if new_string is None:
        new_string = ""

    path = path.lstrip('/')
    safe, full_path = is_safe_path(path)
    if not safe:
        return ERROR_PATH_OUTSIDE_DIR
        
    if not os.path.exists(full_path):
        return ERROR_FILE_DOES_NOT_EXIST.format(path=path)
        
    try:
        if old_string == new_string:
            return ERROR_EDITING_FILE_IDENTICAL

        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        count = content.count(old_string)
        if count == 0:
            return ERROR_EDITING_FILE_NO_MATCH
        if count > 1:
            return ERROR_EDITING_FILE_MULTIPLE_MATCHES.format(count=count)
            
        new_content = content.replace(old_string, new_string)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        return f"success: updated {path}"
    except Exception as e:
        return ERROR_EDITING_FILE.format(error=str(e))

def delete_file(path):
    if path is None:
        return "Error: path argument is required"
    path = path.lstrip('/')
    safe, full_path = is_safe_path(path)
    if not safe:
        return ERROR_PATH_OUTSIDE_DIR
        
    if not os.path.exists(full_path):
        return ERROR_FILE_DOES_NOT_EXIST.format(path=path)
        
    try:
        os.remove(full_path)
        return f"success: deleted {path}"
    except Exception as e:
        return ERROR_DELETING_FILE.format(error=str(e))


def get_current_directory_structure():
    if os.getcwd() == os.path.expanduser("~"):
        return "Error: Currently on user home directory, not injecting file tree"
    return get_file_tree()

def list_files_recursive():
    file_list = []
    for root, dirs, files in os.walk(WORKING_DIR):
        # skip hidden stuff
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for f in files:
            if not f.startswith('.'):
                rel_path = os.path.relpath(os.path.join(root, f), WORKING_DIR)
                file_list.append(rel_path)
    return file_list

def normalize_call_syntax(call_str):
    """
    Normalizes LLM-generated tool calls to be valid Python syntax.
    Specifically handles multi-line strings using single/double quotes by
    converting them to triple-quoted strings.
    """
    def fix_quotes(m):
        quote_type = m.group(1)
        content = m.group(2)
        # If it's already triple-quoted, leave it alone
        if len(quote_type) == 3:
            return m.group(0)
        # If it's a single-line string, leave it alone
        if '\n' not in content:
            return m.group(0)
        # Upgrade multi-line single/double quoted string to triple-quoted
        return f"{quote_type*3}{content}{quote_type*3}"
        
    # Matches triple quotes or single/double quotes, correctly handling escaped quotes
    # group(1) is the quote delimiter, group(2) is the string content
    pattern = r'(\'\'\'|"""|\'|")(.*?(?<!\\)(?:\\\\)*)\1'
    return re.sub(pattern, fix_quotes, call_str, flags=re.DOTALL)


def repair_truncated_call(call_str):
    """
    Attempts to repair a truncated tool call by closing any open strings
    and parentheses.
    """
    depth = 0
    in_str = None
    escape = False
    
    i = 0
    while i < len(call_str):
        c = call_str[i]
        if escape:
            escape = False
            i += 1
            continue
        if c == '\\':
            escape = True
            i += 1
            continue
            
        if in_str is None:
            if call_str[i:i+3] in ("'''", '"""'):
                in_str = call_str[i:i+3]
                i += 3
                continue
            elif c in ("'", '"'):
                in_str = c
                i += 1
                continue
            elif c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
        elif in_str in ("'''", '"""'):
            if call_str[i:i+3] == in_str:
                in_str = None
                i += 3
                continue
        elif in_str in ("'", '"'):
            if c == in_str:
                in_str = None
        i += 1
    
    repaired = call_str
    if in_str:
        repaired += in_str
    
    while depth > 0:
        repaired += ")"
        depth -= 1
        
    return repaired


def parse_commands(text):
    valid_tools = {
        'read_file': {'args': ['path', 'start_line', 'end_line'], 'required': ['path']},
        'create_file': {'args': ['path', 'content'], 'required': ['path', 'content']},
        'edit_file': {'args': ['path', 'old_string', 'new_string'], 'required': ['path', 'old_string']},
        'delete_file': {'args': ['path'], 'required': ['path']},
        'get_current_directory_structure': {'args': [], 'required': []}
    }
    
    # Extract code blocks or use full text if no blocks but looks like tool call
    blocks = re.findall(r'```(?:[a-zA-Z0-9]*)\n(.*?)\n```', text, re.DOTALL)
    if not blocks:
        if any(re.search(rf"\b{tool}\s*\(", text) for tool in valid_tools):
            blocks = [text]
        else:
            return []

    unique_commands = []
    seen_originals = set()

    for block in blocks:
        for tool in valid_tools:
            # Find every instance of "tool_name("
            for match in re.finditer(rf"\b{tool}\s*\(", block):
                start_idx = match.start()
                # Find the matching closing parenthesis
                depth = 0
                in_str = None
                escape = False
                end_idx = -1
                
                i = start_idx
                while i < len(block):
                    c = block[i]
                    
                    if escape:
                        escape = False
                        i += 1
                        continue
                    if c == '\\':
                        escape = True
                        i += 1
                        continue
                        
                    if in_str is None:
                        if block[i:i+3] in ("'''", '"""'):
                            in_str = block[i:i+3]
                            i += 3
                            continue
                        elif c in ("'", '"'):
                            in_str = c
                            i += 1
                            continue
                        elif c == "(":
                            depth += 1
                        elif c == ")":
                            depth -= 1
                            if depth == 0:
                                end_idx = i + 1
                                break
                    elif in_str in ("'''", '"""'):
                        if block[i:i+3] == in_str:
                            in_str = None
                            i += 3
                            continue
                    elif in_str in ("'", '"'):
                        if c == in_str:
                            in_str = None
                    i += 1
                
                if end_idx != -1:
                    call_str = block[start_idx:end_idx]
                else:
                    # Truncated call? Let's try to repair it if it's at the end of the block
                    call_str = repair_truncated_call(block[start_idx:])
                
                try:
                    call_str_normalized = re.sub(rf"^{tool}\s*\(", f"{tool}(", call_str, count=1)
                    # Fix LLM multi-line string mistakes
                    call_str_normalized = normalize_call_syntax(call_str_normalized)
                    
                    # Use ast to safely extract arguments from the isolated call string
                    tree = ast.parse(call_str_normalized)
                    if isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Call):
                        node = tree.body[0].value
                        args = {}
                        arg_names = valid_tools[tool]['args']
                        required_args = valid_tools[tool]['required']
                        
                        for j, arg in enumerate(node.args):
                            if j < len(arg_names):
                                args[arg_names[j]] = ast.literal_eval(arg)
                        
                        for keyword in node.keywords:
                            args[keyword.arg] = ast.literal_eval(keyword.value)

                        # Check for missing required arguments
                        missing = [a for a in required_args if a not in args]
                        if missing:
                            raise ValueError(f"missing required arguments: {', '.join(missing)}")

                        # Deduplicate based on name and arguments to handle minor syntax differences
                        arg_items = tuple(sorted((k, str(v)) for k, v in args.items()))
                        call_key = (tool, arg_items)
                        
                        if call_key not in seen_originals:
                            unique_commands.append({
                                "name": tool,
                                "args": args,
                                "original": call_str
                            })
                            seen_originals.add(call_key)
                except Exception as e:
                    error_msg = f"invalid call: {str(e)}"
                    error_key = (tool, error_msg, call_str)
                    if error_key not in seen_originals:
                        unique_commands.append({
                            "name": tool,
                            "error": error_msg,
                            "original": call_str
                        })
                        seen_originals.add(error_key)
            
    return unique_commands
