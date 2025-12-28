"""
Chat management for grucli - handles saving, loading and managing chat histories.
"""
import os
import json
import time
from datetime import datetime
from .theme import Colors, Icons, Borders
from . import interrupt
from . import ui

CHATS_DIR = os.path.expanduser("~/.grucli/chats/")

def ensure_chats_dir():
    """Ensure the chats directory exists."""
    if not os.path.exists(CHATS_DIR):
        os.makedirs(CHATS_DIR)

def get_chat_path(name):
    """Get the full path for a chat file."""
    # Simple slugify to avoid issues with filenames
    safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
    return os.path.join(CHATS_DIR, f"{safe_name}.json")

def save_chat(name, messages, model, provider):
    """Save the current chat history."""
    ensure_chats_dir()
    path = get_chat_path(name)
    
    chat_data = {
        "name": name,
        "messages": messages,
        "model": model,
        "provider": provider,
        "last_opened": datetime.now().isoformat(),
        "version": 1
    }
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(chat_data, f, indent=2, ensure_ascii=False)
    
    return path

def load_chat(name):
    """Load a chat history by name."""
    path = get_chat_path(name)
    if not os.path.exists(path):
        return None
        
    with open(path, 'r', encoding='utf-8') as f:
        chat_data = json.load(f)
    
    # Update last opened time
    chat_data["last_opened"] = datetime.now().isoformat()
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(chat_data, f, indent=2, ensure_ascii=False)
        
    return chat_data

def list_chats():
    """List all saved chats with metadata."""
    ensure_chats_dir()
    chats = []
    for filename in os.listdir(CHATS_DIR):
        if filename.endswith(".json"):
            try:
                with open(os.path.join(CHATS_DIR, filename), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    chats.append({
                        "name": data.get("name", filename[:-5]),
                        "filename": filename,
                        "last_opened": data.get("last_opened", "Unknown"),
                        "model": data.get("model", "unknown")
                    })
            except Exception:
                continue
                
    # Sort by last opened (newest first)
    chats.sort(key=lambda x: x["last_opened"], reverse=True)
    return chats

def delete_chat(name):
    """Delete a saved chat."""
    path = get_chat_path(name)
    if os.path.exists(path):
        os.remove(path)
        return True
    return False

def rename_chat(old_name, new_name):
    """Rename a saved chat."""
    old_path = get_chat_path(old_name)
    new_path = get_chat_path(new_name)
    
    if os.path.exists(old_path):
        if os.path.exists(new_path):
            return False, "A chat with that name already exists."
            
        with open(old_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        data["name"] = new_name
        
        with open(new_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        os.remove(old_path)
        return True, None
    return False, "Original chat not found."

def manage_chats_ui():
    """Interactive UI to manage chats."""
    while True:
        chats = list_chats()
        if not chats:
            print(f"\n{Colors.WARNING}No saved chats found.{Colors.RESET}\n")
            return None

        title = "Manage Saved Chats"
        options = []
        for chat in chats:
            # Format last opened time for display
            try:
                dt = datetime.fromisoformat(chat["last_opened"])
                last_opened_str = dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                last_opened_str = chat["last_opened"]
                
            label = f"{chat['name']} ({Colors.MUTED}{chat['model']}, {last_opened_str}{Colors.RESET})"
            options.append(label)
        
        options.append(f"{Colors.MUTED}Back to chat{Colors.RESET}")

        try:
            result = ui.select_option(options, title)
            if not result:
                return None
            
            _, selected_index = result
            
            # Check if 'Back to chat' was selected (it's the last option)
            if selected_index == len(chats):
                return None
                
            selected_chat = chats[selected_index]
            selected_chat_name = selected_chat['name']
            
            # Action menu for the selected chat
            action_title = f"Chat: {selected_chat_name}"
            actions = [
                f"{Colors.SUCCESS}{Icons.CHECK} Load Chat{Colors.RESET}",
                f"{Colors.WARNING} Rename Chat{Colors.RESET}",
                f"{Colors.ERROR}{Icons.CROSS} Delete Chat{Colors.RESET}",
                f"{Colors.MUTED}Cancel{Colors.RESET}"
            ]
            
            action_result = ui.select_option(actions, action_title)
            if not action_result:
                continue
                
            _, action_index = action_result
            
            if action_index == 0: # Load
                return selected_chat_name
            elif action_index == 1: # Rename
                print(f"\n{Colors.MUTED}Enter new name for '{selected_chat_name}':{Colors.RESET}")
                new_name = interrupt.safe_input(f"{Colors.INPUT_ACTIVE}> {Colors.RESET}").strip()
                if new_name:
                    success, err = rename_chat(selected_chat_name, new_name)
                    if success:
                        print(f"{Colors.SUCCESS}{Icons.CHECK} Chat renamed to '{new_name}'.{Colors.RESET}")
                        time.sleep(1)
                    else:
                        print(f"{Colors.ERROR}{Icons.CROSS} {err}{Colors.RESET}")
                        time.sleep(2)
            elif action_index == 2: # Delete
                confirm = interrupt.safe_input(f"{Colors.WARNING}Delete chat '{selected_chat_name}'? (y/n): {Colors.RESET}").strip().lower()
                if confirm == 'y':
                    if delete_chat(selected_chat_name):
                        print(f"{Colors.SUCCESS}{Icons.CHECK} Chat deleted.{Colors.RESET}")
                        time.sleep(1)
                    else:
                        print(f"{Colors.ERROR}{Icons.CROSS} Failed to delete chat.{Colors.RESET}")
                        time.sleep(2)
            # action_index == 3 is Cancel, which just loops back
                        
        except interrupt.BackSignal:
            return None
        except KeyboardInterrupt:
            return None
