"""
Slash command handling.
"""

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import HTML
from . import api
from . import config
from . import tools
from . import auth
from . import interrupt
from . import chat_manager
from . import ui
from .theme import Colors, Icons, Borders
import os
import time

CMD_LIST = ['/exit', '/clear', '/help', '/model', '/manage-api-keys', '/gemini-login', '/gemini-auth-mode', '/show-reasoning', '/save', '/load', '/manage-chats', '/telemetry']


class ChatCompleter(Completer):
    """Autocomplete for commands and file mentions."""
    
    def __init__(self):
        self._file_cache = []
        self._last_cache_time = 0

    def get_completions(self, document, complete_event):
        text_before_cursor = document.text_before_cursor
        if not text_before_cursor:
            return

        last_space = text_before_cursor.rfind(' ')
        current_word = text_before_cursor[last_space+1:]

        if text_before_cursor.startswith('/') and ' ' not in text_before_cursor:
            for cmd in CMD_LIST:
                if cmd.startswith(text_before_cursor):
                    yield Completion(
                        cmd,
                        start_position=-len(text_before_cursor),
                        display=HTML(f'<style color="#af5fff">{cmd}</style>')
                    )
            return

        if text_before_cursor.startswith('/load ') and ' ' not in text_before_cursor[6:]:
            chat_prefix = text_before_cursor[6:].lower()
            chats = chat_manager.list_chats()
            for chat in chats:
                name = chat['name']
                if name.lower().startswith(chat_prefix):
                    yield Completion(
                        name,
                        start_position=-len(chat_prefix),
                        display=HTML(f'<style color="#af5fff">{name}</style>')
                    )
            return

        if '@' in current_word:
            at_idx = current_word.rfind('@')
            mention = current_word[at_idx+1:]
            mention_lower = mention.lower()
            
            now = time.time()
            if now - self._last_cache_time > 5:
                self._file_cache = tools.list_files_recursive()
                self._last_cache_time = now
                
            for file_path in self._file_cache:
                if mention_lower in file_path.lower():
                    yield Completion(
                        file_path,
                        start_position=-len(mention),
                        display=HTML(f'<style color="#af5fff">@{file_path}</style>')
                    )


completer = ChatCompleter()


def manage_api_key(api_type='gemini'):
    """Manage saved API keys."""
    api_name = api_type.capitalize()
    
    print(f"\n{Colors.BOLD}{api_name} API Key{Colors.RESET}")
    print(f"{Colors.MUTED}{Borders.HORIZONTAL * 25}{Colors.RESET}\n")
    
    print(f"  {Colors.SUCCESS}1{Colors.RESET}) Change key")
    print(f"  {Colors.WARNING}2{Colors.RESET}) Change password")
    print(f"  {Colors.ERROR}3{Colors.RESET}) Remove key")
    print(f"  {Colors.MUTED}4{Colors.RESET}) Cancel")
    print()
    
    choice = interrupt.safe_input(f"{Colors.INPUT_ACTIVE}Choice: {Colors.RESET}").strip()

    if choice == '1':
        if config.has_saved_api_key(api_type):
            print(f"\n{Colors.MUTED}Enter new {api_name} API key:{Colors.RESET}")
            new_api_key = interrupt.safe_input(f"{Colors.INPUT_ACTIVE}> {Colors.RESET}").strip()
            if new_api_key:
                config.save_encrypted_api_key(new_api_key, api_type)
                print(f"{Colors.SUCCESS}{Icons.CHECK} Updated{Colors.RESET}")
            else:
                print(f"{Colors.WARNING}No key provided{Colors.RESET}")
        else:
            print(f"{Colors.WARNING}No saved key found{Colors.RESET}")

    elif choice == '2':
        config.change_encrypted_api_key_password(api_type)

    elif choice == '3':
        config.remove_saved_api_key(api_type)

    elif choice == '4':
        print(f"{Colors.MUTED}Cancelled{Colors.RESET}")
    else:
        print(f"{Colors.ERROR}Invalid option{Colors.RESET}")


def handle_command(cmd, state):
    """Handle slash commands."""
    c = cmd.lower().strip()
    
    if c == '/exit':
        return "exit"
        
    elif c == '/clear':
        sys_prompt = api.get_system_prompt()
        state['messages'] = [{"role": "system", "content": sys_prompt}]
        print(f"{Colors.SUCCESS}{Icons.CHECK} Cleared{Colors.RESET}\n")
        return "continue"
        
    elif c == '/help':
        print(f"\n{Colors.BOLD}Commands{Colors.RESET}\n")
        
        commands_help = [
            ('/help', 'Show this help'),
            ('/exit', 'Exit'),
            ('/clear', 'Clear chat history'),
            ('/model', 'Switch model'),
            ('/manage-api-keys', 'Manage API keys'),
            ('/gemini-login', 'Login with Google'),
            ('/gemini-auth-mode', 'Toggle auth mode'),
            ('/show-reasoning', 'Toggle reasoning display'),
            ('/save [name]', 'Save chat'),
            ('/load [name]', 'Load chat'),
            ('/manage-chats', 'Manage saved chats'),
            ('/telemetry [true|false]', 'Enable/disable usage stats'),
        ]
        
        for cmd_name, desc in commands_help:
            print(f"  {Colors.SECONDARY}{cmd_name:20}{Colors.RESET} {Colors.MUTED}{desc}{Colors.RESET}")
        
        print(f"\n{Colors.MUTED}Use @filename to attach file contents{Colors.RESET}\n")
        return "continue"
        
    elif c == '/model':
        return "select_model"
        
    elif c == '/manage-api-keys':
        print(f"\n{Colors.BOLD}Select API{Colors.RESET}\n")
        
        print(f"  {Colors.SUCCESS}1{Colors.RESET}) OpenAI")
        print(f"  {Colors.SUCCESS}2{Colors.RESET}) Anthropic")
        print(f"  {Colors.SUCCESS}3{Colors.RESET}) Gemini")
        print(f"  {Colors.SUCCESS}4{Colors.RESET}) Cerebras")
        print(f"  {Colors.MUTED}5{Colors.RESET}) Cancel")
        print()

        choice = interrupt.safe_input(f"{Colors.INPUT_ACTIVE}Choice: {Colors.RESET}").strip()
        if choice == '1':
            manage_api_key('openai')
        elif choice == '2':
            manage_api_key('anthropic')
        elif choice == '3':
            manage_api_key('gemini')
        elif choice == '4':
            manage_api_key('cerebras')
        elif choice == '5':
            print(f"{Colors.MUTED}Cancelled{Colors.RESET}")
        else:
            print(f"{Colors.ERROR}Invalid option{Colors.RESET}")

        return "continue"
        
    elif c == '/gemini-login':
        print(f"\n{Colors.INFO}Authenticating with Google...{Colors.RESET}")
        try:
            auth.perform_oauth_login()
            print(f"{Colors.SUCCESS}{Icons.CHECK} Logged in{Colors.RESET}")
            config.set_use_google_auth(True)
        except Exception as e:
            print(f"{Colors.ERROR}{Icons.CROSS} Failed: {e}{Colors.RESET}")
        return "continue"
        
    elif c == '/gemini-auth-mode':
        current_mode = "Google Auth" if config.is_using_google_auth() else "API Key"
        print(f"\n{Colors.BOLD}Auth Mode{Colors.RESET}")
        print(f"{Colors.MUTED}Current: {Colors.SECONDARY}{current_mode}{Colors.RESET}")
        
        if config.is_using_google_auth():
            project_id = os.environ.get('GOOGLE_CLOUD_PROJECT') or os.environ.get('GOOGLE_CLOUD_PROJECT_ID') or config.get_google_cloud_project()
            print(f"{Colors.MUTED}Project: {Colors.SECONDARY}{project_id or 'Not set'}{Colors.RESET}")
        
        print(f"\n  {Colors.SUCCESS}1{Colors.RESET}) Google Auth")
        print(f"  {Colors.SUCCESS}2{Colors.RESET}) API Key")
        print(f"  {Colors.WARNING}3{Colors.RESET}) Set Project ID")
        print(f"  {Colors.MUTED}4{Colors.RESET}) Cancel")
        print()
        
        choice = interrupt.safe_input(f"{Colors.INPUT_ACTIVE}Choice: {Colors.RESET}").strip()
        if choice == '1':
            config.set_use_google_auth(True)
            print(f"{Colors.SUCCESS}{Icons.CHECK} Using Google Auth{Colors.RESET}")
            if not auth.get_auth_token():
                print(f"{Colors.MUTED}Starting login...{Colors.RESET}")
                auth.perform_oauth_login()
        elif choice == '2':
            config.set_use_google_auth(False)
            print(f"{Colors.SUCCESS}{Icons.CHECK} Using API Key{Colors.RESET}")
        elif choice == '3':
            new_project_id = interrupt.safe_input(f"{Colors.INPUT_ACTIVE}Project ID: {Colors.RESET}").strip()
            if new_project_id:
                config.set_google_cloud_project(new_project_id)
                print(f"{Colors.SUCCESS}{Icons.CHECK} Set to {new_project_id}{Colors.RESET}")
        elif choice == '4':
            print(f"{Colors.MUTED}Cancelled{Colors.RESET}")
        else:
            print(f"{Colors.ERROR}Invalid option{Colors.RESET}")
        return "continue"
        
    elif c.startswith('/show-reasoning'):
        parts = c.split()
        if len(parts) > 1:
            val = parts[1]
            if val in ['true', 'on', '1', 'yes']:
                api.SHOW_REASONING = True
                print(f"{Colors.SUCCESS}{Icons.CHECK} Reasoning enabled{Colors.RESET}")
            elif val in ['false', 'off', '0', 'no']:
                api.SHOW_REASONING = False
                print(f"{Colors.SUCCESS}{Icons.CHECK} Reasoning disabled{Colors.RESET}")
            else:
                print(f"{Colors.ERROR}Use true/false{Colors.RESET}")
        else:
            api.SHOW_REASONING = not api.SHOW_REASONING
            status = "enabled" if api.SHOW_REASONING else "disabled"
            print(f"{Colors.SUCCESS}{Icons.CHECK} Reasoning {status}{Colors.RESET}")
        return "continue"
        
    elif c.startswith('/telemetry'):
        parts = c.split()
        if len(parts) > 1:
            val = parts[1]
            if val in ['true', 'on', '1', 'yes']:
                config.set_telemetry_enabled(True)
                print(f"{Colors.SUCCESS}{Icons.CHECK} Telemetry enabled. Thank you for supporting the project!{Colors.RESET}")
            elif val in ['false', 'off', '0', 'no']:
                config.set_telemetry_enabled(False)
                print(f"{Colors.SUCCESS}{Icons.CHECK} Telemetry permanently disabled.{Colors.RESET}")
            else:
                print(f"{Colors.ERROR}Use /telemetry true or /telemetry false{Colors.RESET}")
        else:
            current = config.get_telemetry_enabled()
            status = "enabled" if current else "disabled"
            print(f"{Colors.INFO}Telemetry is currently {status}.{Colors.RESET}")
            print(f"{Colors.MUTED}Use /telemetry false to disable.{Colors.RESET}")
        return "continue"
        
    elif c.startswith('/save'):
        parts = cmd.split(None, 1)
        if len(parts) > 1:
            name = parts[1].strip()
        else:
            print(f"\n{Colors.MUTED}Chat name:{Colors.RESET}")
            name = interrupt.safe_input(f"{Colors.INPUT_ACTIVE}> {Colors.RESET}").strip()
            
        if not name:
            print(f"{Colors.ERROR}Name required{Colors.RESET}")
            return "continue"
            
        path = chat_manager.save_chat(name, state['messages'], state['current_model'], api.CURRENT_API)
        print(f"{Colors.SUCCESS}{Icons.CHECK} Saved to {Colors.SECONDARY}{path}{Colors.RESET}\n")
        return "continue"

    elif c.startswith('/load'):
        parts = cmd.split(None, 1)
        if len(parts) > 1:
            name = parts[1].strip()
        else:
            chats = chat_manager.list_chats()
            if not chats:
                print(f"{Colors.WARNING}No saved chats{Colors.RESET}")
                return "continue"
            
            title = "Load Chat"
            options = [f"{c['name']} ({Colors.MUTED}{c['model']}{Colors.RESET})" for c in chats]
            result = ui.select_option(options, title)
            if not result:
                return "continue"
            _, idx = result
            name = chats[idx]['name']
            
        chat_data = chat_manager.load_chat(name)
        if chat_data:
            state['messages'] = chat_data['messages']
            
            print(f"{Colors.SUCCESS}{Icons.CHECK} Loaded '{name}'{Colors.RESET}\n")
            os.system('cls' if os.name == 'nt' else 'clear')
            ui.print_messages(state['messages'])
            return "continue"
        else:
            print(f"{Colors.ERROR}Chat '{name}' not found{Colors.RESET}")
            return "continue"

    elif c == '/manage-chats':
        chat_to_load = chat_manager.manage_chats_ui()
        if chat_to_load:
            chat_data = chat_manager.load_chat(chat_to_load)
            if chat_data:
                state['messages'] = chat_data['messages']
                
                print(f"{Colors.SUCCESS}{Icons.CHECK} Loaded '{chat_to_load}'{Colors.RESET}\n")
                os.system('cls' if os.name == 'nt' else 'clear')
                ui.print_messages(state['messages'])
        return "continue"
        
    else:
        print(f"{Colors.ERROR}Unknown: {cmd}{Colors.RESET}")
        print(f"{Colors.MUTED}Type /help for commands{Colors.RESET}")
        return "continue"