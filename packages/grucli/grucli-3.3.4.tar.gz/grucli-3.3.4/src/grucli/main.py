import sys
import re
import os
import atexit
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.lexers import Lexer
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from . import api
from . import commands
from . import handlers
from . import tools
from . import config
from . import auth
from . import interrupt
from . import ui
from . import permissions
from .theme import Colors, Icons, Styles, Borders
from .stats import STATS


def get_yn_input(prompt):
    """Get yes/no input."""
    while True:
        try:
            choice = interrupt.prompt_input(f"{Colors.INPUT_CONFIRM}{prompt}{Colors.RESET}").strip().lower()
            if choice in ['y', 'n']:
                return choice
            print(f"{Colors.ERROR}Enter y or n{Colors.RESET}")
        except KeyboardInterrupt:
            interrupt.handle_interrupt()
            raise interrupt.BackSignal()


def get_api_key_for_provider(api_type):
    """Get API key from config or user input."""
    api_name = api_type.capitalize()
    
    if api_type == 'gemini' and config.is_using_google_auth():
        token = auth.get_auth_token()
        if not token:
            print(f"\n{Colors.WARNING}Google Auth enabled but not logged in{Colors.RESET}")
            try:
                print(f"\n  {Colors.SUCCESS}1{Colors.RESET}) Login now")
                print(f"  {Colors.ERROR}2{Colors.RESET}) Cancel")
                choice = interrupt.prompt_input(f"\n{Colors.INPUT_ACTIVE}Choice: {Colors.RESET}").strip()
            except KeyboardInterrupt:
                interrupt.handle_interrupt()
                raise interrupt.BackSignal()
            
            if choice == '1':
                try:
                    auth.perform_oauth_login()
                    token = auth.get_auth_token()
                except Exception as e:
                    print(f"{Colors.ERROR}Login failed: {e}{Colors.RESET}")
                    sys.exit(1)
            else:
                print(f"{Colors.MUTED}Authentication required{Colors.RESET}")
                sys.exit(1)
        
        print(f"\n{Colors.INFO}Checking onboarding...{Colors.RESET}")
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT') or os.environ.get('GOOGLE_CLOUD_PROJECT_ID') or config.get_google_cloud_project()
        
        load_res = api.load_code_assist(token, project_id)
        if not load_res:
            print(f"{Colors.WARNING}Could not load status{Colors.RESET}")
            tier_id = 'FREE'
        else:
            current_tier = load_res.get('currentTier', {})
            tier_id = current_tier.get('id', 'FREE')
            
            if load_res.get('cloudaicompanionProject'):
                project_id = load_res['cloudaicompanionProject']
                config.set_google_cloud_project(project_id)
        
        if not project_id:
            if tier_id == 'FREE':
                print(f"{Colors.MUTED}Onboarding to FREE tier...{Colors.RESET}")
                onboard_res = api.onboard_user(token, 'FREE')
                if onboard_res and onboard_res.get('done'):
                    project_id = onboard_res.get('response', {}).get('cloudaicompanionProject', {}).get('id')
                    if project_id:
                        config.set_google_cloud_project(project_id)
                elif onboard_res:
                    print(f"{Colors.WARNING}Onboarding in progress, try again shortly{Colors.RESET}")
            
            if not project_id:
                print(f"\n{Colors.WARNING}Project ID required{Colors.RESET}")
                try:
                    project_id = interrupt.prompt_input(f"{Colors.INPUT_ACTIVE}Project ID (or Enter to skip): {Colors.RESET}").strip()
                except KeyboardInterrupt:
                    interrupt.handle_interrupt()
                    raise interrupt.BackSignal()
                if project_id:
                    config.set_google_cloud_project(project_id)
        
        print(f"\n{Colors.SUCCESS}{Icons.CHECK} Authenticated ({tier_id}, {project_id or 'Managed'}){Colors.RESET}")
        return None

    saved_api_key = None
    if config.has_saved_api_key(api_type):
        print(f"\n{Colors.INFO}Found saved {api_name} key{Colors.RESET}")
        use_saved = get_yn_input("Use saved key? (y/n): ")
        if use_saved == 'y':
            saved_api_key = config.load_decrypted_api_key(api_type)
            if saved_api_key:
                print(f"{Colors.SUCCESS}{Icons.CHECK} Using saved key{Colors.RESET}")
                return saved_api_key
            else:
                print(f"{Colors.ERROR}Failed to load key{Colors.RESET}")

    print(f"\n{Colors.MUTED}Enter {api_name} API key:{Colors.RESET}")
    try:
        api_key = interrupt.prompt_input(f"{Colors.INPUT_ACTIVE}> {Colors.RESET}").strip()
    except KeyboardInterrupt:
        interrupt.handle_interrupt()
        raise interrupt.BackSignal()
    
    if not api_key:
        print(f"{Colors.ERROR}No key provided{Colors.RESET}")
        sys.exit(1)

    save_choice = get_yn_input("Save key? (y/n): ")
    if save_choice == 'y':
        try:
            config.save_encrypted_api_key(api_key, api_type)
            print(f"{Colors.SUCCESS}{Icons.CHECK} Saved{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.ERROR}Save failed: {e}{Colors.RESET}")

    return api_key


def select_api_ui():
    """Display API provider selection menu."""
    while True:
        try:
            title = 'Select API Provider'
            options = [
                ('class:option', 'OpenAI'),
                ('class:option', 'Anthropic'),
                ('class:cloud', 'Gemini (Google Auth)'),
                ('class:option', 'Gemini (API Key)'),
                ('class:option', 'Ollama'),
                ('class:option', 'LM Studio'),
                ('class:option', 'Cerebras'),
            ]
            _, index = ui.select_option(options, title, is_root=True)

            if index == 0:
                return "openai", get_api_key_for_provider("openai")
            elif index == 1:
                return "anthropic", get_api_key_for_provider("anthropic")
            elif index == 2:
                config.set_use_google_auth(True)
                return "gemini", get_api_key_for_provider("gemini")
            elif index == 3:
                config.set_use_google_auth(False)
                return "gemini", get_api_key_for_provider("gemini")
            elif index == 4:
                return "ollama", None
            elif index == 5:
                return "lm_studio", None
            elif index == 6:
                return "cerebras", get_api_key_for_provider("cerebras")
        except interrupt.BackSignal:
            interrupt.clear_bottom_warning()
            continue
        except KeyboardInterrupt:
            interrupt.handle_interrupt()


def select_model_ui(skip_loading=False):
    """Display model selection."""
    while True:
        try:
            models = api.get_models()

            options = [{"label": m.get('id', 'unknown'), "id": m.get('id', 'unknown')} for m in models]
            
            ui_options = []
            for o in options:
                label = o['label']
                if api.CURRENT_API == "ollama" and "cloud" in label.lower():
                    ui_options.append(('class:cloud', label))
                else:
                    ui_options.append(label)

            _, index = ui.select_option(ui_options, 'Select Model')
            selected_model = options[index]['id']

            if selected_model == "custom":
                print(f"\n{Colors.MUTED}Model name:{Colors.RESET}")
                try:
                    selected_model = interrupt.prompt_input(f"{Colors.INPUT_ACTIVE}> {Colors.RESET}").strip()
                except KeyboardInterrupt:
                    interrupt.handle_interrupt()
                    raise interrupt.BackSignal()
                    
                if not selected_model:
                    print(f"{Colors.WARNING}No model specified{Colors.RESET}")
                    continue

            is_cloud = api.CURRENT_API in ["gemini", "cerebras", "anthropic", "openai"]
            if api.CURRENT_API == "ollama" and "cloud" in selected_model.lower():
                is_cloud = True
            
            if api.CURRENT_API == "ollama" and is_cloud and not api.OLLAMA_API_KEY:
                key = get_api_key_for_provider("ollama")
                api.set_api_config("ollama", key)

            if skip_loading or is_cloud:
                return selected_model

            spinner = ui.Spinner(f"Loading {selected_model}")
            spinner.start()

            try:
                api.load_model_and_verify(selected_model)
                spinner.stop()
                return selected_model

            except KeyboardInterrupt:
                spinner.stop()
                if interrupt.should_quit():
                    sys.exit(0)
                print(f"\n{Colors.WARNING}Cancelled{Colors.RESET}")
                continue

        except KeyboardInterrupt:
            interrupt.handle_interrupt()
            raise interrupt.BackSignal()


def get_tool_category(tool_name: str) -> str:
    """Get display category for a tool."""
    group = permissions.get_tool_permission_group(tool_name)
    if group == permissions.PermissionGroup.READ:
        return "read"
    elif group == permissions.PermissionGroup.WRITE:
        return "write"
    elif group == permissions.PermissionGroup.DESTRUCTIVE:
        return "destructive"
    return "read"


def execute_tool(cmd):
    """Execute a tool command."""
    name = cmd['name']
    args = cmd['args']
    
    try:
        result = None
        if name == 'read_file':
            result = tools.read_file(args.get('path'), args.get('start_line'), args.get('end_line'))
        elif name == 'create_file':
            result = tools.create_file(args.get('path'), args.get('content'))
        elif name == 'edit_file':
            result = tools.edit_file(args.get('path'), args.get('old_string'), args.get('new_string'))
        elif name == 'delete_file':
            result = tools.delete_file(args.get('path'))
        elif name == 'get_current_directory_structure':
            result = tools.get_current_directory_structure()
        else:
            result = "error: unknown tool"
    except Exception as e:
        result = f"Error: execution failed: {str(e)}"
    
    success = not result.startswith("Error") and not result.startswith("error")
    STATS.record_tool_call(success)
    return result


def process_tool_calls(cmds, state):
    """Process tool calls with permissions."""
    all_results = []
    denied = False
    total = len(cmds)
    
    for i, cmd in enumerate(cmds):
        if denied:
            break
            
        name = cmd['name']
        
        if 'error' in cmd:
            print(f"\n{Colors.ERROR}{Icons.CROSS} Tool call invalid:{Colors.RESET}")
            print(f"{Colors.MUTED}{cmd['original']}{Colors.RESET}")
            print(f"{Colors.ERROR}{cmd['error']}{Colors.RESET}")
            all_results.append(f"Result of `{cmd['original']}`:\n{cmd['error']}")
            continue
            
        args = cmd['args']
        category = get_tool_category(name)
        
        print()
        if total > 1:
            print(f"{Colors.MUTED}[{i + 1}/{total}]{Colors.RESET}")
        
        print(ui.format_tool_call_block(name, args, category))
        
        if name == 'edit_file' and 'old_string' in args:
            print(ui.format_diff(
                args.get('old_string', ''),
                args.get('new_string', ''),
                args.get('path', 'unknown')
            ))
        
        allowed, decision = permissions.check_permission(name, args)
        
        if not allowed:
            denied = True
            state['messages'].append({"role": "user", "content": "Tool execution denied by user."})
            break
        
        path = args.get('path', '')
        action_map = {
            'create_file': f"Creating {path}",
            'edit_file': f"Editing {path}",
            'delete_file': f"Deleting {path}",
            'read_file': f"Reading {path}",
            'get_current_directory_structure': "Scanning"
        }
        action_msg = action_map.get(name, f"Running {name}")
        
        print(f"{Colors.MUTED}{action_msg}...{Colors.RESET}", end=" ", flush=True)
        result = execute_tool(cmd)
        
        if result.startswith("Error") or result.startswith("error"):
            print(f"{Colors.ERROR}{Icons.CROSS} {result}{Colors.RESET}")
        else:
            display_result = result if len(result) < 150 else result[:147] + "..."
            print(f"{Colors.SUCCESS}{Icons.CHECK} {display_result}{Colors.RESET}")
        
        all_results.append(f"Result of `{cmd['original']}`:\n{result}")
    
    if all_results:
        return "\n\n".join(all_results)
    return None


class MentionLexer(Lexer):
    """Lexer that highlights @file mentions in purple."""
    
    def lex_document(self, document):
        def get_line(lineno):
            line = document.lines[lineno]
            tokens = []
            last_idx = 0
            for match in re.finditer(r'@[^\s]+', line):
                start, end = match.start(), match.end()
                if start > last_idx:
                    tokens.append(('', line[last_idx:start]))
                tokens.append(('class:mention', line[start:end]))
                last_idx = end
            if last_idx < len(line):
                tokens.append(('', line[last_idx:]))
            return tokens
        return get_line


def get_status_bar(state):
    """Generate status bar content."""
    width = ui.get_terminal_width()
    cwd_text = f"~/{os.path.basename(os.getcwd())}"
    
    provider_text = api.CURRENT_API.upper()
    model_name = state.get('current_model', 'unknown')
    model_text = f"{provider_text}: {model_name}"
    
    if len(model_text) > 35:
        model_text = model_text[:32] + "..."
    
    is_accepting_edits = permissions.PERMISSION_STORE.is_allowed(permissions.PermissionGroup.WRITE)
    center_html = ""
    center_len = 0
    if is_accepting_edits:
        center_text = "ACCEPTING EDITS"
        center_html = f'<style fg="#F3E5AB">{center_text}</style>'
        center_len = len(center_text)
    
    warning_line = ""
    if state.get('toolbar') and "ctrl+c" in str(state['toolbar']).lower():
        warning_text = interrupt.get_quit_hint()
        warning_line = f'<style fg="#F3E5AB">{warning_text}</style>\n'
    
    if center_len > 0:
        pad_left_len = max(1, (width // 2 - center_len // 2) - len(cwd_text))
        pad_right_len = max(1, width - len(cwd_text) - pad_left_len - center_len - len(model_text))
        
        bottom_line = (
            f'<style fg="#8a8a8a">{cwd_text}</style>'
            f'{" " * pad_left_len}{center_html}{" " * pad_right_len}'
            f'<style fg="#af5fff">{model_text}</style>'
        )
    else:
        padding_len = max(1, width - len(cwd_text) - len(model_text))
        
        bottom_line = (
            f'<style fg="#8a8a8a">{cwd_text}</style>'
            f'{" " * padding_len}'
            f'<style fg="#af5fff">{model_text}</style>'
        )
        
    return HTML(f"{warning_line}{bottom_line}")


def start_chat(initial_model_id):
    """Main chat loop."""
    os.system('cls' if os.name == 'nt' else 'clear')
    
    ui.print_ascii_art()
    
    config.prune_history(config.get_history_file_path(), 25)
    sys_prompt = api.get_system_prompt()
    state = {
        "messages": [{"role": "system", "content": sys_prompt}],
        "toolbar": None,
        "current_model": initial_model_id
    }
    
    permissions.PERMISSION_STORE.reset()
    
    bindings = handlers.get_chat_bindings(state)
    
    chat_style = Style.from_dict({
        'mention': '#af5fff',
        'prompt_prefix': '#0087ff',
        'bottom-toolbar': 'bg:default #8a8a8a',
        'completion-menu.completion': 'bg:#2c2c2c #bcbcbc',
        'completion-menu.completion.current': 'bg:#5f5faf #ffffff',
        'completion-menu.meta.completion': 'bg:#2c2c2c #8a8a8a',
        'completion-menu.meta.completion.current': 'bg:#5f5faf #ffffff',
        'completion-menu.multi-column-meta': 'bg:#2c2c2c #bcbcbc',
    })
    
    session = PromptSession(
        completer=commands.completer,
        lexer=MentionLexer(),
        style=chat_style,
        key_bindings=bindings,
        bottom_toolbar=lambda: get_status_bar(state),
        complete_while_typing=True,
        history=FileHistory(config.get_history_file_path())
    )
    
    if os.getcwd() == os.path.expanduser("~"):
        print(f"\033[38;2;243;229;171m{Icons.WARNING} Running in home directory is not recommended\033[0m")
    
    ui.print_tips()
    print(f"{Colors.SUCCESS}{Icons.CHECK} Connected to {Colors.SECONDARY}{state['current_model']}{Colors.RESET}")
    print()
    
    while True:
        try:
            user_input = session.prompt([('class:prompt_prefix', '> ')])
            
            if not user_input.strip():
                continue

            if user_input.startswith('/'):
                result = commands.handle_command(user_input, state)
                if result == "exit":
                    break
                if result == "select_model":
                    new_model = select_model_ui(skip_loading=(api.CURRENT_API in ["gemini", "cerebras", "anthropic", "openai"]))
                    state['current_model'] = new_model
                    print(f"\n{Colors.SUCCESS}{Icons.CHECK} Using {Colors.SECONDARY}{state['current_model']}{Colors.RESET}\n")
                
                if result == "reload_model":
                    is_cloud = api.CURRENT_API in ["gemini", "cerebras", "anthropic", "openai"]
                    if not is_cloud:
                        spinner = ui.Spinner(f"Loading {state['current_model']}")
                        spinner.start()
                        try:
                            api.load_model_and_verify(state['current_model'])
                            spinner.stop()
                        except Exception:
                            spinner.stop()
                            print(f"{Colors.WARNING}Failed to verify model{Colors.RESET}")
                continue
            
            # Handle @file mentions
            processed_content = user_input
            mentions = []
            found_mentions = re.findall(r'@([^\s]+)', user_input)
            added_paths = set()

            for raw_path in found_mentions:
                path = raw_path.rstrip('.,!?:;)]}\'"')
                
                if path in added_paths:
                    continue

                content = tools.read_file(path)
                if not content.startswith("Error:"):
                    mentions.append(f"Content of {path}:\n```\n{content}\n```")
                    added_paths.add(path)

            if mentions:
                processed_content += "\n\n--- ATTACHED FILES ---" + "\n\n".join(mentions)

            state['messages'].append({"role": "user", "content": processed_content})
            
            while True:
                print()
                ai_res, ai_reasoning, thinking_duration = api.stream_chat(state['current_model'], state['messages'])
                
                if not ai_res:
                    break

                cmds = tools.parse_commands(ai_res)
                
                if cmds:
                    last_tool_end = 0
                    for cmd in cmds:
                        tool_str = cmd['original']
                        pos = ai_res.rfind(tool_str)
                        if pos != -1:
                            last_tool_end = max(last_tool_end, pos + len(tool_str))
                    
                    if last_tool_end > 0:
                        ai_res = ai_res[:last_tool_end]
                
                history_msg = {"role": "assistant", "content": ai_res}
                if ai_reasoning:
                    history_msg["reasoning"] = ai_reasoning
                if thinking_duration:
                    history_msg["thinking_duration"] = thinking_duration
                state['messages'].append(history_msg)
                
                if cmds:
                    result_str = process_tool_calls(cmds, state)
                    
                    if result_str:
                        state['messages'].append({"role": "user", "content": result_str})
                    else:
                        break
                else:
                    break

        except EOFError:
            break


def main():
    """Entry point."""
    if os.name == 'nt':
        print("grucli was *NOT* tested on windows, use at your own risk. Color codes may appear as weird characters")

    from .stats import send_telemetry_ping
    send_telemetry_ping()
    
    ui.print_ascii_art()
    
    interrupt.hide_control_chars()
    atexit.register(STATS.print_summary)
    
    while True:
        try:
            api_type, api_key = select_api_ui()
            api.set_api_config(api_type, api_key)

            selected_model = select_model_ui(skip_loading=(api_type in ["gemini", "cerebras", "anthropic", "openai"]))
            start_chat(selected_model)
            break
        except interrupt.BackSignal:
            interrupt.clear_bottom_warning()
            continue


if __name__ == "__main__":
    main()
