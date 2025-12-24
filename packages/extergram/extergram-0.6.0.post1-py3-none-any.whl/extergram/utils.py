# extergram/utils.py

import re

def escape_markdown_v2(text: str) -> str:
    """Escapes special characters for MarkdownV2."""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

class Markdown:
    """
    A helper class for building Markdown formatted text.
    (This is a placeholder for potential future enhancements).
    """
    def __init__(self, text=""):
        self.text = text

    def bold(self, text: str) -> 'Markdown':
        self.text += f"*{text}*"
        return self

    def italic(self, text: str) -> 'Markdown':
        self.text += f"_{text}_"
        return self
    
    def __str__(self):
        return self.text