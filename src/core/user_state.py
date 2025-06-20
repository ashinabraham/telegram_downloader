"""
User state management module for the Telegram File Downloader Bot.
Handles user sessions, states, and state transitions.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class UserState:
    """User state management class."""
    
    def __init__(self):
        # Track user login state
        self.user_states: Dict[str, Dict[str, Any]] = {}
        # Possible states: None, 'awaiting_phone', 'awaiting_code', 'awaiting_2fa', 'logged_in', 'selecting_directory', 'awaiting_filename', 'awaiting_folder_name'
    
    def get_state(self, user_id: str) -> Optional[str]:
        """Get the current state of a user."""
        return self.user_states.get(user_id, {}).get('state')
    
    def set_state(self, user_id: str, state: str, **kwargs) -> None:
        """Set the state of a user with additional data."""
        if user_id not in self.user_states:
            self.user_states[user_id] = {}
        
        self.user_states[user_id]['state'] = state
        self.user_states[user_id].update(kwargs)
        logger.info(f"User {user_id} state changed to: {state}")
    
    def get_user_data(self, user_id: str, key: str, default=None) -> Any:
        """Get specific data for a user."""
        return self.user_states.get(user_id, {}).get(key, default)
    
    def set_user_data(self, user_id: str, key: str, value: Any) -> None:
        """Set specific data for a user."""
        if user_id not in self.user_states:
            self.user_states[user_id] = {}
        self.user_states[user_id][key] = value
    
    def update_user_data(self, user_id: str, **kwargs) -> None:
        """Update multiple data fields for a user."""
        if user_id not in self.user_states:
            self.user_states[user_id] = {}
        self.user_states[user_id].update(kwargs)
    
    def clear_user_state(self, user_id: str) -> None:
        """Clear all state data for a user."""
        if user_id in self.user_states:
            del self.user_states[user_id]
            logger.info(f"Cleared state for user {user_id}")
    
    def is_logged_in(self, user_id: str) -> bool:
        """Check if a user is logged in."""
        return self.get_state(user_id) == 'logged_in'
    
    def is_authorized(self, user_id: str, allowed_users: set) -> bool:
        """Check if a user is authorized to use the bot."""
        return user_id in allowed_users
    
    def get_chat_id(self, user_id: str) -> Optional[int]:
        """Get the chat ID for a user."""
        return self.get_user_data(user_id, 'chat_id')
    
    def set_chat_id(self, user_id: str, chat_id: int) -> None:
        """Set the chat ID for a user."""
        self.set_user_data(user_id, 'chat_id', chat_id)

# Global user state instance
user_state = UserState() 