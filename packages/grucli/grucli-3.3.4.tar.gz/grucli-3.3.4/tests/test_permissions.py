"""
Tests for the permission system.
"""

import pytest
from grucli.permissions import (
    PermissionGroup,
    PermissionStore,
    TOOL_PERMISSION_MAP,
    get_tool_permission_group,
    PERMISSION_STORE,
)


class TestPermissionGroups:
    """Test permission group enum and mappings."""
    
    def test_permission_groups_exist(self):
        """All required permission groups should exist."""
        assert PermissionGroup.READ is not None
        assert PermissionGroup.WRITE is not None
        assert PermissionGroup.DESTRUCTIVE is not None
    
    def test_read_tools_mapped_correctly(self):
        """Read tools should map to READ group."""
        assert get_tool_permission_group('read_file') == PermissionGroup.READ
        assert get_tool_permission_group('get_current_directory_structure') == PermissionGroup.READ
    
    def test_write_tools_mapped_correctly(self):
        """Write tools should map to WRITE group."""
        assert get_tool_permission_group('create_file') == PermissionGroup.WRITE
        assert get_tool_permission_group('edit_file') == PermissionGroup.WRITE
    
    def test_destructive_tools_mapped_correctly(self):
        """Destructive tools should map to DESTRUCTIVE group."""
        assert get_tool_permission_group('delete_file') == PermissionGroup.DESTRUCTIVE
    
    def test_destructive_isolated_from_write(self):
        """DESTRUCTIVE must be separate from WRITE."""
        assert PermissionGroup.DESTRUCTIVE != PermissionGroup.WRITE
        assert get_tool_permission_group('delete_file') != get_tool_permission_group('edit_file')
    
    def test_unknown_tool_returns_none(self):
        """Unknown tools should return None."""
        assert get_tool_permission_group('unknown_tool') is None


class TestPermissionStore:
    """Test the session-scoped permission store."""
    
    def test_store_starts_empty(self):
        """New store should have no allowed groups."""
        store = PermissionStore()
        assert len(store.get_allowed_groups()) == 0
        assert not store.is_allowed(PermissionGroup.READ)
        assert not store.is_allowed(PermissionGroup.WRITE)
        assert not store.is_allowed(PermissionGroup.DESTRUCTIVE)
    
    def test_allow_always_persists_in_session(self):
        """Allow always should persist until reset."""
        store = PermissionStore()
        
        store.allow_always(PermissionGroup.READ)
        assert store.is_allowed(PermissionGroup.READ)
        
        # Should still be allowed
        assert store.is_allowed(PermissionGroup.READ)
    
    def test_allow_always_per_group(self):
        """Allow always should only apply to specific group."""
        store = PermissionStore()
        
        store.allow_always(PermissionGroup.READ)
        assert store.is_allowed(PermissionGroup.READ)
        assert not store.is_allowed(PermissionGroup.WRITE)
        assert not store.is_allowed(PermissionGroup.DESTRUCTIVE)
    
    def test_store_reset(self):
        """Reset should clear all permissions."""
        store = PermissionStore()
        
        store.allow_always(PermissionGroup.READ)
        store.allow_always(PermissionGroup.WRITE)
        assert store.is_allowed(PermissionGroup.READ)
        assert store.is_allowed(PermissionGroup.WRITE)
        
        store.reset()
        assert not store.is_allowed(PermissionGroup.READ)
        assert not store.is_allowed(PermissionGroup.WRITE)
        assert len(store.get_allowed_groups()) == 0
    
    def test_multiple_groups_can_be_allowed(self):
        """Multiple groups can be allowed simultaneously."""
        store = PermissionStore()
        
        store.allow_always(PermissionGroup.READ)
        store.allow_always(PermissionGroup.WRITE)
        
        assert store.is_allowed(PermissionGroup.READ)
        assert store.is_allowed(PermissionGroup.WRITE)
        assert len(store.get_allowed_groups()) == 2


class TestGlobalStore:
    """Test the global permission store."""
    
    def test_global_store_exists(self):
        """Global PERMISSION_STORE should exist."""
        assert PERMISSION_STORE is not None
    
    def test_global_store_is_permission_store(self):
        """Global store should be a PermissionStore instance."""
        assert isinstance(PERMISSION_STORE, PermissionStore)
