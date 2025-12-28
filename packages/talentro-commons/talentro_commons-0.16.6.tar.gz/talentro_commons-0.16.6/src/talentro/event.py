import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from uuid import UUID, uuid4


@dataclass
class EventMeta:
    event_type: str = "generic"           # bv. "application.raw" of "application.normalized"
    source: Optional[str] = None          # bv. "indeed" / "dpg" / "leadads" / "integrations"
    schema: Optional[str] = None          # bv. "talentro.applications.raw.v1"
    trace_id: str = field(default_factory=lambda: str(uuid4()))
    correlation_id: Optional[str] = None # zet gelijk aan trace_id voor request/response chains
    idempotency_key: Optional[str] = None # (source, source_event_id) hash of inbound unique

    def to_headers(self) -> Dict[str, Any]:
        """Headers die je mee kunt sturen via RabbitMQ (Message.headers)."""
        h = {
            "x-event-type": self.event_type,
            "x-trace-id": self.trace_id,
        }
        if self.correlation_id:
            h["x-correlation-id"] = self.correlation_id
        if self.source:
            h["x-source"] = self.source
        if self.schema:
            h["x-schema"] = self.schema
        if self.idempotency_key:
            h["x-idempotency-key"] = self.idempotency_key
        return h


@dataclass
class Event:
    payload: Dict[str, Any]
    organization_id: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    meta: EventMeta = field(default_factory=EventMeta)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # Zorg voor ISO8601 UTC string voor datums
        d["created_at"] = self.created_at.isoformat()
        # UUIDs als strings in meta
        d["meta"]["trace_id"] = str(self.meta.trace_id)
        if d["meta"].get("correlation_id"):
            d["meta"]["correlation_id"] = str(self.meta.correlation_id)

        # Converteer UUIDs in payload naar strings
        d["payload"] = self._convert_uuids_to_str(self.payload)

        return d

    @staticmethod
    def _convert_uuids_to_str(obj: Any) -> Any:
        """Recursief UUIDs naar strings converteren in dicts/lists."""
        if isinstance(obj, UUID):
            return str(obj)
        elif isinstance(obj, dict):
            return {k: Event._convert_uuids_to_str(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [Event._convert_uuids_to_str(item) for item in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return obj

    def encode(self) -> bytes:
        """Serialize naar bytes voor RabbitMQ."""
        return json.dumps(self.to_dict(), separators=(",", ":"), ensure_ascii=False).encode("utf-8")

    @staticmethod
    def decode(data: bytes) -> "Event":
        """Handige inverse van encode() voor je consumers."""
        obj = json.loads(data.decode("utf-8"))
        meta = obj.get("meta") or {}
        ev = Event(
            payload=obj.get("payload") or {},
            organization_id=obj.get("organization_id"),
            created_at=datetime.fromisoformat(obj["created_at"]) if obj.get("created_at") else datetime.now(timezone.utc),
            meta=EventMeta(
                event_type=meta.get("event_type", "generic"),
                source=meta.get("source"),
                schema=meta.get("schema"),
                trace_id=UUID(meta["trace_id"]) if meta.get("trace_id") else str(uuid4()),
                correlation_id=UUID(meta["correlation_id"]) if meta.get("correlation_id") else None,
                idempotency_key=meta.get("idempotency_key"),
            ),
        )
        return ev

@dataclass
class Message:
    """Generieke AMQP message voor publish via exchanges."""
    event: Event
    exchange: str                      # bv. "applications"
    routing_key: str                   # bv. "applications.raw" of "applications.normalized"
    headers: Dict[str, Any] = field(default_factory=dict)
    persistent: bool = True

    def body(self) -> bytes:
        return self.event.encode()

    def merged_headers(self) -> Dict[str, Any]:
        base = {
            "x-created-at": self.event.created_at.isoformat(),
        }
        base.update(self.event.meta.to_headers())
        base.update(self.headers or {})
        return base

    # --- Backwards-compat: als je nog 'queue' code hebt, bied no-op property ---
    @property
    def queue(self):
        """Deprecated: aanwezig voor compatibiliteit met oude code die queue gebruikte."""
        return self.routing_key  # je oude code gebruikte routing_key==queue-naam
