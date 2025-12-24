import sqlite3
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List
import hashlib

DB_PATH = Path(__file__).parent / "uaal_decisions.db"

@dataclass
class DecisionRecord:
    decision_id: str
    agent_id: str
    action: str
    policy: str
    outcome: str
    knowledge_hash: str
    parent_decision_id: Optional[str]
    decision_hash: str

def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with _get_conn() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS decisions (
            decision_id TEXT PRIMARY KEY,
            agent_id TEXT NOT NULL,
            action TEXT NOT NULL,
            policy TEXT NOT NULL,
            outcome TEXT NOT NULL,
            knowledge_hash TEXT NOT NULL,
            parent_decision_id TEXT
        )
        """)

        # 🔁 MIGRATION: add decision_hash if missing
        cols = [r["name"] for r in conn.execute("PRAGMA table_info(decisions)")]
        if "decision_hash" not in cols:
            conn.execute(
                "ALTER TABLE decisions ADD COLUMN decision_hash TEXT"
            )

def compute_decision_hash(
    decision_id,
    agent_id,
    action,
    policy,
    outcome,
    knowledge_hash,
    parent_hash=""
):
    payload = f"{decision_id}|{agent_id}|{action}|{policy}|{outcome}|{knowledge_hash}|{parent_hash}"
    return hashlib.sha256(payload.encode()).hexdigest()

def save_decision(record: DecisionRecord):
    init_db()
    with _get_conn() as conn:
        conn.execute("""
        INSERT OR REPLACE INTO decisions VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.decision_id,
            record.agent_id,
            record.action,
            record.policy,
            record.outcome,
            record.knowledge_hash,
            record.parent_decision_id,
            record.decision_hash
        ))

def get_decision(decision_id: str) -> DecisionRecord:
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM decisions WHERE decision_id = ?",
            (decision_id,)
        ).fetchone()

        if not row:
            raise KeyError(decision_id)

        return DecisionRecord(**dict(row))

def get_full_lineage(decision_id: str) -> List[DecisionRecord]:
    lineage = []
    current = get_decision(decision_id)

    while current:
        lineage.insert(0, current)
        if current.parent_decision_id:
            current = get_decision(current.parent_decision_id)
        else:
            break

    return lineage
