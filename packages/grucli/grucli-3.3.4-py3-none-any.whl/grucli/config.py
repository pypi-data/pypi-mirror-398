import os
import json
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import getpass
import sys
from . import interrupt

CONFIG_DIR_NAME = '.grucli'

def get_config_dir():
    home_dir = os.path.expanduser("~")
    config_dir = os.path.join(home_dir, CONFIG_DIR_NAME)
    
    os.makedirs(config_dir, exist_ok=True)
    
    return config_dir

def get_key_storage_path(api_type='gemini'):
    config_dir = get_config_dir()
    if api_type == 'gemini':
        return os.path.join(config_dir, 'api_keys_gemini.enc')
    elif api_type == 'cerebras':
        return os.path.join(config_dir, 'api_keys_cerebras.enc')
    elif api_type == 'anthropic':
        return os.path.join(config_dir, 'api_keys_anthropic.enc')
    elif api_type == 'openai':
        return os.path.join(config_dir, 'api_keys_openai.enc')
    elif api_type == 'ollama':
        return os.path.join(config_dir, 'api_keys_ollama.enc')
    else:
        return os.path.join(config_dir, 'api_keys.enc')


def get_settings_path():
    config_dir = get_config_dir()
    return os.path.join(config_dir, 'settings.json')

def load_settings():
    path = get_settings_path()
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_settings(settings):
    path = get_settings_path()
    with open(path, 'w') as f:
        json.dump(settings, f, indent=2)

def is_using_google_auth():
    settings = load_settings()
    return settings.get('use_google_auth', False)

def set_use_google_auth(use_google_auth: bool):
    settings = load_settings()
    settings['use_google_auth'] = use_google_auth
    save_settings(settings)

def get_telemetry_enabled():
    settings = load_settings()
    return settings.get('telemetry_enabled', True)

def set_telemetry_enabled(enabled: bool):
    settings = load_settings()
    settings['telemetry_enabled'] = enabled
    save_settings(settings)

def get_google_cloud_project():
    settings = load_settings()
    return settings.get('google_cloud_project')

def set_google_cloud_project(project_id: str):
    settings = load_settings()
    settings['google_cloud_project'] = project_id
    save_settings(settings)

def get_history_file_path():
    config_dir = get_config_dir()
    return os.path.join(config_dir, 'history.txt')

def prune_history(file_path, max_entries=25):
    if not os.path.exists(file_path):
        return
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        entries = []
        current_entry = []
        for line in lines:
            if line.startswith('#'):
                if current_entry:
                    entries.append(current_entry)
                current_entry = [line]
            else:
                current_entry.append(line)
        if current_entry:
            entries.append(current_entry)
            
        if len(entries) > max_entries:
            entries = entries[-max_entries:]
            with open(file_path, 'w', encoding='utf-8') as f:
                for entry in entries:
                    f.writelines(entry)
    except Exception:
        pass

def derive_key_from_password(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key

def encrypt_data(data: str, master_password: str) -> tuple[bytes, bytes]:
    salt = os.urandom(16)
    
    key = derive_key_from_password(master_password, salt)
    
    cipher = Fernet(key)
    encrypted_data = cipher.encrypt(data.encode())
    
    return encrypted_data, salt

def decrypt_data(encrypted_data: bytes, master_password: str, salt: bytes) -> str:
    key = derive_key_from_password(master_password, salt)
    
    cipher = Fernet(key)
    decrypted_data = cipher.decrypt(encrypted_data)
    
    return decrypted_data.decode()

def save_encrypted_api_key(api_key: str, api_type='gemini'):
    print("\nTo securely store your API key, please set a password.")
    print("This password will be used to encrypt your API key.")

    while True:
        password = interrupt.safe_getpass("Set password: ")
        confirm_password = interrupt.safe_getpass("Confirm password: ")

        if password == confirm_password:
            break
        else:
            print("Passwords do not match. Please try again.")

    encrypted_data, salt = encrypt_data(api_key, password)

    storage_path = get_key_storage_path(api_type)
    key_name = f'{api_type}_api_key'
    storage_data = {
        key_name: base64.b64encode(encrypted_data).decode(),
        'salt': base64.b64encode(salt).decode(),
    }

    with open(storage_path, 'w') as f:
        json.dump(storage_data, f)

    print(f"API key saved securely in {storage_path}")


def change_encrypted_api_key_password(api_type='gemini'):
    storage_path = get_key_storage_path(api_type)

    if not os.path.exists(storage_path):
        print("No saved API key found.")
        return False

    try:
        with open(storage_path, 'r') as f:
            storage_data = json.load(f)

        key_name = f'{api_type}_api_key'
        if key_name not in storage_data or 'salt' not in storage_data:
            print("Saved API key data is corrupted.")
            return False

        encrypted_data = base64.b64decode(storage_data[key_name])
        salt = base64.b64decode(storage_data['salt'])

        current_password = interrupt.safe_getpass("\nEnter current password: ")
        decrypted_api_key = decrypt_data(encrypted_data, current_password, salt)

        while True:
            new_password = interrupt.safe_getpass("Enter new password: ")
            confirm_new_password = interrupt.safe_getpass("Confirm new password: ")

            if new_password == confirm_new_password:
                break
            else:
                print("Passwords do not match. Please try again.")

        new_encrypted_data, new_salt = encrypt_data(decrypted_api_key, new_password)

        key_name = f'{api_type}_api_key'
        new_storage_data = {
            key_name: base64.b64encode(new_encrypted_data).decode(),
            'salt': base64.b64encode(new_salt).decode(),
        }

        with open(storage_path, 'w') as f:
            json.dump(new_storage_data, f)

        print("Password changed successfully.")
        return True

    except Exception as e:
        print(f"Error changing password: {e}")
        return False


def remove_saved_api_key(api_type='gemini'):
    storage_path = get_key_storage_path(api_type)

    if not os.path.exists(storage_path):
        print("No saved API key found.")
        return False

    confirm = interrupt.safe_input(f"Are you sure you want to remove the saved API key? (y/N): ").strip().lower()
    if confirm == 'y':
        try:
            os.remove(storage_path)
            print("Saved API key removed successfully.")
            return True
        except Exception as e:
            print(f"Error removing saved API key: {e}")
            return False
    else:
        print("Operation cancelled.")
        return False


def load_decrypted_api_key(api_type='gemini') -> str:
    storage_path = get_key_storage_path(api_type)

    if not os.path.exists(storage_path):
        return None

    try:
        with open(storage_path, 'r') as f:
            storage_data = json.load(f)

        key_name = f'{api_type}_api_key'
        if key_name not in storage_data or 'salt' not in storage_data:
            return None

        encrypted_data = base64.b64decode(storage_data[key_name])
        salt = base64.b64decode(storage_data['salt'])

        password = interrupt.safe_getpass("\nEnter password to unlock API key: ")

        decrypted_api_key = decrypt_data(encrypted_data, password, salt)
        return decrypted_api_key

    except Exception as e:
        print(f"Error loading API key: {e}")
        return None


def has_saved_api_key(api_type='gemini') -> bool:
    storage_path = get_key_storage_path(api_type)
    return os.path.exists(storage_path)

