from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional


ISO_UTC_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime(ISO_UTC_FORMAT)  # ISO 8601 UTC [web:67][web:70]


@dataclass(frozen=True)
class Message:
    type: str          # p.ej. "map.v1"
    source: str        # id agente origen
    target: str        # id/rol agente destino
    timestamp: str     # ISO 8601 UTC
    payload: Dict[str, Any]
    status: str        # p.ej. "PENDING", "OK", "ERROR"
    context: Dict[str, Any]

    def __post_init__(self) -> None:
        # Validaciones explícitas
        if not self.type:
            raise ValueError("type is required")
        if not self.source:
            raise ValueError("source is required")
        if not self.target:
            raise ValueError("target is required")
        try:
            datetime.strptime(self.timestamp, ISO_UTC_FORMAT)
        except ValueError as e:
            raise ValueError(
                f"timestamp must be ISO 8601 UTC like 2025-01-01T00:00:00Z"
            ) from e
        if self.payload is None:
            raise ValueError("payload is required")
        if not self.status:
            raise ValueError("status is required")
        if self.context is None:
            raise ValueError("context must be a dict (can be empty)")

    def to_json_dict(self) -> Dict[str, Any]:
        """Dict listo para pasarlo a json.dumps()."""
        return asdict(self) 