# extergram/ext/base.py

from ..api_types import Update

class BaseHandler:
    """Base class for all handlers."""
    def __init__(self, callback):
        self.callback = callback

    def check_update(self, update: Update) -> bool:
        """Checks if the update is suitable for this handler."""
        raise NotImplementedError