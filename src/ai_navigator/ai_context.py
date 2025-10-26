"""
AI Context Manager for maintaining conversation history and context.

This module provides context management for AI interactions, allowing the AI
to maintain awareness of previous interactions and make more informed decisions.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ContextMessage:
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None


class AIContext:
    """
    Maintains conversation context for AI interactions.
    
    This class stores conversation history, user preferences, and session
    information to provide better AI responses with awareness of previous
    interactions.
    """
    
    def __init__(self, max_history: int = 10):
        self.messages: List[ContextMessage] = []
        self.max_history = max_history
        self.user_preferences: Dict[str, Any] = {}
        self.session_data: Dict[str, Any] = {}
        self.start_location: Optional[Dict[str, Any]] = None
        self.end_location: Optional[Dict[str, Any]] = None
        
    def add_user_message(self, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Add a user message to the context."""
        self.messages.append(ContextMessage(
            role="user",
            content=content,
            metadata=metadata
        ))
        self._trim_history()
    
    def add_assistant_message(self, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Add an assistant message to the context."""
        self.messages.append(ContextMessage(
            role="assistant",
            content=content,
            metadata=metadata
        ))
        self._trim_history()
    
    def add_system_message(self, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Add a system message to the context."""
        self.messages.append(ContextMessage(
            role="system",
            content=content,
            metadata=metadata
        ))
        self._trim_history()
    
    def set_start_location(self, location: Dict[str, Any]):
        """Set the start location for navigation."""
        self.start_location = location
        self.add_system_message(
            f"Start location set: {location.get('name', 'Unknown')}",
            metadata={"location": location}
        )
    
    def set_end_location(self, location: Dict[str, Any]):
        """Set the end location for navigation."""
        self.end_location = location
        self.add_system_message(
            f"End location set: {location.get('name', 'Unknown')}",
            metadata={"location": location}
        )
    
    def set_preference(self, key: str, value: Any):
        """Set a user preference."""
        self.user_preferences[key] = value
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference."""
        return self.user_preferences.get(key, default)
    
    def set_session_data(self, key: str, value: Any):
        """Set session-specific data."""
        self.session_data[key] = value
    
    def get_session_data(self, key: str, default: Any = None) -> Any:
        """Get session-specific data."""
        return self.session_data.get(key, default)
    
    def get_conversation_history(self, include_system: bool = False) -> List[Dict[str, str]]:
        """
        Get conversation history in a format suitable for AI providers.
        
        Args:
            include_system: Whether to include system messages
            
        Returns:
            List of message dictionaries with 'role' and 'content' keys
        """
        messages = []
        for msg in self.messages:
            if not include_system and msg.role == "system":
                continue
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        return messages
    
    def get_context_summary(self) -> str:
        """
        Get a summary of the current context for inclusion in prompts.
        
        Returns:
            A formatted string summarizing the current context
        """
        summary_parts = []
        
        if self.start_location:
            summary_parts.append(
                f"Start location: {self.start_location.get('name', 'Unknown')} "
                f"({self.start_location.get('longitude')}, {self.start_location.get('latitude')})"
            )
        
        if self.end_location:
            summary_parts.append(
                f"End location: {self.end_location.get('name', 'Unknown')} "
                f"({self.end_location.get('longitude')}, {self.end_location.get('latitude')})"
            )
        
        if self.user_preferences:
            prefs = ", ".join(f"{k}: {v}" for k, v in self.user_preferences.items())
            summary_parts.append(f"User preferences: {prefs}")
        
        recent_messages = self.messages[-3:] if len(self.messages) > 3 else self.messages
        if recent_messages:
            summary_parts.append("Recent conversation:")
            for msg in recent_messages:
                if msg.role != "system":
                    summary_parts.append(f"  {msg.role}: {msg.content[:100]}...")
        
        return "\n".join(summary_parts) if summary_parts else "No context available"
    
    def _trim_history(self):
        """Trim message history to max_history length."""
        if len(self.messages) > self.max_history:
            system_messages = [msg for msg in self.messages if msg.role == "system"]
            other_messages = [msg for msg in self.messages if msg.role != "system"]
            
            keep_count = self.max_history - len(system_messages)
            if keep_count > 0:
                other_messages = other_messages[-keep_count:]
            else:
                other_messages = []
            
            self.messages = system_messages + other_messages
    
    def clear_history(self):
        """Clear all conversation history."""
        self.messages.clear()
    
    def clear_locations(self):
        """Clear start and end locations."""
        self.start_location = None
        self.end_location = None
    
    def reset(self):
        """Reset the entire context."""
        self.messages.clear()
        self.user_preferences.clear()
        self.session_data.clear()
        self.start_location = None
        self.end_location = None
