"""
Navigation stack for menu hierarchy and breadcrumbs.

Provides history tracking and breadcrumb generation for nested menus.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any
from pathlib import Path
import json


@dataclass
class NavigationNode:
    """Single level in navigation hierarchy.

    Attributes:
        id: Unique identifier for this navigation level
        label: Display name for breadcrumbs
        metadata: Additional data (menu state, filters, etc.)

    Example:
        >>> node = NavigationNode(
        ...     id="mcp_config",
        ...     label="MCP Configurations",
        ...     metadata={"filter": "active"}
        ... )
    """
    id: str
    label: str
    metadata: dict = field(default_factory=dict)


class NavigationStack:
    """Manages navigation hierarchy for menu system.

    Tracks navigation path, generates breadcrumbs, and supports
    deep linking to specific menu levels.

    Features:
    - Push/pop navigation levels
    - Automatic breadcrumb generation
    - Navigation depth tracking
    - State persistence (save/restore)

    Example:
        >>> nav = NavigationStack()
        >>> nav.push(NavigationNode(id="main", label="Main Menu"))
        >>> nav.push(NavigationNode(id="settings", label="Settings"))
        >>> nav.push(NavigationNode(id="mcp", label="MCP"))
        >>> nav.breadcrumbs()
        'Main Menu > Settings > MCP'
        >>> nav.depth()
        3
        >>> nav.pop()
        NavigationNode(id='mcp', label='MCP')
        >>> nav.breadcrumbs()
        'Main Menu > Settings'
    """

    def __init__(self):
        """Initialize empty navigation stack."""
        self._stack: List[NavigationNode] = []

    def push(self, node: NavigationNode):
        """Enter new navigation level.

        Args:
            node: NavigationNode to add to stack

        Example:
            >>> nav = NavigationStack()
            >>> nav.push(NavigationNode(id="settings", label="Settings"))
            >>> nav.depth()
            1
        """
        self._stack.append(node)

    def pop(self) -> Optional[NavigationNode]:
        """Go back one navigation level.

        Returns:
            Removed NavigationNode, or None if stack is empty

        Example:
            >>> nav = NavigationStack()
            >>> nav.push(NavigationNode(id="menu1", label="Menu 1"))
            >>> node = nav.pop()
            >>> node.id
            'menu1'
            >>> nav.depth()
            0
        """
        if self._stack:
            return self._stack.pop()
        return None

    def current(self) -> Optional[NavigationNode]:
        """Get current navigation level without removing it.

        Returns:
            Current NavigationNode, or None if stack is empty

        Example:
            >>> nav = NavigationStack()
            >>> nav.push(NavigationNode(id="menu1", label="Menu 1"))
            >>> nav.current().id
            'menu1'
            >>> nav.depth()  # Still at depth 1
            1
        """
        return self._stack[-1] if self._stack else None

    def peek(self, offset: int = 0) -> Optional[NavigationNode]:
        """Peek at a node in the stack without removing it.

        Args:
            offset: Offset from end (0 = current, 1 = parent, etc.)

        Returns:
            NavigationNode at offset, or None if invalid offset

        Example:
            >>> nav = NavigationStack()
            >>> nav.push(NavigationNode(id="main", label="Main"))
            >>> nav.push(NavigationNode(id="sub", label="Sub"))
            >>> nav.peek(0).id  # Current
            'sub'
            >>> nav.peek(1).id  # Parent
            'main'
        """
        index = -(offset + 1)
        if abs(index) <= len(self._stack):
            return self._stack[index]
        return None

    def breadcrumbs(self, separator: str = " > ", max_levels: int = None) -> str:
        """Generate breadcrumb trail from navigation stack.

        Args:
            separator: String to separate breadcrumb levels
            max_levels: Maximum levels to show (None = all)

        Returns:
            Formatted breadcrumb string

        Example:
            >>> nav = NavigationStack()
            >>> nav.push(NavigationNode(id="main", label="Main"))
            >>> nav.push(NavigationNode(id="settings", label="Settings"))
            >>> nav.push(NavigationNode(id="mcp", label="MCP"))
            >>> nav.breadcrumbs()
            'Main > Settings > MCP'
            >>> nav.breadcrumbs(separator=" → ")
            'Main → Settings → MCP'
            >>> nav.breadcrumbs(max_levels=2)
            'Settings > MCP'
        """
        if not self._stack:
            return ""

        # Get nodes to display
        nodes = self._stack
        if max_levels and len(nodes) > max_levels:
            nodes = nodes[-max_levels:]

        # Build breadcrumb string
        return separator.join(node.label for node in nodes)

    def breadcrumbs_styled(
        self,
        separator: str = " > ",
        current_style: str = "accent.soft",
        parent_style: str = "tertiary"
    ) -> str:
        """Generate styled breadcrumb trail with Rich markup.

        Args:
            separator: String to separate breadcrumb levels
            current_style: Rich style for current (last) level
            parent_style: Rich style for parent levels

        Returns:
            Styled breadcrumb string with Rich markup

        Example:
            >>> nav = NavigationStack()
            >>> nav.push(NavigationNode(id="main", label="Main"))
            >>> nav.push(NavigationNode(id="settings", label="Settings"))
            >>> nav.breadcrumbs_styled()
            '[tertiary]Main[/tertiary] > [accent.soft]Settings[/accent.soft]'
        """
        if not self._stack:
            return ""

        parts = []
        for i, node in enumerate(self._stack):
            is_current = (i == len(self._stack) - 1)
            style = current_style if is_current else parent_style
            parts.append(f"[{style}]{node.label}[/{style}]")

        return separator.join(parts)

    def depth(self) -> int:
        """Get current navigation depth.

        Returns:
            Number of levels in navigation stack

        Example:
            >>> nav = NavigationStack()
            >>> nav.depth()
            0
            >>> nav.push(NavigationNode(id="menu", label="Menu"))
            >>> nav.depth()
            1
        """
        return len(self._stack)

    def is_empty(self) -> bool:
        """Check if navigation stack is empty.

        Returns:
            True if stack is empty

        Example:
            >>> nav = NavigationStack()
            >>> nav.is_empty()
            True
            >>> nav.push(NavigationNode(id="menu", label="Menu"))
            >>> nav.is_empty()
            False
        """
        return len(self._stack) == 0

    def clear(self):
        """Reset navigation stack to empty state.

        Example:
            >>> nav = NavigationStack()
            >>> nav.push(NavigationNode(id="menu1", label="Menu 1"))
            >>> nav.push(NavigationNode(id="menu2", label="Menu 2"))
            >>> nav.depth()
            2
            >>> nav.clear()
            >>> nav.depth()
            0
        """
        self._stack.clear()

    def get_path(self) -> List[str]:
        """Get navigation path as list of node IDs.

        Returns:
            List of node IDs from root to current

        Example:
            >>> nav = NavigationStack()
            >>> nav.push(NavigationNode(id="main", label="Main"))
            >>> nav.push(NavigationNode(id="settings", label="Settings"))
            >>> nav.get_path()
            ['main', 'settings']
        """
        return [node.id for node in self._stack]

    def find(self, node_id: str) -> Optional[NavigationNode]:
        """Find node in stack by ID.

        Args:
            node_id: Node ID to search for

        Returns:
            First matching NavigationNode, or None if not found

        Example:
            >>> nav = NavigationStack()
            >>> nav.push(NavigationNode(id="main", label="Main"))
            >>> nav.push(NavigationNode(id="settings", label="Settings"))
            >>> node = nav.find("main")
            >>> node.label
            'Main'
        """
        for node in self._stack:
            if node.id == node_id:
                return node
        return None

    def contains(self, node_id: str) -> bool:
        """Check if node with ID exists in stack.

        Args:
            node_id: Node ID to check

        Returns:
            True if node exists in stack

        Example:
            >>> nav = NavigationStack()
            >>> nav.push(NavigationNode(id="main", label="Main"))
            >>> nav.contains("main")
            True
            >>> nav.contains("nonexistent")
            False
        """
        return self.find(node_id) is not None

    def pop_to(self, node_id: str) -> bool:
        """Pop stack until specified node is current.

        Args:
            node_id: Target node ID to pop to

        Returns:
            True if node was found and stack popped, False otherwise

        Example:
            >>> nav = NavigationStack()
            >>> nav.push(NavigationNode(id="main", label="Main"))
            >>> nav.push(NavigationNode(id="settings", label="Settings"))
            >>> nav.push(NavigationNode(id="mcp", label="MCP"))
            >>> nav.pop_to("settings")
            True
            >>> nav.current().id
            'settings'
            >>> nav.depth()
            2
        """
        # Find target node index
        target_index = None
        for i, node in enumerate(self._stack):
            if node.id == node_id:
                target_index = i
                break

        if target_index is None:
            return False

        # Pop until target is current
        while len(self._stack) > target_index + 1:
            self._stack.pop()

        return True

    def save_state(self, file_path: Path):
        """Save navigation state to JSON file.

        Args:
            file_path: Path to save state file

        Example:
            >>> nav = NavigationStack()
            >>> nav.push(NavigationNode(id="main", label="Main"))
            >>> nav.save_state(Path(".tmp/nav_state.json"))
        """
        state = {
            "stack": [
                {
                    "id": node.id,
                    "label": node.label,
                    "metadata": node.metadata
                }
                for node in self._stack
            ]
        }

        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w") as f:
            json.dump(state, f, indent=2)

    def load_state(self, file_path: Path) -> bool:
        """Load navigation state from JSON file.

        Args:
            file_path: Path to state file

        Returns:
            True if state loaded successfully, False otherwise

        Example:
            >>> nav = NavigationStack()
            >>> nav.load_state(Path(".tmp/nav_state.json"))
            True
            >>> nav.depth()
            1
        """
        if not file_path.exists():
            return False

        try:
            with open(file_path, "r") as f:
                state = json.load(f)

            self._stack = [
                NavigationNode(
                    id=node_data["id"],
                    label=node_data["label"],
                    metadata=node_data.get("metadata", {})
                )
                for node_data in state.get("stack", [])
            ]
            return True
        except Exception:
            return False

    def __repr__(self) -> str:
        """String representation of navigation stack.

        Returns:
            Debug string showing depth and breadcrumbs
        """
        if not self._stack:
            return "NavigationStack(empty)"
        return f"NavigationStack(depth={self.depth()}, path={self.breadcrumbs()})"
