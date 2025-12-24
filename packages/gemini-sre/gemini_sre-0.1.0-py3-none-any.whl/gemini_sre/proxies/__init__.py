"""
Namespace proxies for Google GenAI SDK.

Each proxy wraps a namespace of the official SDK with SRE features.
"""

from gemini_sre.proxies.caches import CachesProxy
from gemini_sre.proxies.chats import ChatsProxy
from gemini_sre.proxies.files import FilesProxy
from gemini_sre.proxies.models import ModelsProxy
from gemini_sre.proxies.operations import OperationsProxy
from gemini_sre.proxies.tunings import TuningsProxy

__all__ = [
    "ModelsProxy",
    "FilesProxy",
    "ChatsProxy",
    "TuningsProxy",
    "CachesProxy",
    "OperationsProxy",
]
