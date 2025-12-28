import requests
import json
import sys
import time
import os
import uuid
import platform
import re
from . import tools, auth, config, interrupt, __version__
from .theme import Colors, Icons
from .stats import STATS

# Constants
BASE_URL = "http://localhost:1234/v1"
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
CODE_ASSIST_ENDPOINT = 'https://cloudcode-pa.googleapis.com'
CODE_ASSIST_API_VERSION = 'v1internal'
CEREBRAS_BASE_URL = "https://api.cerebras.ai/v1"
ANTHROPIC_BASE_URL = "https://api.anthropic.com/v1"
OPENAI_BASE_URL = "https://api.openai.com/v1"
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_CLOUD_BASE_URL = "https://ollama.com/v1"

# State
GEMINI_API_KEY = None
CEREBRAS_API_KEY = None
ANTHROPIC_API_KEY = None
OPENAI_API_KEY = None
OLLAMA_API_KEY = None
CURRENT_API = "lm_studio"
SHOW_REASONING = False

def get_user_agent(model_id="unknown"):
    os_name = platform.system().lower()
    arch = platform.machine().lower()
    return f"GeminiCLI/{__version__}/{model_id} ({os_name}; {arch})"

def _google_code_assist_request(endpoint, token, project_id=None, extra_payload=None):
    url = f"{CODE_ASSIST_ENDPOINT}/{CODE_ASSIST_API_VERSION}:{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": get_user_agent()
    }
    
    payload = {
        "metadata": {
            "ideType": "IDE_UNSPECIFIED",
            "platform": "PLATFORM_UNSPECIFIED",
            "pluginType": "GEMINI"
        }
    }
    if project_id:
        payload["cloudaicompanionProject"] = project_id
        payload["metadata"]["duetProject"] = project_id
        
    if extra_payload:
        payload.update(extra_payload)

    try:
        resp = requests.post(url, json=payload, headers=headers)
        if resp.status_code == 200:
            return resp.json()
        else:
            print(f"{endpoint} Error: {resp.status_code} - {resp.text}")
            return None
    except Exception as e:
        print(f"{endpoint} Exception: {e}")
        return None

def load_code_assist(token, project_id=None):
    return _google_code_assist_request("loadCodeAssist", token, project_id)

def onboard_user(token, tier_id, project_id=None):
    return _google_code_assist_request("onboardUser", token, project_id, {"tierId": tier_id})

def get_system_prompt():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    path = os.path.join(dir_path, "sysprompts", "main_sysprompt.txt")
    default = "You are a helpful assistant."
    
    content = default
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                content = f.read().strip()
        except Exception as e:
            print(f"\nerror reading sysprompt: {e}")
            
    if "<auto_inject_file_tree>" in content:
        if os.getcwd() == os.path.expanduser("~"):
            tree = "Currently on user home directory, not injecting file tree"
        else:
            tree = tools.get_file_tree()
        content = content.replace("<auto_inject_file_tree>", tree)
        
    return content

def set_api_config(api_type, api_key=None):
    global CURRENT_API, GEMINI_API_KEY, CEREBRAS_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY, OLLAMA_API_KEY
    CURRENT_API = api_type
    if api_type == "gemini": GEMINI_API_KEY = api_key
    elif api_type == "cerebras": CEREBRAS_API_KEY = api_key
    elif api_type == "anthropic": ANTHROPIC_API_KEY = api_key
    elif api_type == "openai": OPENAI_API_KEY = api_key
    elif api_type == "ollama": OLLAMA_API_KEY = api_key

def get_gemini_models():
    return ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.5-flash-lite", "gemini-3-flash-preview", "gemini-3-pro-preview", "custom"]

def get_cerebras_models():
    return ["llama3.1-8b", "llama-3.3-70b", "gpt-oss-120b", "qwen-3-32b", "custom"]

def get_anthropic_models():
    return [
        "claude-opus-4-5-20251101", "claude-sonnet-4-5-20250929", "claude-haiku-4-5-20251001",
        "claude-4-5-opus-latest", "claude-4-5-sonnet-latest", "claude-4-5-haiku-latest",
        "claude-4-opus-latest", "claude-4-sonnet-latest", "claude-3-7-sonnet-latest",
        "claude-3-5-sonnet-latest", "claude-3-5-haiku-latest", "claude-3-opus-latest", "custom"
    ]

def get_openai_models():
    return [
        "gpt-5.2-pro", "gpt-5.2-thinking", "gpt-5.2-instant", "gpt-5", "gpt-5-chat",
        "gpt-5-mini", "gpt-5-nano", "o4-mini", "o4-mini-high", "o3", "o3-mini",
        "o3-pro", "o1", "o1-mini", "o1-pro", "o1-preview", "gpt-4.5", "gpt-4o",
        "gpt-4o-mini", "custom"
    ]

def get_ollama_models():
    cloud_models = ["gpt-oss:120b-cloud", "gpt-oss:20b-cloud", "qwen3-coder:480b-cloud", "qwen3-vl:235b-cloud"]
    local_models = []
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
        if resp.status_code == 200:
            local_models = [m.get('name') for m in resp.json().get('models', [])]
    except:
        pass
    return cloud_models + local_models + ["custom"]

def get_models():
    model_funcs = {
        "gemini": get_gemini_models,
        "cerebras": get_cerebras_models,
        "anthropic": get_anthropic_models,
        "openai": get_openai_models,
        "ollama": get_ollama_models
    }
    
    if CURRENT_API in model_funcs:
        return [{"id": model, "context_length": "N/A", "size": 0} for model in model_funcs[CURRENT_API]()]
    else:
        try:
            resp = requests.get(f"{BASE_URL}/models")
            resp.raise_for_status()
            return resp.json()['data']
        except:
            print("lm studio server dead, start it up pls")
            sys.exit(1)

def load_model_and_verify(model_id):
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": "hello"}],
        "stream": True,
        "max_tokens": 1
    }
    try:
        with requests.post(f"{BASE_URL}/chat/completions", json=payload, stream=True) as r:
            for line in r.iter_lines():
                if line and line.decode('utf-8').startswith("data: "):
                    return True
        return False
    except Exception:
        return False

# --- Parsers ---

def _parse_openai_chunk(line_str):
    if not line_str.startswith("data: "):
        return "", "", False
    content_json = line_str[6:]
    if content_json.strip() == "[DONE]":
        return "", "", True
    try:
        chunk = json.loads(content_json)
        if 'choices' in chunk and len(chunk['choices']) > 0:
            delta_obj = chunk['choices'][0]['delta']
            # Support multiple reasoning field names (reasoning_content, reasoning, or new structured fields)
            reasoning = delta_obj.get('reasoning_content') or delta_obj.get('reasoning')
            if not reasoning and 'reasoning_summary_text' in delta_obj:
                reasoning = delta_obj['reasoning_summary_text'].get('delta', '')
                
            return delta_obj.get('content', '') or '', reasoning or '', False
    except json.JSONDecodeError:
        pass
    return "", "", False

def _parse_anthropic_chunk(line_str):
    if not line_str.startswith("data: "):
        return "", "", False
    content = line_str[6:]
    try:
        chunk = json.loads(content)
        if chunk['type'] == 'content_block_delta':
            delta = chunk['delta']
            d_type = delta.get('type')
            if d_type == 'text_delta':
                return delta.get('text', ''), "", False
            elif d_type == 'thinking_delta':
                return "", delta.get('thinking', ''), False
            elif 'text' in delta: # Fallback for older formats
                return delta.get('text', ''), "", False
        elif chunk['type'] == 'message_stop':
            return "", "", True
    except (json.JSONDecodeError, KeyError):
        pass
    return "", "", False

def _parse_gemini_chunk(line_str):
    if not line_str.startswith("data: "):
        return "", "", False
    content = line_str[6:]
    if content.strip() == "[DONE]":
        return "", "", True
    try:
        chunk = json.loads(content)
        if 'candidates' in chunk:
            text = ""
            for candidate in chunk['candidates']:
                if 'content' in candidate and 'parts' in candidate['content']:
                    for part in candidate['content']['parts']:
                        text += part.get('text', '')
            return text, "", False
    except json.JSONDecodeError:
        pass
    return "", "", False

def _process_stream_ui(response, parser_func, line_generator=None):
    """Process streaming response and display to terminal."""
    VALID_TOOLS = ['read_file', 'create_file', 'edit_file', 'delete_file', 'get_current_directory_structure']
    
    # State tracking
    buffer = ""
    in_tool_call = False
    current_tool = None
    processed_idx = 0
    
    start_time = time.time()
    first_token = True
    
    # Styling
    AI_COLOR = "\033[38;5;141m"
    TOOL_COLOR = "\033[38;5;214m" # Orange-ish for tools
    THINK_COLOR = "\033[38;5;213m"
    DIM = "\033[90m"
    RESET = "\033[0m"
    
    ai_prefix = f"{Colors.SECONDARY}{Icons.DIAMOND}{Colors.RESET} "
    # print(ai_prefix, end="", flush=True) # Now printed by stream_chat for immediate feedback
    
    iterator = line_generator(response) if line_generator else response.iter_lines()
    
    full_response = ""
    full_reasoning = ""
    thinking_duration = 0
    is_thinking = False
    thinking_via_tag = False
    thinking_start = 0
    check_for_think = True
    
    def check_tool_start(text):
        """Check if text contains a potential tool start."""
        for tool in VALID_TOOLS:
            # Look for tool start. Case-insensitive.
            # We allow it to start anywhere (no prefix required) to be safe.
            match = re.search(rf"(^|[\s`]|```[a-zA-Z0-9]*\n)({tool})\s*\(", text, re.IGNORECASE)
            if match:
                hide_start = match.start()
                tool_name_start = match.start(2)
                # We return the tool name as defined in VALID_TOOLS
                return tool, hide_start, tool_name_start
        
        # Check for partial matches at the end of text to buffer.
        # We buffer if it looks like it's starting a tool call.
        text_lower = text.lower()
        potential_prefixes = ["```", "```python", "```python\n"]
        for tool in VALID_TOOLS:
            potential_prefixes.append(tool)
            potential_prefixes.append(tool + "(")
            
        for p in potential_prefixes:
            for i in range(len(p), 0, -1):
                if text_lower.endswith(p[:i].lower()):
                    return None, -1, -1
        return False, 0, 0

    def get_tool_path(text):
        """Extract path argument from tool call string."""
        match = re.search(r'path=["\']([^"\']+)["\']', text)
        if match:
            return match.group(1)
        return None

    def is_tool_complete(text, tool_start_idx):
        """Check if the tool call starting at tool_start_idx is complete using balanced parens."""
        depth = 0
        in_str = None
        escape = False
        
        # Start searching from the tool name start
        i = tool_start_idx + len(current_tool)
        while i < len(text):
            c = text[i]
            
            if escape:
                escape = False
                i += 1
                continue
            if c == '\\':
                escape = True
                i += 1
                continue
                
            if in_str is None:
                if text[i:i+3] in ('"""', "'''"):
                    in_str = text[i:i+3]
                    i += 3
                    continue
                elif c in ("'", '"'):
                    in_str = c
                    i += 1
                    continue
            elif in_str in ('"""', "'''"):
                if text[i:i+3] == in_str:
                    in_str = None
                    i += 3
                    continue
            elif in_str in ("'", '"'):
                if c == in_str:
                    in_str = None
            
            if in_str is None:
                if c == "(":
                    depth += 1
                elif c == ")":
                    depth -= 1
                    if depth == 0:
                        # Found end of tool call. Check if it's followed by markdown closing
                        end_pos = i + 1
                        remaining = text[end_pos:]
                        if remaining.startswith("\n```"):
                            return end_pos + 4
                        elif remaining.startswith("```"):
                            return end_pos + 3
                        return end_pos
            i += 1
        return -1

    last_status_len = 0
    hide_start_idx = -1
    tool_name_idx = -1

    for line in iterator:
        if not line: continue

        decoded = line.decode('utf-8') if isinstance(line, bytes) else line
        text_delta, reasoning_delta, is_done = parser_func(decoded)
        
        # Handle Reasoning/Thinking
        if reasoning_delta:
            full_reasoning += reasoning_delta
            if not is_thinking:
                is_thinking = True
                thinking_via_tag = False
                thinking_start = time.time()
                # Clear any partial tool text if we jumped to thinking
                if buffer: 
                    print(buffer, end="", flush=True)
                    buffer = ""
                if SHOW_REASONING:
                    print()
            
            if SHOW_REASONING:
                print(f"{DIM}{reasoning_delta}{RESET}", end="", flush=True)
            else:
                elapsed = time.time() - thinking_start
                print(f"\r{ai_prefix}{THINK_COLOR}[Thinking... {elapsed:.0f}s]{RESET}\033[K", end="", flush=True)
            continue
            
        if not text_delta: continue
        
        # Handle end of thinking
        if is_thinking and not thinking_via_tag and not reasoning_delta:
            is_thinking = False
            duration = time.time() - thinking_start
            thinking_duration = duration
            if SHOW_REASONING:
                print(f"\n{ai_prefix}", end="", flush=True)
            else:
                print(f"\r{ai_prefix}{DIM}[Thought for {duration:.0f}s]{RESET}\033[K")
            
        full_response += text_delta
        buffer += text_delta

        # <think> tag handling
        if is_thinking and thinking_via_tag:
            full_reasoning += text_delta
            if SHOW_REASONING:
                print(f"{DIM}{text_delta}{RESET}", end="", flush=True)
            else:
                elapsed = time.time() - thinking_start
                print(f"\r{ai_prefix}{THINK_COLOR}[Thinking... {elapsed:.0f}s]{RESET}\033[K", end="", flush=True)
            
            if "</think>" in buffer:
                is_thinking = False
                thinking_via_tag = False
                duration = time.time() - thinking_start
                thinking_duration = duration
                if SHOW_REASONING:
                    print(f"\n{ai_prefix}", end="", flush=True)
                else:
                    print(f"\r{ai_prefix}{DIM}[Thought for {duration:.0f}s]{RESET}\033[K")
                _, post = buffer.split("</think>", 1)
                buffer = post
            else:
                continue

        elif not is_thinking and (check_for_think or CURRENT_API == "lm_studio"):
            if "<think>" in buffer:
                is_thinking = True
                thinking_via_tag = True
                thinking_start = time.time()
                check_for_think = False
                pre, post = buffer.split("<think>", 1)
                if pre: print(pre, end="", flush=True)
                buffer = post
                continue
            
            is_partial = False
            for i in range(1, 7):
                if buffer.endswith("<think>"[:i]):
                    is_partial = True
                    break
            if is_partial: continue
            if not CURRENT_API == "lm_studio": check_for_think = False

        # --- Tool Call Detection & Streaming ---
        if not is_thinking:
            if not in_tool_call:
                tool, s_idx, t_idx = check_tool_start(buffer)
                
                if tool:
                    # Found a valid tool!
                    in_tool_call = True
                    current_tool = tool
                    hide_start_idx = s_idx
                    tool_name_idx = t_idx
                    
                    # Print everything before the tool block and REMOVE it from buffer
                    pre_tool = buffer[:hide_start_idx]
                    if pre_tool:
                        print(pre_tool, end="", flush=True)
                    
                    # Buffer now only contains the beginning of the tool block
                    buffer = buffer[hide_start_idx:]
                    
                    # Determine friendly action name
                    action_map = {
                        'create_file': "Creating",
                        'edit_file': "Editing",
                        'delete_file': "Deleting",
                        'read_file': "Reading",
                        'get_current_directory_structure': "Scanning directory"
                    }
                    action = action_map.get(tool, "Running")

                    status = f"  {TOOL_COLOR}> {action}...{RESET}"
                    print(f"\n{status}", end="", flush=True)
                    last_status_len = len(status) - len(TOOL_COLOR) - len(RESET)
                elif s_idx == -1:
                    # Potential tool start detected at the end of buffer, wait for more data
                    continue
                else:
                    # No tool start and no potential start, print and clear buffer
                    print(buffer, end="", flush=True)
                    buffer = ""

            else:
                # We ARE in a tool call
                rel_tool_name_idx = tool_name_idx - hide_start_idx
                end_idx = is_tool_complete(buffer, rel_tool_name_idx)
                
                # Update status
                path = get_tool_path(buffer)
                path_str = f" {path}" if path else ""
                
                action_map = {
                    'create_file': "Creating",
                    'edit_file': "Editing",
                    'delete_file': "Deleting",
                    'read_file': "Reading",
                    'get_current_directory_structure': "Scanning directory"
                }
                action = action_map.get(current_tool, "Running")
                
                status_line = f"\r{TOOL_COLOR}> {action}{path_str}...{RESET}"
                padding = " " * max(0, last_status_len - len(status_line) + 10) 
                print(f"{status_line}{padding}", end="", flush=True)
                last_status_len = len(status_line)

                if end_idx != -1:
                    # Found the end of the tool call!
                    in_tool_call = False
                    current_tool = None
                    print("\r\033[K", end="") # Clear the status line
                    
                    # We return the FULL response so main.py can parse it.
                    # Hiding from history DISPLAY is handled in ui.py.
                    return full_response, full_reasoning, thinking_duration
                    
        if is_done:
            break
                    
    if buffer:
        if in_tool_call:
            # We are at the end of stream but tool call is still open.
            # Don't print it! Let main.py try to parse it as is.
            print("\r\033[K", end="")
        else:
            print(buffer, end="", flush=True)
    
    print("\n")
    return full_response, full_reasoning, thinking_duration

def _generic_chat_stream(url, headers, payload, parser_func, line_generator=None):
    """Make streaming API request and handle response."""
    try:
        with requests.post(url, json=payload, stream=True, headers=headers) as r:
            if r.status_code != 200:
                print(f"\n\033[91mAPI Error: {r.status_code} - {r.text}\033[0m")
                return None
            return _process_stream_ui(r, parser_func, line_generator)
    except KeyboardInterrupt:
        if interrupt.should_quit(): sys.exit(0)
        print("\033[38;5;213m\nGeneration cancelled\033[0m")
        return None
    except Exception as e:
        print(f"\n\033[91mAPI Error: {e}\033[0m")
        return None

def stream_chat_anthropic(model_id, messages):
    system_prompt = ""
    anthropic_messages = []
    for msg in messages:
        if msg['role'] == 'system': system_prompt = msg['content']
        else: anthropic_messages.append({"role": msg['role'], "content": msg['content']})

    payload = {
        "model": model_id, "max_tokens": 4096, "messages": anthropic_messages, "stream": True
    }
    if system_prompt: payload["system"] = system_prompt

    headers = {
        "x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"
    }
    return _generic_chat_stream(f"{ANTHROPIC_BASE_URL}/messages", headers, payload, _parse_anthropic_chunk)

def stream_chat_openai(model_id, messages):
    payload = {"model": model_id, "messages": messages, "stream": True}
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    return _generic_chat_stream(f"{OPENAI_BASE_URL}/chat/completions", headers, payload, _parse_openai_chunk)

def stream_chat_ollama(model_id, messages):
    payload = {"model": model_id, "messages": messages, "stream": True}
    is_cloud = "cloud" in model_id.lower()
    url = f"{OLLAMA_CLOUD_BASE_URL}/chat/completions" if is_cloud else f"{OLLAMA_BASE_URL}/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    if OLLAMA_API_KEY: headers["Authorization"] = f"Bearer {OLLAMA_API_KEY}"
    return _generic_chat_stream(url, headers, payload, _parse_openai_chunk)

def stream_chat_cerebras(model_id, messages):
    payload = {"model": model_id, "messages": messages, "stream": True}
    headers = {"Authorization": f"Bearer {CEREBRAS_API_KEY}", "Content-Type": "application/json"}
    return _generic_chat_stream(f"{CEREBRAS_BASE_URL}/chat/completions", headers, payload, _parse_openai_chunk)

def stream_chat_gemini(model_id, messages):
    if config.is_using_google_auth(): return stream_chat_gemini_oauth(model_id, messages)
    
    contents = []
    system_instruction = None
    for msg in messages:
        if msg['role'] == 'system': system_instruction = msg['content']
        elif msg['role'] == 'user': contents.append({"role": "user", "parts": [{"text": msg['content']}]})
        elif msg['role'] == 'assistant': contents.append({"role": "model", "parts": [{"text": msg['content']}]})

    payload = {"contents": contents}
    if system_instruction: payload["system_instruction"] = {"parts": [{"text": system_instruction}]}
    
    url = f"{GEMINI_BASE_URL}/models/{model_id}:streamGenerateContent?key={GEMINI_API_KEY}&alt=sse"
    return _generic_chat_stream(url, {}, payload, _parse_gemini_chunk)

def stream_chat_gemini_oauth(model_id, messages):
    token = auth.get_auth_token()
    if not token:
        print("\033[91mNo Google Auth token found. Please login first using '/login'.\033[0m")
        return None

    project_id = os.environ.get('GOOGLE_CLOUD_PROJECT') or os.environ.get('GOOGLE_CLOUD_PROJECT_ID') or config.get_google_cloud_project()
    if not project_id:
        print("\033[91mGoogle Cloud Project ID is required. Set it in /gemini-auth-mode.\033[0m")
        return None

    contents = []
    system_instruction = None
    for msg in messages:
        if msg['role'] == 'system': system_instruction = {"parts": [{"text": msg['content']}]}
        elif msg['role'] == 'user': contents.append({"role": "user", "parts": [{"text": msg['content']}]})
        elif msg['role'] == 'assistant': contents.append({"role": "model", "parts": [{"text": msg['content']}]})

    clean_model_id = model_id[7:] if model_id.startswith('models/') else model_id
    payload = {
        "model": clean_model_id,
        "user_prompt_id": str(uuid.uuid4()),
        "request": {"contents": contents}
    }
    if project_id: payload["project"] = project_id
    if system_instruction: payload["request"]["systemInstruction"] = system_instruction

    url = f"{CODE_ASSIST_ENDPOINT}/{CODE_ASSIST_API_VERSION}:streamGenerateContent?alt=sse"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": get_user_agent(clean_model_id)
    }

    def smart_oauth_generator(response):
        buffered_lines = []
        for line in response.iter_lines():
            if not line:
                if buffered_lines:
                    yield "\n".join(buffered_lines)
                    buffered_lines = []
                continue
            decoded = line.decode('utf-8')
            if decoded.startswith("data: "):
                buffered_lines.append(decoded[6:].strip())
            elif decoded.strip() == "[DONE]":
                break

    def smart_oauth_parser(json_str):
        try:
            chunk = json.loads(json_str)
            candidate_source = chunk.get('response', chunk)
            text = ""
            if 'candidates' in candidate_source:
                for candidate in candidate_source['candidates']:
                    if 'content' in candidate and 'parts' in candidate['content']:
                        for part in candidate['content']['parts']:
                            text += part.get('text', '')
            return text, "", False
        except json.JSONDecodeError:
            pass
        return "", "", False

    return _generic_chat_stream(url, headers, payload, smart_oauth_parser, smart_oauth_generator)

def stream_chat(model_id, messages):
    start_time = time.time()
    response = None
    reasoning = ""
    thinking_duration = 0
    
    # Immediate feedback
    ai_prefix = f"{Colors.SECONDARY}{Icons.DIAMOND}{Colors.RESET} "
    print(ai_prefix, end="", flush=True)
    
    # Disable typing during generation
    interrupt.set_echo(False)
    
    try:
        if CURRENT_API == "gemini": 
            res = stream_chat_gemini(model_id, messages)
        elif CURRENT_API == "cerebras": 
            res = stream_chat_cerebras(model_id, messages)
        elif CURRENT_API == "anthropic": 
            res = stream_chat_anthropic(model_id, messages)
        elif CURRENT_API == "openai": 
            res = stream_chat_openai(model_id, messages)
        elif CURRENT_API == "ollama": 
            res = stream_chat_ollama(model_id, messages)
        else:
            payload = {"model": model_id, "messages": messages, "stream": True}
            res = _generic_chat_stream(f"{BASE_URL}/chat/completions", {}, payload, _parse_openai_chunk)
        
        if isinstance(res, tuple):
            if len(res) == 3:
                response, reasoning, thinking_duration = res
            else:
                response, reasoning = res
        else:
            response = res
            
    finally:
        # Re-enable typing and clear any buffered input
        interrupt.flush_input()
        interrupt.set_echo(True)
        
        if response:
            duration = time.time() - start_time
            STATS.record_request(model_id, duration)
            
    return response, reasoning, thinking_duration