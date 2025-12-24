"""
TOON Format Integration for Claux.

Provides token-efficient inter-agent communication using TOON format.
TOON (Token-Oriented Object Notation) reduces token usage by ~40% vs JSON
while maintaining 74% accuracy (vs JSON's 70%).

Features:
- Tabular encoding for uniform arrays
- Lossless JSON compatibility
- Built-in validation
- 30-60% token reduction

References:
- Specification: https://toonformat.dev
- Python Implementation: https://github.com/toon-format/toon-python
"""

from typing import Any, Dict, Optional
import json
import os


try:
    from toon_format import encode as toon_encode, decode as toon_decode

    TOON_AVAILABLE = True
except ImportError:
    TOON_AVAILABLE = False

    # Fallback to JSON if TOON not installed
    def toon_encode(data: Any, **kwargs) -> str:
        """Fallback to JSON encoding if TOON not available."""
        return json.dumps(data, indent=2)

    def toon_decode(data: str, **kwargs) -> Any:
        """Fallback to JSON decoding if TOON not available."""
        return json.loads(data)


class ToonCodec:
    """
    TOON format encoder/decoder for inter-agent communication.

    Examples:
        >>> codec = ToonCodec()
        >>>
        >>> # Encode task assignment
        >>> tasks = {
        ...     "tasks": [
        ...         {"id": "T-001", "type": "bug_fix", "priority": "high"},
        ...         {"id": "T-002", "type": "test", "priority": "medium"}
        ...     ]
        ... }
        >>> toon_msg = codec.encode(tasks)
        >>>
        >>> # Decode response
        >>> result = codec.decode(toon_msg)
    """

    def __init__(self, use_toon: bool = True, track_metrics: bool = True):
        """
        Initialize TOON codec.

        Args:
            use_toon: Use TOON format if available, otherwise fallback to JSON
            track_metrics: Automatically log token usage metrics (default: True)
        """
        self.use_toon = use_toon and TOON_AVAILABLE
        self.format_name = "TOON" if self.use_toon else "JSON"
        self.track_metrics = track_metrics and os.environ.get("CLAUX_TRACK_METRICS", "1") == "1"

        # Lazy import to avoid circular dependency
        self._tracker = None
        if self.track_metrics:
            try:
                from claux.core.metrics import get_tracker

                self._tracker = get_tracker()
            except ImportError:
                self.track_metrics = False

    def encode(self, data: Any) -> str:
        """
        Encode data to TOON format.

        Args:
            data: Python object (dict, list, primitives)

        Returns:
            TOON-encoded string

        Examples:
            >>> codec = ToonCodec()
            >>> codec.encode({"name": "Alice", "age": 30})
            'name: Alice\\nage: 30'

            >>> codec.encode([{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}])
            'items[2]{id,name}:\\n  1,Alice\\n  2,Bob'
        """
        result = toon_encode(data) if self.use_toon else json.dumps(data, indent=2)

        # Log metrics if enabled (calculate directly without calling estimate_savings to avoid recursion)
        if self.track_metrics and self._tracker:
            json_str = json.dumps(data)
            json_tokens = len(json_str) // 4
            toon_tokens = len(result) // 4
            savings = json_tokens - toon_tokens
            savings_percent = (savings / json_tokens * 100) if json_tokens > 0 else 0

            self._tracker.log_encode(
                data=data,
                json_tokens=json_tokens,
                toon_tokens=toon_tokens,
                savings_percent=round(savings_percent, 1),
                format_used=self.format_name,
            )

        return result

    def decode(self, toon_str: str) -> Any:
        """
        Decode TOON format to Python object.

        Args:
            toon_str: TOON-encoded string

        Returns:
            Decoded Python object

        Examples:
            >>> codec = ToonCodec()
            >>> codec.decode("name: Alice\\nage: 30")
            {'name': 'Alice', 'age': 30}
        """
        result = toon_decode(toon_str) if self.use_toon else json.loads(toon_str)

        # Log metrics if enabled (calculate directly to avoid recursion)
        if self.track_metrics and self._tracker:
            json_str = json.dumps(result)
            json_tokens = len(json_str) // 4
            toon_tokens = len(toon_str) // 4
            savings = json_tokens - toon_tokens
            savings_percent = (savings / json_tokens * 100) if json_tokens > 0 else 0

            self._tracker.log_decode(
                toon_str=toon_str,
                json_tokens=json_tokens,
                toon_tokens=toon_tokens,
                savings_percent=round(savings_percent, 1),
            )

        return result

    def estimate_savings(self, data: Any) -> Dict[str, Any]:
        """
        Estimate token savings with TOON vs JSON.

        Args:
            data: Python object to analyze

        Returns:
            Dictionary with JSON tokens, TOON tokens, and savings percentage

        Examples:
            >>> codec = ToonCodec()
            >>> data = [{"id": i, "name": f"User{i}"} for i in range(100)]
            >>> stats = codec.estimate_savings(data)
            >>> print(f"Savings: {stats['savings_percent']}%")
            Savings: 42%
        """
        json_str = json.dumps(data)
        toon_str = self.encode(data)

        # Rough token estimation (4 chars ≈ 1 token)
        json_tokens = len(json_str) // 4
        toon_tokens = len(toon_str) // 4

        savings = json_tokens - toon_tokens
        savings_percent = (savings / json_tokens * 100) if json_tokens > 0 else 0

        return {
            "json_tokens": json_tokens,
            "toon_tokens": toon_tokens,
            "savings_tokens": savings,
            "savings_percent": round(savings_percent, 1),
            "format_used": self.format_name,
        }


class AgentMessage:
    """
    Structured message for inter-agent communication.

    Uses TOON format for token efficiency.

    Examples:
        >>> msg = AgentMessage(
        ...     from_agent="orchestrator",
        ...     to_agent="bug-fixer",
        ...     action="fix_bugs",
        ...     payload={"files": ["app.py", "utils.py"]}
        ... )
        >>> toon_str = msg.to_toon()
        >>>
        >>> # Agent receives and decodes
        >>> received = AgentMessage.from_toon(toon_str)
    """

    def __init__(
        self,
        from_agent: str,
        to_agent: str,
        action: str,
        payload: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Create agent message.

        Args:
            from_agent: Source agent ID
            to_agent: Destination agent ID
            action: Action to perform
            payload: Message data
            metadata: Optional metadata (timestamps, IDs, etc.)
        """
        self.from_agent = from_agent
        self.to_agent = to_agent
        self.action = action
        self.payload = payload
        self.metadata = metadata or {}
        self.codec = ToonCodec()

    def to_toon(self) -> str:
        """
        Encode message to TOON format.

        Returns:
            TOON-encoded message string
        """
        data = {
            "from": self.from_agent,
            "to": self.to_agent,
            "action": self.action,
            "payload": self.payload,
            "metadata": self.metadata,
        }
        return self.codec.encode(data)

    @classmethod
    def from_toon(cls, toon_str: str) -> "AgentMessage":
        """
        Decode TOON message.

        Args:
            toon_str: TOON-encoded message

        Returns:
            AgentMessage instance
        """
        codec = ToonCodec()
        data = codec.decode(toon_str)

        return cls(
            from_agent=data["from"],
            to_agent=data["to"],
            action=data["action"],
            payload=data["payload"],
            metadata=data.get("metadata", {}),
        )

    def __repr__(self) -> str:
        return f"AgentMessage(from={self.from_agent}, to={self.to_agent}, action={self.action})"


# Convenience functions
def encode_for_agent(data: Any) -> str:
    """
    Quick encode data for agent communication.

    Args:
        data: Data to encode

    Returns:
        TOON-encoded string
    """
    codec = ToonCodec()
    return codec.encode(data)


def decode_from_agent(toon_str: str) -> Any:
    """
    Quick decode data from agent communication.

    Args:
        toon_str: TOON-encoded string

    Returns:
        Decoded Python object
    """
    codec = ToonCodec()
    return codec.decode(toon_str)


def is_toon_available() -> bool:
    """
    Check if TOON format library is installed.

    Returns:
        True if toon_format is available, False otherwise
    """
    return TOON_AVAILABLE
