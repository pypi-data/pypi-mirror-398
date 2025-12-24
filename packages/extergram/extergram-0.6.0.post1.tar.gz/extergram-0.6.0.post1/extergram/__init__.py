# extergram/__init__.py

from .core import Bot
from .ui import ButtonsDesign
from .utils import Markdown, escape_markdown_v2
from .api_types import Message, CallbackQuery, Update, User, Chat
from .docs import Docs
from . import ext
from . import errors

__version__ = "0.6.0"
__author__ = "WinFun15"
__email__ = "tibipocoxzsa@gmail.com"

__all__ = [
    "Bot",
    "ButtonsDesign",
    "Markdown",
    "escape_markdown_v2",
    "Message",
    "CallbackQuery",
    "Update",
    "User",
    "Chat",
    "Docs",
    "ext",
    "errors",
]