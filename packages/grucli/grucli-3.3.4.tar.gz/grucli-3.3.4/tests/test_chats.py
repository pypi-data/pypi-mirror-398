"""
Tests for chat saving and loading functionality.
"""
import os
import json
import shutil
import unittest
from unittest.mock import MagicMock, patch
from grucli import chat_manager

class TestChatManager(unittest.TestCase):
    def setUp(self):
        # Use a temporary directory for chats
        self.test_chats_dir = os.path.expanduser("~/.grucli/test_chats/")
        if os.path.exists(self.test_chats_dir):
            shutil.rmtree(self.test_chats_dir)
        os.makedirs(self.test_chats_dir)
        
        # Patch CHATS_DIR in chat_manager
        self.patcher = patch('grucli.chat_manager.CHATS_DIR', self.test_chats_dir)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        if os.path.exists(self.test_chats_dir):
            shutil.rmtree(self.test_chats_dir)

    def test_save_and_load_chat(self):
        messages = [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi!"}]
        name = "Test Chat"
        model = "gpt-4o"
        provider = "openai"
        
        path = chat_manager.save_chat(name, messages, model, provider)
        self.assertTrue(os.path.exists(path))
        
        loaded = chat_manager.load_chat(name)
        self.assertEqual(loaded['name'], name)
        self.assertEqual(loaded['messages'], messages)
        self.assertEqual(loaded['model'], model)
        self.assertEqual(loaded['provider'], provider)

    def test_list_chats(self):
        chat_manager.save_chat("Chat 1", [], "m1", "p1")
        chat_manager.save_chat("Chat 2", [], "m2", "p2")
        
        chats = chat_manager.list_chats()
        self.assertEqual(len(chats), 2)
        names = [c['name'] for c in chats]
        self.assertIn("Chat 1", names)
        self.assertIn("Chat 2", names)

    def test_delete_chat(self):
        chat_manager.save_chat("To Delete", [], "m", "p")
        self.assertTrue(chat_manager.delete_chat("To Delete"))
        self.assertFalse(os.path.exists(chat_manager.get_chat_path("To Delete")))

    def test_rename_chat(self):
        chat_manager.save_chat("Old Name", [], "m", "p")
        success, err = chat_manager.rename_chat("Old Name", "New Name")
        self.assertTrue(success)
        self.assertIsNone(err)
        self.assertTrue(os.path.exists(chat_manager.get_chat_path("New Name")))
        self.assertFalse(os.path.exists(chat_manager.get_chat_path("Old Name")))

if __name__ == '__main__':
    unittest.main()
