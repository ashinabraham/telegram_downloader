"""
Unit tests for the user state management module.
"""

import pytest
from src.core.user_state import UserState


class TestUserState:
    """Test cases for the UserState class."""

    def test_user_state_initialization(self):
        """Test UserState initialization."""
        user_state = UserState()
        assert user_state.user_states == {}

    def test_set_state_new_user(self):
        """Test setting state for a new user."""
        user_state = UserState()
        user_state.set_state("123456", "logged_in", chat_id=789012)
        
        assert user_state.user_states["123456"]["state"] == "logged_in"
        assert user_state.user_states["123456"]["chat_id"] == 789012

    def test_set_state_existing_user(self):
        """Test setting state for an existing user."""
        user_state = UserState()
        user_state.set_state("123456", "awaiting_phone", chat_id=789012)
        user_state.set_state("123456", "logged_in", phone="+1234567890")
        
        assert user_state.user_states["123456"]["state"] == "logged_in"
        assert user_state.user_states["123456"]["chat_id"] == 789012
        assert user_state.user_states["123456"]["phone"] == "+1234567890"

    def test_get_state_existing_user(self):
        """Test getting state for an existing user."""
        user_state = UserState()
        user_state.set_state("123456", "logged_in")
        
        state = user_state.get_state("123456")
        assert state == "logged_in"

    def test_get_state_nonexistent_user(self):
        """Test getting state for a nonexistent user."""
        user_state = UserState()
        state = user_state.get_state("nonexistent")
        assert state is None

    def test_get_user_data_existing_key(self):
        """Test getting user data for an existing key."""
        user_state = UserState()
        user_state.set_user_data("123456", "phone", "+1234567890")
        
        phone = user_state.get_user_data("123456", "phone")
        assert phone == "+1234567890"

    def test_get_user_data_nonexistent_key(self):
        """Test getting user data for a nonexistent key."""
        user_state = UserState()
        user_state.set_user_data("123456", "phone", "+1234567890")
        
        data = user_state.get_user_data("123456", "nonexistent")
        assert data is None

    def test_get_user_data_nonexistent_user(self):
        """Test getting user data for a nonexistent user."""
        user_state = UserState()
        data = user_state.get_user_data("nonexistent", "phone")
        assert data is None

    def test_get_user_data_with_default(self):
        """Test getting user data with a default value."""
        user_state = UserState()
        data = user_state.get_user_data("123456", "phone", default="default_phone")
        assert data == "default_phone"

    def test_set_user_data_new_user(self):
        """Test setting user data for a new user."""
        user_state = UserState()
        user_state.set_user_data("123456", "phone", "+1234567890")
        
        assert user_state.user_states["123456"]["phone"] == "+1234567890"

    def test_set_user_data_existing_user(self):
        """Test setting user data for an existing user."""
        user_state = UserState()
        user_state.set_state("123456", "logged_in")
        user_state.set_user_data("123456", "phone", "+1234567890")
        
        assert user_state.user_states["123456"]["state"] == "logged_in"
        assert user_state.user_states["123456"]["phone"] == "+1234567890"

    def test_update_user_data_multiple_fields(self):
        """Test updating multiple user data fields."""
        user_state = UserState()
        user_state.update_user_data("123456", phone="+1234567890", code="123456", chat_id=789012)
        
        assert user_state.user_states["123456"]["phone"] == "+1234567890"
        assert user_state.user_states["123456"]["code"] == "123456"
        assert user_state.user_states["123456"]["chat_id"] == 789012

    def test_update_user_data_existing_user(self):
        """Test updating user data for an existing user."""
        user_state = UserState()
        user_state.set_state("123456", "logged_in")
        user_state.update_user_data("123456", phone="+1234567890")
        
        assert user_state.user_states["123456"]["state"] == "logged_in"
        assert user_state.user_states["123456"]["phone"] == "+1234567890"

    def test_clear_user_state_existing_user(self):
        """Test clearing state for an existing user."""
        user_state = UserState()
        user_state.set_state("123456", "logged_in")
        user_state.clear_user_state("123456")
        
        assert "123456" not in user_state.user_states

    def test_clear_user_state_nonexistent_user(self):
        """Test clearing state for a nonexistent user."""
        user_state = UserState()
        user_state.clear_user_state("nonexistent")
        
        # Should not raise an exception
        assert user_state.user_states == {}

    def test_is_logged_in_true(self):
        """Test is_logged_in returns True for logged in user."""
        user_state = UserState()
        user_state.set_state("123456", "logged_in")
        
        assert user_state.is_logged_in("123456") is True

    def test_is_logged_in_false(self):
        """Test is_logged_in returns False for non-logged in user."""
        user_state = UserState()
        user_state.set_state("123456", "awaiting_phone")
        
        assert user_state.is_logged_in("123456") is False

    def test_is_logged_in_nonexistent_user(self):
        """Test is_logged_in returns False for nonexistent user."""
        user_state = UserState()
        assert user_state.is_logged_in("nonexistent") is False

    def test_is_authorized_true(self):
        """Test is_authorized returns True for authorized user."""
        user_state = UserState()
        allowed_users = {"123456", "789012"}
        
        assert user_state.is_authorized("123456", allowed_users) is True

    def test_is_authorized_false(self):
        """Test is_authorized returns False for unauthorized user."""
        user_state = UserState()
        allowed_users = {"123456", "789012"}
        
        assert user_state.is_authorized("345678", allowed_users) is False

    def test_is_authorized_empty_allowed_users(self):
        """Test is_authorized with empty allowed users set."""
        user_state = UserState()
        allowed_users = set()
        
        assert user_state.is_authorized("123456", allowed_users) is False

    def test_get_chat_id_existing_user(self):
        """Test getting chat_id for an existing user."""
        user_state = UserState()
        user_state.set_chat_id("123456", 789012)
        
        chat_id = user_state.get_chat_id("123456")
        assert chat_id == 789012

    def test_get_chat_id_nonexistent_user(self):
        """Test getting chat_id for a nonexistent user."""
        user_state = UserState()
        chat_id = user_state.get_chat_id("nonexistent")
        assert chat_id is None

    def test_set_chat_id_new_user(self):
        """Test setting chat_id for a new user."""
        user_state = UserState()
        user_state.set_chat_id("123456", 789012)
        
        assert user_state.user_states["123456"]["chat_id"] == 789012

    def test_set_chat_id_existing_user(self):
        """Test setting chat_id for an existing user."""
        user_state = UserState()
        user_state.set_state("123456", "logged_in")
        user_state.set_chat_id("123456", 789012)
        
        assert user_state.user_states["123456"]["state"] == "logged_in"
        assert user_state.user_states["123456"]["chat_id"] == 789012

    def test_state_transitions(self):
        """Test various state transitions."""
        user_state = UserState()
        
        # Initial state
        user_state.set_state("123456", "awaiting_phone", chat_id=789012)
        assert user_state.get_state("123456") == "awaiting_phone"
        
        # Transition to awaiting code
        user_state.set_state("123456", "awaiting_code", phone="+1234567890")
        assert user_state.get_state("123456") == "awaiting_code"
        assert user_state.get_user_data("123456", "phone") == "+1234567890"
        assert user_state.get_user_data("123456", "chat_id") == 789012
        
        # Transition to logged in
        user_state.set_state("123456", "logged_in")
        assert user_state.get_state("123456") == "logged_in"
        assert user_state.get_user_data("123456", "phone") == "+1234567890"

    def test_multiple_users_independence(self):
        """Test that multiple users have independent states."""
        user_state = UserState()
        
        user_state.set_state("user1", "awaiting_phone", chat_id=111111)
        user_state.set_state("user2", "logged_in", chat_id=222222)
        
        assert user_state.get_state("user1") == "awaiting_phone"
        assert user_state.get_state("user2") == "logged_in"
        assert user_state.get_chat_id("user1") == 111111
        assert user_state.get_chat_id("user2") == 222222 