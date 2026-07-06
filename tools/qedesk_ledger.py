#!/usr/bin/env python3
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = PROJECT_ROOT / "qedesk-router.json"


def load_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def ledger_path(config: dict[str, Any]) -> Path:
    configured = Path(config.get("ledger", {}).get("path", "build/qedesk-ledger.sqlite"))
    if not configured.is_absolute():
        configured = PROJECT_ROOT / configured
    configured.parent.mkdir(parents=True, exist_ok=True)
    return configured


def connect(config: dict[str, Any] | None = None) -> sqlite3.Connection:
    config = config or load_config()
    conn = sqlite3.connect(ledger_path(config))
    init(conn)
    return conn


def init(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ledger (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          created_at TEXT NOT NULL,
          worksheet_id TEXT NOT NULL,
          node_id TEXT NOT NULL,
          stage TEXT NOT NULL,
          tier TEXT NOT NULL,
          model_name TEXT NOT NULL,
          prompt_tokens INTEGER NOT NULL DEFAULT 0,
          completion_tokens INTEGER NOT NULL DEFAULT 0,
          estimated_cost_usd REAL NOT NULL DEFAULT 0,
          elapsed_ms INTEGER NOT NULL DEFAULT 0,
          outcome TEXT NOT NULL,
          lean_status TEXT NOT NULL DEFAULT 'unchecked',
          error_type TEXT,
          tags_json TEXT NOT NULL DEFAULT '{}'
        )
        """
    )
    conn.commit()


def model_cost(
    config: dict[str, Any],
    tier: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> float:
    model = config["models"][tier]
    input_rate = float(model.get("input_usd_per_mtok", 0))
    output_rate = float(model.get("output_usd_per_mtok", 0))
    return (prompt_tokens * input_rate + completion_tokens * output_rate) / 1_000_000


def record_call(
    conn: sqlite3.Connection,
    *,
    config: dict[str, Any],
    worksheet_id: str,
    node_id: str,
    stage: str,
    tier: str,
    model_name: str,
    prompt_tokens: int,
    completion_tokens: int,
    elapsed_ms: int,
    outcome: str,
    lean_status: str = "unchecked",
    error_type: str | None = None,
    tags: dict[str, Any] | None = None,
) -> None:
    estimated_cost = model_cost(config, tier, prompt_tokens, completion_tokens)
    conn.execute(
        """
        INSERT INTO ledger (
          created_at, worksheet_id, node_id, stage, tier, model_name,
          prompt_tokens, completion_tokens, estimated_cost_usd, elapsed_ms,
          outcome, lean_status, error_type, tags_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.now(timezone.utc).isoformat(),
            worksheet_id,
            node_id,
            stage,
            tier,
            model_name,
            prompt_tokens,
            completion_tokens,
            estimated_cost,
            elapsed_ms,
            outcome,
            lean_status,
            error_type,
            json.dumps(tags or {}, sort_keys=True),
        ),
    )
    conn.commit()


def worksheet_tokens(conn: sqlite3.Connection, worksheet_id: str) -> int:
    row = conn.execute(
        """
        SELECT COALESCE(SUM(prompt_tokens + completion_tokens), 0)
        FROM ledger
        WHERE worksheet_id = ?
        """,
        (worksheet_id,),
    ).fetchone()
    return int(row[0] or 0)


def node_failures(conn: sqlite3.Connection, worksheet_id: str, node_id: str, tier: str | None = None) -> int:
    params: list[Any] = [worksheet_id, node_id]
    tier_filter = ""
    if tier:
        tier_filter = "AND tier = ?"
        params.append(tier)
    row = conn.execute(
        f"""
        SELECT COUNT(*)
        FROM ledger
        WHERE worksheet_id = ?
          AND node_id = ?
          AND outcome IN ('fail', 'escalated', 'abandoned')
          {tier_filter}
        """,
        params,
    ).fetchone()
    return int(row[0] or 0)


def summary(conn: sqlite3.Connection, worksheet_id: str | None = None) -> dict[str, Any]:
    where = ""
    params: tuple[Any, ...] = ()
    if worksheet_id:
        where = "WHERE worksheet_id = ?"
        params = (worksheet_id,)

    total = conn.execute(
        f"""
        SELECT
          COUNT(*),
          COALESCE(SUM(prompt_tokens), 0),
          COALESCE(SUM(completion_tokens), 0),
          COALESCE(SUM(estimated_cost_usd), 0),
          COUNT(DISTINCT node_id)
        FROM ledger
        {where}
        """,
        params,
    ).fetchone()

    by_model = conn.execute(
        f"""
        SELECT model_name, COUNT(*), COALESCE(SUM(prompt_tokens + completion_tokens), 0),
               COALESCE(SUM(estimated_cost_usd), 0)
        FROM ledger
        {where}
        GROUP BY model_name
        ORDER BY SUM(estimated_cost_usd) DESC
        """,
        params,
    ).fetchall()

    calls, prompt, completion, cost, nodes = total
    return {
        "calls": int(calls or 0),
        "prompt_tokens": int(prompt or 0),
        "completion_tokens": int(completion or 0),
        "estimated_cost_usd": float(cost or 0),
        "distinct_nodes": int(nodes or 0),
        "cost_per_checked_node": float(cost or 0) / int(nodes or 1),
        "by_model": [
            {
                "model": row[0],
                "calls": int(row[1] or 0),
                "tokens": int(row[2] or 0),
                "estimated_cost_usd": float(row[3] or 0),
            }
            for row in by_model
        ],
    }
