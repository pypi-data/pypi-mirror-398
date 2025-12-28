"""
TIBET Safety Chip - Data Provenance Tracking

Beyond security: Track what happens to ALL data.
Every tab, every API call, every transformation leaves a trail.

"We know what we do with data" - and we can PROVE it.
"""

from dataclasses import dataclass, field
from typing import Optional, Any
from enum import Enum
import hashlib
import time
import json


class DataOperation(Enum):
    """What happened to the data."""
    READ = "read"
    WRITE = "write"
    TRANSFORM = "transform"
    SEND = "send"
    RECEIVE = "receive"
    STORE = "store"
    DELETE = "delete"
    COPY = "copy"
    ANALYZE = "analyze"
    DISPLAY = "display"
    ENCRYPT = "encrypt"
    DECRYPT = "decrypt"


class DataLocation(Enum):
    """Where the data lives."""
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    BROWSER_TAB = "browser_tab"
    CLIPBOARD = "clipboard"
    DATABASE = "database"
    API = "api"
    LLM_CONTEXT = "llm_context"
    USER_DISPLAY = "user_display"


@dataclass
class DataTrail:
    """Complete trail of what happened to a piece of data."""
    data_id: str
    content_hash: str
    operations: list[dict] = field(default_factory=list)
    current_location: DataLocation = DataLocation.MEMORY
    created_at: float = field(default_factory=time.time)
    tibet_chain: list[str] = field(default_factory=list)

    def record_operation(
        self,
        operation: DataOperation,
        actor: str,
        location: DataLocation,
        details: Optional[dict] = None
    ) -> str:
        """Record what just happened to this data."""
        token_id = f"trail_{self.data_id}_{len(self.operations)}"

        op_record = {
            "token_id": token_id,
            "timestamp": time.time(),
            "operation": operation.value,
            "actor": actor,
            "from_location": self.current_location.value,
            "to_location": location.value,
            "details": details or {},
            "tibet": {
                "erin": f"{operation.value} by {actor}",
                "eromheen": {"location": location.value},
                "erachter": f"Data moved: {self.current_location.value} -> {location.value}",
                "eraan": self.tibet_chain[-1] if self.tibet_chain else None,
            }
        }

        self.operations.append(op_record)
        self.current_location = location
        self.tibet_chain.append(token_id)

        return token_id

    def get_full_trail(self) -> dict:
        """Get complete provenance trail."""
        return {
            "data_id": self.data_id,
            "content_hash": self.content_hash,
            "created_at": self.created_at,
            "current_location": self.current_location.value,
            "operation_count": len(self.operations),
            "operations": self.operations,
            "tibet_chain": self.tibet_chain,
        }

    def to_json(self) -> str:
        """Export trail as JSON."""
        return json.dumps(self.get_full_trail(), indent=2)


class DataProvenanceTracker:
    """
    Track ALL data flows through the system.

    Every piece of data gets a trail:
    - Where it came from
    - What happened to it
    - Where it went
    - Who touched it

    This is how we PROVE what we do with data.
    """

    def __init__(self):
        self.trails: dict[str, DataTrail] = {}
        self.active_sessions: dict[str, list[str]] = {}  # session_id -> data_ids

    def register_data(
        self,
        content: Any,
        source: str,
        location: DataLocation = DataLocation.MEMORY,
        session_id: Optional[str] = None
    ) -> DataTrail:
        """Register new data entering the system."""
        content_str = str(content) if not isinstance(content, str) else content
        content_hash = hashlib.sha256(content_str.encode()).hexdigest()[:16]
        data_id = f"data_{int(time.time())}_{content_hash}"

        trail = DataTrail(
            data_id=data_id,
            content_hash=content_hash,
            current_location=location,
        )

        # Record initial creation
        trail.record_operation(
            DataOperation.RECEIVE,
            actor=source,
            location=location,
            details={"initial": True, "content_length": len(content_str)}
        )

        self.trails[data_id] = trail

        # Track in session if provided
        if session_id:
            if session_id not in self.active_sessions:
                self.active_sessions[session_id] = []
            self.active_sessions[session_id].append(data_id)

        return trail

    def track_browser_tab(
        self,
        tab_id: str,
        url: str,
        content: str,
        session_id: str
    ) -> DataTrail:
        """Track data from a browser tab - we know what tabs do."""
        trail = self.register_data(
            content,
            source=f"browser_tab:{tab_id}",
            location=DataLocation.BROWSER_TAB,
            session_id=session_id
        )

        # Browser tabs have specific behaviors we track
        trail.record_operation(
            DataOperation.READ,
            actor="browser_renderer",
            location=DataLocation.BROWSER_TAB,
            details={
                "url": url,
                "tab_id": tab_id,
                "action": "page_load",
            }
        )

        return trail

    def track_llm_input(
        self,
        content: str,
        model: str,
        session_id: str
    ) -> DataTrail:
        """Track data going into an LLM."""
        trail = self.register_data(
            content,
            source="user_or_system",
            location=DataLocation.MEMORY,
            session_id=session_id
        )

        trail.record_operation(
            DataOperation.SEND,
            actor="llm_client",
            location=DataLocation.LLM_CONTEXT,
            details={"model": model}
        )

        return trail

    def track_api_call(
        self,
        data: Any,
        endpoint: str,
        direction: str,  # "send" or "receive"
        session_id: str
    ) -> DataTrail:
        """Track data going to/from APIs."""
        trail = self.register_data(
            data,
            source=f"api:{endpoint}",
            location=DataLocation.API,
            session_id=session_id
        )

        op = DataOperation.SEND if direction == "send" else DataOperation.RECEIVE
        trail.record_operation(
            op,
            actor="api_client",
            location=DataLocation.NETWORK,
            details={"endpoint": endpoint}
        )

        return trail

    def get_session_trails(self, session_id: str) -> list[dict]:
        """Get all data trails for a session."""
        if session_id not in self.active_sessions:
            return []

        return [
            self.trails[data_id].get_full_trail()
            for data_id in self.active_sessions[session_id]
            if data_id in self.trails
        ]

    def prove_data_handling(self, data_id: str) -> dict:
        """
        Generate proof of how data was handled.

        This is how we answer: "What did you do with my data?"
        With cryptographic certainty.
        """
        if data_id not in self.trails:
            return {"error": "Data not found in registry"}

        trail = self.trails[data_id]
        return {
            "data_id": data_id,
            "proof": {
                "content_hash": trail.content_hash,
                "operations_count": len(trail.operations),
                "first_seen": trail.created_at,
                "current_location": trail.current_location.value,
                "tibet_chain": trail.tibet_chain,
                "full_trail": trail.operations,
            },
            "verification": hashlib.sha256(
                json.dumps(trail.operations).encode()
            ).hexdigest(),
        }


# Global tracker instance
_tracker = DataProvenanceTracker()


def track(content: Any, source: str, **kwargs) -> DataTrail:
    """Quick track function."""
    return _tracker.register_data(content, source, **kwargs)


def prove(data_id: str) -> dict:
    """Quick prove function."""
    return _tracker.prove_data_handling(data_id)


def get_tracker() -> DataProvenanceTracker:
    """Get the global tracker."""
    return _tracker
