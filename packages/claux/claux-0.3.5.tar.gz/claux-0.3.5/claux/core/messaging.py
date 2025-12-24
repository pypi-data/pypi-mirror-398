"""
Agent Messaging Protocol using TOON Format.

Provides standardized message types and encoding for inter-agent communication.
Reduces token usage by ~40% compared to JSON while maintaining compatibility.
"""

from typing import Any, Dict, Optional
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime

from claux.core.toon import ToonCodec, AgentMessage


class MessageType(str, Enum):
    """Standard message types for agent communication."""

    REQUEST = "request"
    RESPONSE = "response"
    ERROR = "error"
    STATUS = "status"
    PLAN = "plan"
    REPORT = "report"


@dataclass
class MessageMetadata:
    """Metadata for agent messages."""

    timestamp: str
    message_id: str
    session_id: Optional[str] = None
    parent_message_id: Optional[str] = None

    @classmethod
    def create(cls, session_id: Optional[str] = None, parent_id: Optional[str] = None):
        """Create metadata with auto-generated values."""
        import uuid

        return cls(
            timestamp=datetime.utcnow().isoformat() + "Z",
            message_id=str(uuid.uuid4()),
            session_id=session_id,
            parent_message_id=parent_id,
        )


class AgentProtocol:
    """
    Standardized protocol for agent-to-agent communication.

    Examples:
        >>> protocol = AgentProtocol()
        >>>
        >>> # Send plan to worker
        >>> msg = protocol.create_plan_message(
        ...     from_agent="orchestrator",
        ...     to_agent="bug-fixer",
        ...     plan_data={"bugs": [...], "strategy": "fix_by_priority"}
        ... )
        >>> toon_str = protocol.encode(msg)
        >>>
        >>> # Worker receives and decodes
        >>> received = protocol.decode(toon_str)
    """

    def __init__(self):
        self.codec = ToonCodec()

    def create_request(
        self,
        from_agent: str,
        to_agent: str,
        action: str,
        params: Dict[str, Any],
        metadata: Optional[MessageMetadata] = None,
    ) -> AgentMessage:
        """Create a request message."""
        return AgentMessage(
            from_agent=from_agent,
            to_agent=to_agent,
            action=action,
            payload={"type": MessageType.REQUEST, "params": params},
            metadata=asdict(metadata or MessageMetadata.create()),
        )

    def create_response(
        self,
        from_agent: str,
        to_agent: str,
        action: str,
        result: Any,
        success: bool = True,
        metadata: Optional[MessageMetadata] = None,
    ) -> AgentMessage:
        """Create a response message."""
        return AgentMessage(
            from_agent=from_agent,
            to_agent=to_agent,
            action=action,
            payload={"type": MessageType.RESPONSE, "success": success, "result": result},
            metadata=asdict(metadata or MessageMetadata.create()),
        )

    def create_plan_message(
        self,
        from_agent: str,
        to_agent: str,
        plan_data: Dict[str, Any],
        metadata: Optional[MessageMetadata] = None,
    ) -> AgentMessage:
        """Create a plan message for worker agents."""
        return AgentMessage(
            from_agent=from_agent,
            to_agent=to_agent,
            action="execute_plan",
            payload={"type": MessageType.PLAN, "plan": plan_data},
            metadata=asdict(metadata or MessageMetadata.create()),
        )

    def create_report_message(
        self,
        from_agent: str,
        to_agent: str,
        report_data: Dict[str, Any],
        metadata: Optional[MessageMetadata] = None,
    ) -> AgentMessage:
        """Create a report message from worker to orchestrator."""
        return AgentMessage(
            from_agent=from_agent,
            to_agent=to_agent,
            action="report_results",
            payload={"type": MessageType.REPORT, "report": report_data},
            metadata=asdict(metadata or MessageMetadata.create()),
        )

    def create_error_message(
        self,
        from_agent: str,
        to_agent: str,
        error: str,
        details: Optional[Dict[str, Any]] = None,
        metadata: Optional[MessageMetadata] = None,
    ) -> AgentMessage:
        """Create an error message."""
        return AgentMessage(
            from_agent=from_agent,
            to_agent=to_agent,
            action="error",
            payload={"type": MessageType.ERROR, "error": error, "details": details or {}},
            metadata=asdict(metadata or MessageMetadata.create()),
        )

    def encode(self, message: AgentMessage) -> str:
        """Encode message to TOON format."""
        return message.to_toon()

    def decode(self, toon_str: str) -> AgentMessage:
        """Decode TOON message."""
        return AgentMessage.from_toon(toon_str)

    def estimate_savings(self, message: AgentMessage) -> Dict[str, Any]:
        """Estimate token savings for this message."""
        data = {
            "from": message.from_agent,
            "to": message.to_agent,
            "action": message.action,
            "payload": message.payload,
            "metadata": message.metadata,
        }
        return self.codec.estimate_savings(data)


# Convenience functions
def create_plan(from_agent: str, to_agent: str, plan_data: Dict[str, Any]) -> str:
    """Quick function to create and encode a plan message."""
    protocol = AgentProtocol()
    msg = protocol.create_plan_message(from_agent, to_agent, plan_data)
    return protocol.encode(msg)


def create_report(from_agent: str, to_agent: str, report_data: Dict[str, Any]) -> str:
    """Quick function to create and encode a report message."""
    protocol = AgentProtocol()
    msg = protocol.create_report_message(from_agent, to_agent, report_data)
    return protocol.encode(msg)


def decode_message(toon_str: str) -> AgentMessage:
    """Quick function to decode a TOON message."""
    protocol = AgentProtocol()
    return protocol.decode(toon_str)
