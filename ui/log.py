from collections import deque
from dataclasses import dataclass
from typing import Optional


@dataclass
class Message:
    """A single log message with color"""

    text: str
    color: str = "white"


class MessageLog:
    """
    Stores game messages with colors.
    Supports scrolling through history.
    """

    def __init__(self, max_messages: int = 200):
        self.messages: deque[Message] = deque(maxlen=max_messages)
        self.scroll_offset: int = 0

    def add(self, text: str, color: str = "white"):
        """Add a message to the log"""
        self.messages.append(Message(text, color))
        # Reset scroll to bottom when new message arrives
        self.scroll_offset = 0

    def add_combat(self, text: str):
        """Convenience: add a combat message (red)"""
        self.add(text, "red")

    def add_info(self, text: str):
        """Convenience: add an info message (light blue)"""
        self.add(text, "light blue")

    def add_warning(self, text: str):
        """Convenience: add a warning message (yellow)"""
        self.add(text, "yellow")

    def add_success(self, text: str):
        """Convenience: add a success message (green)"""
        self.add(text, "green")

    def get_visible_messages(self, visible_lines: int) -> list[tuple[str, str]]:
        """
        Get messages to display, accounting for scroll offset.
        Returns list of (text, color) tuples, oldest first.
        """
        if not self.messages:
            return []

        total = len(self.messages)

        # end_idx is where we stop (exclusive), counting from the end
        # scroll_offset=0 means show the newest messages
        # scroll_offset=5 means skip the 5 newest, show older ones
        end_idx = total - self.scroll_offset
        start_idx = max(0, end_idx - visible_lines)

        return [(m.text, m.color) for m in list(self.messages)[start_idx:end_idx]]

    def scroll_up(self, amount: int = 1):
        """Scroll to see older messages"""
        # Can't scroll past the beginning
        max_scroll = max(0, len(self.messages) - 1)
        self.scroll_offset = min(self.scroll_offset + amount, max_scroll)

    def scroll_down(self, amount: int = 1):
        """Scroll to see newer messages"""
        self.scroll_offset = max(0, self.scroll_offset - amount)

    def scroll_to_bottom(self):
        """Jump to most recent messages"""
        self.scroll_offset = 0

    def scroll_to_top(self):
        """Jump to oldest messages"""
        self.scroll_offset = max(0, len(self.messages) - 1)

    def can_scroll_up(self) -> bool:
        """Check if there are older messages to scroll to"""
        return self.scroll_offset < len(self.messages) - 1

    def can_scroll_down(self) -> bool:
        """Check if there are newer messages to scroll to"""
        return self.scroll_offset > 0

    @property
    def is_at_bottom(self) -> bool:
        """Check if viewing the most recent messages"""
        return self.scroll_offset == 0
