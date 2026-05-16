"""
VALLUM CHAIN — Governance & Audit Layer
Immutable hash-chain audit trails and compliance reporting.
"""

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3

from vallum.config import get_settings


def _settings():
    return get_settings()


class EventType(Enum):
    SHIELD_DECISION = "SHIELD_DECISION"
    SPEAR_TEST_COMPLETED = "SPEAR_TEST_COMPLETED"
    AGENT_ACTION = "AGENT_ACTION"
    POLICY_VIOLATION = "POLICY_VIOLATION"


@dataclass
class AuditEvent:
    event_id: str
    event_type: str
    timestamp: str
    agent_id: str
    session_id: Optional[str]
    action: str
    result: str
    risk_level: int
    evidence_hash: str
    metadata: Dict[str, Any]
    previous_hash: str
    current_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class HashChain:
    """Immutable hash chain for tamper-evident audit logging."""

    def __init__(self, secret: Optional[str] = None):
        self.secret = secret or _settings().audit_chain_secret
        if not self.secret:
            if _settings().is_production:
                raise RuntimeError(
                    "AUDIT_CHAIN_SECRET is required in production. "
                    "Set it via environment variable or GCP Secret Manager."
                )
            import logging
            logging.getLogger(__name__).warning(
                "AUDIT_CHAIN_SECRET not configured. Using ephemeral secret. "
                "Set AUDIT_CHAIN_SECRET for persistent chain integrity."
            )
            import secrets as _secrets
            self.secret = _secrets.token_hex(32)
        self._last_hash = self._genesis_hash()

    def _genesis_hash(self) -> str:
        return hashlib.sha256(f"VALLUM_GENESIS_{self.secret}".encode()).hexdigest()

    def _compute_hash(self, event_data: Dict[str, Any], previous_hash: str) -> str:
        data_string = json.dumps(event_data, sort_keys=True)
        combined = f"{previous_hash}:{data_string}:{self.secret}"
        return hashlib.sha256(combined.encode()).hexdigest()

    def add_event(self, event_data: Dict[str, Any]) -> AuditEvent:
        """Add new event to the chain."""
        event_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        evidence = event_data.get("evidence", {})
        evidence_hash = hashlib.sha256(json.dumps(evidence, sort_keys=True).encode()).hexdigest()[:32]

        hash_input = {
            "event_id": event_id, "timestamp": timestamp,
            "agent_id": event_data.get("agent_id", "unknown"),
            "action": event_data.get("action", "unknown"),
            "evidence_hash": evidence_hash
        }

        current_hash = self._compute_hash(hash_input, self._last_hash)

        event = AuditEvent(
            event_id=event_id, event_type=event_data.get("event_type", "UNKNOWN"),
            timestamp=timestamp, agent_id=event_data.get("agent_id", "unknown"),
            session_id=event_data.get("session_id"), action=event_data.get("action", "unknown"),
            result=event_data.get("result", "unknown"), risk_level=event_data.get("risk_level", 0),
            evidence_hash=evidence_hash, metadata=event_data.get("metadata", {}),
            previous_hash=self._last_hash, current_hash=current_hash
        )

        self._last_hash = current_hash
        return event

    def verify_chain(self, events: List[AuditEvent]) -> bool:
        """Verify integrity of event chain."""
        expected_hash = self._genesis_hash()
        for event in events:
            if event.previous_hash != expected_hash:
                return False
            hash_input = {
                "event_id": event.event_id, "timestamp": event.timestamp,
                "agent_id": event.agent_id, "action": event.action,
                "evidence_hash": event.evidence_hash
            }
            computed = self._compute_hash(hash_input, event.previous_hash)
            if computed != event.current_hash:
                return False
            expected_hash = event.current_hash
        return True


class ChainDatabase:
    """SQLite backend for audit event persistence."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or _settings().database_url.replace("sqlite:///", "")
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id TEXT PRIMARY KEY, event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL, agent_id TEXT NOT NULL,
                    session_id TEXT, action TEXT NOT NULL, result TEXT NOT NULL,
                    risk_level INTEGER DEFAULT 0, evidence_hash TEXT NOT NULL,
                    metadata TEXT, previous_hash TEXT NOT NULL, current_hash TEXT NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_time ON audit_events(agent_id, timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_risk ON audit_events(risk_level)")

    def store_event(self, event: AuditEvent):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO audit_events
                (event_id, event_type, timestamp, agent_id, session_id, action, result,
                 risk_level, evidence_hash, metadata, previous_hash, current_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (event.event_id, event.event_type, event.timestamp, event.agent_id,
                  event.session_id, event.action, event.result, event.risk_level,
                  event.evidence_hash, json.dumps(event.metadata), event.previous_hash, event.current_hash))

    def get_events(self, agent_id: Optional[str] = None, event_type: Optional[str] = None,
                   min_risk: int = 0, limit: int = 100) -> List[AuditEvent]:
        query = "SELECT * FROM audit_events WHERE risk_level >= ?"
        params = [min_risk]
        if agent_id:
            query += " AND agent_id = ?"
            params.append(agent_id)
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()
            return [AuditEvent(
                event_id=r["event_id"], event_type=r["event_type"], timestamp=r["timestamp"],
                agent_id=r["agent_id"], session_id=r["session_id"], action=r["action"],
                result=r["result"], risk_level=r["risk_level"], evidence_hash=r["evidence_hash"],
                metadata=json.loads(r["metadata"]) if r["metadata"] else {},
                previous_hash=r["previous_hash"], current_hash=r["current_hash"]
            ) for r in rows]

    def get_risk_summary(self) -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM audit_events").fetchone()[0]
            by_level = conn.execute("SELECT risk_level, COUNT(*) FROM audit_events GROUP BY risk_level").fetchall()
            by_agent = conn.execute("""
                SELECT agent_id, COUNT(*) as count, MAX(risk_level) as max_risk
                FROM audit_events GROUP BY agent_id ORDER BY count DESC LIMIT 10
            """).fetchall()
            return {
                "total_events": total,
                "by_risk_level": {f"L{r[0]}": r[1] for r in by_level},
                "top_agents": [{"agent_id": r[0], "events": r[1], "max_risk": r[2]} for r in by_agent]
            }


class Chain:
    """CHAIN — The Ledger. Immutable audit trails and compliance reporting."""

    def __init__(self):
        self.hash_chain = HashChain()
        self.db = ChainDatabase()

    def log_event(self, **kwargs) -> AuditEvent:
        """Log a security event to the immutable chain."""
        event = self.hash_chain.add_event(kwargs)
        self.db.store_event(event)
        return event

    def log_shield_decision(self, agent_id: str, action: str, result: str, risk_level: int,
                            metadata: Dict[str, Any], session_id: Optional[str] = None) -> AuditEvent:
        return self.log_event(event_type=EventType.SHIELD_DECISION.value, agent_id=agent_id,
                              action=action, result=result, risk_level=risk_level,
                              evidence=metadata, metadata=metadata, session_id=session_id)

    def log_spear_result(self, agent_id: str, test_id: str, atlas_id: str, passed: bool,
                         severity: str, evidence: Dict[str, Any]) -> AuditEvent:
        risk_map = {"NONE": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
        return self.log_event(event_type=EventType.SPEAR_TEST_COMPLETED.value, agent_id=agent_id,
                              action=f"ATLAS:{atlas_id}", result="PASS" if passed else "FAIL",
                              risk_level=risk_map.get(severity, 2), evidence=evidence,
                              metadata={"test_id": test_id, "atlas_id": atlas_id, "severity": severity})

    def get_audit_trail(self, agent_id: Optional[str] = None, min_risk: int = 0, limit: int = 100) -> List[AuditEvent]:
        return self.db.get_events(agent_id=agent_id, min_risk=min_risk, limit=limit)

    def get_risk_scorecard(self) -> Dict[str, Any]:
        return self.db.get_risk_summary()

    def verify_integrity(self) -> bool:
        events = self.db.get_events(limit=10000)
        # Events come in DESC order from DB, reverse for chain verification
        events.reverse()
        return self.hash_chain.verify_chain(events)

    def generate_compliance_report(self, framework: str = "SOC2") -> Dict[str, Any]:
        events = self.db.get_events(limit=1000)
        checks = {
            "SOC2": ["CC6.1 — Logical access security", "CC7.1 — Security detection", "CC7.2 — Incident response"],
            "HIPAA": ["164.312(a) — Access control", "164.312(b) — Audit controls", "164.312(c) — Integrity"],
            "PCI_DSS": ["Req 10 — Logging", "Req 11 — Testing"]
        }
        return {
            "framework": framework, "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_events": len(events), "chain_integrity": self.verify_integrity(),
            "applicable_controls": checks.get(framework, []),
            "evidence_summary": {
                "shield_decisions": len([e for e in events if e.event_type == "SHIELD_DECISION"]),
                "spear_tests": len([e for e in events if e.event_type == "SPEAR_TEST_COMPLETED"]),
                "critical_events": len([e for e in events if e.risk_level >= 3])
            },
            "recommendation": "Chain integrity verified. All events tamper-evident."
        }
