"""
Kits - Stateful Tool Bundles with Lifecycle Hooks

Kits bundle related tools with shared state and lifecycle handlers.
They solve the problem of tools that need to coordinate or
participate in loop lifecycle events.

Example:
    from innerloop import Loop
    from innerloop.kits import TodoKit

    kit = TodoKit()
    loop = Loop(model="...", kits=[kit])
    response = loop.run("Add 3 todos and complete them")

    # Access state via kit
    print(kit.state.items)
"""

from .base import MAX_EXIT_ATTEMPTS, Kit, KitContext
from .safe_file import SafeFileKit, SafeFileState
from .todo import Status, Todo, TodoKit, TodoState

__all__ = [
    # Base classes
    "Kit",
    "KitContext",
    "MAX_EXIT_ATTEMPTS",
    # TodoKit
    "TodoKit",
    "TodoState",
    "Todo",
    "Status",
    # SafeFileKit
    "SafeFileKit",
    "SafeFileState",
]
