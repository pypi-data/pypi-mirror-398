"""
Backward-compatible public module.

Prefer importing from `tanu` directly:
    from tanu import Tanuki, TanukiWorker
"""

from .client import Tanuki
from .worker import TanukiWorker

__all__ = ["Tanuki", "TanukiWorker"]
