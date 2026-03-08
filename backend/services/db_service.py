"""SQLite database service — persistent storage for users, sessions, interactions."""
import sqlite3
import uuid
import time
import os
from typing import Optional

DB_PATH = os.getenv("DB_PATH", "data/copilot.db")


class DBService:
    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    created_at INTEGER DEFAULT (strftime('%s','now'))
                );

                CREATE TABLE IF NOT EXISTS interactions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    query TEXT NOT NULL,
                    response TEXT NOT NULL,
                    model TEXT,
                    latency_ms INTEGER,
                    rating INTEGER DEFAULT 0,
                    timestamp INTEGER DEFAULT (strftime('%s','now'))
                );

                CREATE TABLE IF NOT EXISTS knowledge_gaps (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    confidence REAL DEFAULT 0.5,
                    suggestions TEXT,
                    resolved INTEGER DEFAULT 0,
                    detected_at INTEGER DEFAULT (strftime('%s','now'))
                );

                CREATE TABLE IF NOT EXISTS learning_progress (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    skill TEXT,
                    updated_at INTEGER DEFAULT (strftime('%s','now'))
                );
            """)

    # ── Users ───────────────────────────────────────────────────────
    def get_or_create_user(self, email: str) -> dict:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
            if row:
                return dict(row)
            user_id = str(uuid.uuid4())
            conn.execute("INSERT INTO users (user_id, email) VALUES (?,?)", (user_id, email))
            return {"user_id": user_id, "email": email}

    # ── Interactions ─────────────────────────────────────────────────
    def log_interaction(self, user_id: str, query: str, response: str, model: str, latency_ms: int):
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO interactions (id,user_id,query,response,model,latency_ms,timestamp) VALUES (?,?,?,?,?,?,?)",
                (str(uuid.uuid4()), user_id, query, response, model, latency_ms, int(time.time()))
            )
            # Extract topic from query (first 3 words as rough topic)
            topic = " ".join(query.split()[:3])
            conn.execute(
                "INSERT OR IGNORE INTO learning_progress (id,user_id,topic) VALUES (?,?,?)",
                (str(uuid.uuid4()), user_id, topic)
            )

    def get_recent_interactions(self, user_id: str, limit: int = 20) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM interactions WHERE user_id=? ORDER BY timestamp DESC LIMIT ?",
                (user_id, limit)
            ).fetchall()
            return [dict(r) for r in rows]

    def store_feedback(self, user_id: str, timestamp: int, rating: int):
        with self._conn() as conn:
            conn.execute(
                "UPDATE interactions SET rating=? WHERE user_id=? AND timestamp=?",
                (rating, user_id, timestamp)
            )

    # ── Knowledge Gaps ───────────────────────────────────────────────
    def save_knowledge_gap(self, user_id: str, topic: str, confidence: float, suggestions: list):
        import json
        with self._conn() as conn:
            # Update if exists, else insert
            existing = conn.execute(
                "SELECT id FROM knowledge_gaps WHERE user_id=? AND topic=?", (user_id, topic)
            ).fetchone()
            if existing:
                conn.execute(
                    "UPDATE knowledge_gaps SET confidence=?, suggestions=?, resolved=0 WHERE id=?",
                    (confidence, json.dumps(suggestions), existing["id"])
                )
            else:
                conn.execute(
                    "INSERT INTO knowledge_gaps (id,user_id,topic,confidence,suggestions) VALUES (?,?,?,?,?)",
                    (str(uuid.uuid4()), user_id, topic, confidence, json.dumps(suggestions))
                )

    def get_knowledge_gaps(self, user_id: str) -> list[dict]:
        import json
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM knowledge_gaps WHERE user_id=? ORDER BY detected_at DESC",
                (user_id,)
            ).fetchall()
            result = []
            for r in rows:
                d = dict(r)
                d["suggestions"] = json.loads(d.get("suggestions") or "[]")
                result.append(d)
            return result

    # ── Progress ─────────────────────────────────────────────────────
    def get_user_progress(self, user_id: str) -> dict:
        with self._conn() as conn:
            topics = [r[0] for r in conn.execute(
                "SELECT DISTINCT topic FROM learning_progress WHERE user_id=?", (user_id,)
            ).fetchall()]
            interaction_count = conn.execute(
                "SELECT COUNT(*) FROM interactions WHERE user_id=?", (user_id,)
            ).fetchone()[0]

        gaps = self.get_knowledge_gaps(user_id)

        return {
            "user_id": user_id,
            "progress": {
                "topics_covered": topics[:20],
                "total_topics": len(topics),
                "questions_answered": interaction_count,
                "skills_acquired": list({t.split()[0] for t in topics if t})[:10],
                "total_skills": len({t.split()[0] for t in topics if t}),
                "milestones": self._get_milestones(interaction_count),
            },
            "knowledge_gaps": [
                {
                    "gap_id": g["id"],
                    "topic": g["topic"],
                    "confidence_score": g["confidence"],
                    "suggestions": g["suggestions"],
                    "resolved": bool(g["resolved"]),
                    "detected_at": str(g["detected_at"]),
                }
                for g in gaps
            ],
            "interaction_stats": {"total_recent": interaction_count},
        }

    def _get_milestones(self, count: int) -> dict:
        milestones = {}
        if count >= 1:
            milestones["First Question Asked"] = "Achieved!"
        if count >= 10:
            milestones["10 Questions Milestone"] = "Achieved!"
        if count >= 25:
            milestones["25 Questions Club"] = "Achieved!"
        if count >= 50:
            milestones["50 Questions Expert"] = "Achieved!"
        return milestones
