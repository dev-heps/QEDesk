#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import qedesk_ledger
from qedesk_sync import (
    GENERATED_BEGIN,
    GENERATED_END,
    all_blueprint_nodes,
    extract_blueprint_nodes,
    extract_lean_decls,
    read_text,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEX = PROJECT_ROOT / "src" / "main.tex"
DEFAULT_LEAN = PROJECT_ROOT / "src" / "Proof.lean"

STAGE_SCHEMAS = {
    "audit": {
        "node_id": "string",
        "verdict": "ok | gap | unclear | false",
        "gap_type": "none | quantifier_drift | hidden_premise | definition_mismatch | statement_drift | counterexample | skipped_reasoning | unknown",
        "severity": "none | low | medium | high",
        "local_issue": "one or two sentences",
        "repair_hint": "study-oriented hint, not a full proof",
        "suggested_next_target": "optional Lean/local subgoal",
        "confidence": "number from 0 to 1",
    },
    "formalize": {
        "node_id": "string",
        "lean_statement": "Lean statement or skeleton only",
        "required_parents": ["parent node ids"],
        "informal_to_formal_notes": ["short notes"],
        "risk_flags": ["statement drift risks"],
        "confidence": "number from 0 to 1",
    },
    "repair": {
        "node_id": "string",
        "diagnosis": "minimal explanation of the Lean/local logic failure",
        "minimal_patch_hint": "what to try next, not a completed proof",
        "statement_drift_check": "whether the statement changed meaning",
        "next_lean_step": "small next command/tactic/lemma candidate",
        "confidence": "number from 0 to 1",
    },
}


def project_path(value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def strip_generated_map(tex_text: str) -> str:
    if GENERATED_BEGIN not in tex_text:
        return tex_text
    before, rest = tex_text.split(GENERATED_BEGIN, 1)
    _generated, after = rest.split(GENERATED_END, 1)
    return before + after


def approx_tokens(text: str) -> int:
    return max(1, (len(text) + 3) // 4)


def clip_text(text: str, token_budget: int) -> str:
    limit = max(64, token_budget * 4)
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 120].rstrip() + "\n...[clipped for budget]...\n" + text[-80:].lstrip()


def load_nodes(tex_path: Path, lean_path: Path = DEFAULT_LEAN) -> list[dict[str, Any]]:
    tex_text = read_text(tex_path)
    lean_text = read_text(lean_path) if lean_path.exists() else ""
    decls = extract_lean_decls(lean_text) if lean_text else []
    parsed_nodes, _gaps = extract_blueprint_nodes(tex_text, decls)
    nodes = all_blueprint_nodes(decls, parsed_nodes)

    if not nodes:
        body = strip_generated_map(tex_text)
        return [
            {
                "id": tex_path.stem,
                "kind": "worksheet",
                "title": tex_path.name,
                "lean_decl": None,
                "status": "open",
                "uses": [],
                "body": body,
                "span": {"start_line": 1, "end_line": len(tex_text.splitlines())},
            }
        ]

    return [
        {
            "id": node.id,
            "kind": node.kind,
            "title": node.title,
            "lean_decl": node.lean_decl,
            "status": node.status,
            "uses": node.uses,
            "body": node.body,
            "span": {"start_line": node.start_line, "end_line": node.end_line},
        }
        for node in nodes
    ]


def node_map(nodes: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {node["id"]: node for node in nodes}


def default_worksheet_id(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")
    except ValueError:
        return path.name


def remaining_budget(config: dict[str, Any], conn: Any, worksheet_id: str) -> int:
    cap = int(config.get("budget", {}).get("worksheet_tokens", 12000))
    used = qedesk_ledger.worksheet_tokens(conn, worksheet_id)
    return max(0, cap - used)


def route_tier(
    config: dict[str, Any],
    conn: Any,
    worksheet_id: str,
    node_id: str,
    *,
    error_type: str | None = None,
) -> str:
    routing = config.get("routing", {})
    critic_errors = set(routing.get("critic_error_types", []))
    retries = routing.get("retries", {})

    if error_type and error_type in critic_errors:
        return "critic"

    flash_failures = qedesk_ledger.node_failures(conn, worksheet_id, node_id, "flash")
    if flash_failures < int(retries.get("flash", 2)):
        return "flash"

    pro_failures = qedesk_ledger.node_failures(conn, worksheet_id, node_id, "pro")
    if pro_failures < int(retries.get("pro", 1)):
        return "pro"

    return "critic"


def parent_contexts(nodes_by_id: dict[str, dict[str, Any]], node: dict[str, Any]) -> list[dict[str, str]]:
    parents: list[dict[str, str]] = []
    for parent_id in node.get("uses", [])[:3]:
        parent = nodes_by_id.get(parent_id)
        if not parent:
            continue
        parents.append(
            {
                "id": parent["id"],
                "kind": parent["kind"],
                "title": parent["title"],
                "status": parent["status"],
                "body": clip_text(parent.get("body", ""), 80),
            }
        )
    return parents


def stage_instruction(stage: str) -> str:
    if stage == "audit":
        return (
            "Audit only the local mathematical reasoning. Identify quantifier "
            "mistakes, hidden premises, false implications, definition mismatches, "
            "or skipped steps. Do not complete the proof."
        )
    if stage == "formalize":
        return (
            "Produce a Lean statement or small skeleton for this node only. Keep "
            "it faithful to the informal statement and flag any statement drift."
        )
    if stage == "repair":
        return (
            "Given the Lean/local error, explain the smallest repair direction. "
            "Do not rewrite the whole proof."
        )
    raise ValueError(f"unknown stage: {stage}")


def build_messages(
    *,
    config: dict[str, Any],
    stage: str,
    node: dict[str, Any],
    parents: list[dict[str, str]],
    worksheet_id: str,
    budget_remaining: int,
    lean_error: str = "",
    error_type: str | None = None,
) -> list[dict[str, str]]:
    budget = config.get("budget", {})
    node_tokens = int(budget.get("node_input_tokens", 384))
    error_tokens = int(budget.get("lean_error_tokens", 320))
    payload = {
        "stage": stage,
        "worksheet_id": worksheet_id,
        "node": {
            **{key: node.get(key) for key in ["id", "kind", "title", "lean_decl", "status", "uses", "span"]},
            "body": clip_text(str(node.get("body", "")), node_tokens),
        },
        "parents": parents,
        "lean_error": clip_text(lean_error, error_tokens) if lean_error else "",
        "error_type": error_type,
        "remaining_token_budget_for_worksheet": budget_remaining,
        "response_schema": STAGE_SCHEMAS[stage],
    }
    system = (
        "You are QEDesk's proof-audit router. AI is an auditor and proposer; "
        "Lean 4 is the final verifier. Return compact JSON only. Never provide "
        "a full finished proof unless explicitly asked by the human outside this "
        "tool. Prefer local hints, typed assumptions, and small subgoals."
    )
    user = {
        "instruction": stage_instruction(stage),
        "policy": [
            "Do not use chain-of-thought prose.",
            "Do not invent unavailable Lean library names.",
            "If the statement is ambiguous, say what must be clarified.",
            "Keep the answer short enough for the remaining budget.",
        ],
        "payload": payload,
    }
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(user, ensure_ascii=False, separators=(",", ":"))},
    ]


def parse_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    try:
        value = json.loads(text)
        return value if isinstance(value, dict) else {"value": value}
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            try:
                value = json.loads(text[start : end + 1])
                return value if isinstance(value, dict) else {"value": value}
            except json.JSONDecodeError:
                pass
    return {"raw_text": text, "parse_error": "model did not return a JSON object"}


def openrouter_client(config: dict[str, Any]) -> Any:
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set. Use --dry-run or create .env and restart QEDesk.")

    from openai import OpenAI

    openrouter = config.get("openrouter", {})
    headers = {
        "HTTP-Referer": os.environ.get(
            "OPENROUTER_HTTP_REFERER",
            openrouter.get("http_referer", "https://github.com/qedesk/qedesk"),
        ),
        "X-Title": os.environ.get("OPENROUTER_TITLE", openrouter.get("title", "QEDesk")),
    }
    return OpenAI(
        base_url=openrouter.get("base_url", "https://openrouter.ai/api/v1"),
        api_key=api_key,
        default_headers=headers,
    )


def call_model(
    *,
    config: dict[str, Any],
    conn: Any,
    worksheet_id: str,
    node_id: str,
    stage: str,
    tier: str,
    messages: list[dict[str, str]],
    dry_run: bool,
    error_type: str | None = None,
) -> dict[str, Any]:
    model_id = config["models"][tier]["id"]
    max_tokens = int(config.get("budget", {}).get("node_output_tokens", 256))
    prompt_estimate = approx_tokens(json.dumps(messages, ensure_ascii=False))

    if dry_run:
        return {
            "dry_run": True,
            "stage": stage,
            "tier": tier,
            "model": model_id,
            "node_id": node_id,
            "estimated_prompt_tokens": prompt_estimate,
            "max_completion_tokens": max_tokens,
            "messages": messages,
        }

    client = openrouter_client(config)
    started = time.perf_counter()
    try:
        try:
            response = client.chat.completions.create(
                model=model_id,
                messages=messages,
                temperature=0.1,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
            )
        except Exception as exc:
            if "response_format" not in str(exc):
                raise
            response = client.chat.completions.create(
                model=model_id,
                messages=messages,
                temperature=0.1,
                max_tokens=max_tokens,
            )
    except Exception as exc:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        qedesk_ledger.record_call(
            conn,
            config=config,
            worksheet_id=worksheet_id,
            node_id=node_id,
            stage=stage,
            tier=tier,
            model_name=model_id,
            prompt_tokens=prompt_estimate,
            completion_tokens=0,
            elapsed_ms=elapsed_ms,
            outcome="fail",
            error_type=error_type,
            tags={"exception": type(exc).__name__, "message": str(exc)[:500]},
        )
        raise

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    content = response.choices[0].message.content or ""
    usage = getattr(response, "usage", None)
    prompt_tokens = int(getattr(usage, "prompt_tokens", prompt_estimate) or prompt_estimate)
    completion_tokens = int(getattr(usage, "completion_tokens", approx_tokens(content)) or approx_tokens(content))
    parsed = parse_json_object(content)
    outcome = "ok" if "parse_error" not in parsed else "fail"

    qedesk_ledger.record_call(
        conn,
        config=config,
        worksheet_id=worksheet_id,
        node_id=node_id,
        stage=stage,
        tier=tier,
        model_name=model_id,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        elapsed_ms=elapsed_ms,
        outcome=outcome,
        error_type=error_type,
        tags={"content_length": len(content)},
    )
    return {
        "dry_run": False,
        "stage": stage,
        "tier": tier,
        "model": model_id,
        "node_id": node_id,
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "elapsed_ms": elapsed_ms,
        },
        "response": parsed,
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def select_nodes(nodes: list[dict[str, Any]], node_id: str | None, max_nodes: int) -> list[dict[str, Any]]:
    if node_id:
        selected = [node for node in nodes if node["id"] == node_id]
        if not selected:
            available = ", ".join(node["id"] for node in nodes)
            raise SystemExit(f"Unknown node '{node_id}'. Available nodes: {available}")
        return selected
    if max_nodes > 0:
        return nodes[:max_nodes]
    return nodes


def run_stage(args: argparse.Namespace, stage: str) -> int:
    config = qedesk_ledger.load_config(project_path(args.config))
    conn = qedesk_ledger.connect(config)
    tex_path = project_path(args.path)
    worksheet_id = args.worksheet or default_worksheet_id(tex_path)
    nodes = load_nodes(tex_path, project_path(args.lean))
    nodes_by_id = node_map(nodes)
    selected = select_nodes(nodes, args.node, args.max_nodes)
    lean_error = ""
    if getattr(args, "lean_error", None):
        lean_error = args.lean_error
    if getattr(args, "error_file", None):
        lean_error = read_text(project_path(args.error_file))

    results = []
    for node in selected:
        budget_remaining = remaining_budget(config, conn, worksheet_id)
        tier = args.tier or route_tier(
            config,
            conn,
            worksheet_id,
            node["id"],
            error_type=getattr(args, "error_type", None),
        )
        messages = build_messages(
            config=config,
            stage=stage,
            node=node,
            parents=parent_contexts(nodes_by_id, node),
            worksheet_id=worksheet_id,
            budget_remaining=budget_remaining,
            lean_error=lean_error,
            error_type=getattr(args, "error_type", None),
        )
        results.append(
            call_model(
                config=config,
                conn=conn,
                worksheet_id=worksheet_id,
                node_id=node["id"],
                stage=stage,
                tier=tier,
                messages=messages,
                dry_run=args.dry_run,
                error_type=getattr(args, "error_type", None),
            )
        )

    payload = {"stage": stage, "worksheet_id": worksheet_id, "results": results}
    if args.out:
        write_json(project_path(args.out), payload)
        print(f"Wrote {args.out}")
    else:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def cmd_route(args: argparse.Namespace) -> int:
    config = qedesk_ledger.load_config(project_path(args.config))
    conn = qedesk_ledger.connect(config)
    worksheet_id = args.worksheet or "manual"
    tier = route_tier(config, conn, worksheet_id, args.node_id, error_type=args.error_type)
    print(
        json.dumps(
            {
                "worksheet_id": worksheet_id,
                "node_id": args.node_id,
                "tier": tier,
                "model": config["models"][tier]["id"],
                "error_type": args.error_type,
            },
            indent=2,
        )
    )
    return 0


def cmd_cost(args: argparse.Namespace) -> int:
    config = qedesk_ledger.load_config(project_path(args.config))
    conn = qedesk_ledger.connect(config)
    data = qedesk_ledger.summary(conn, args.worksheet)
    if args.json:
        print(json.dumps(data, indent=2))
        return 0
    print(f"Calls: {data['calls']}")
    print(f"Prompt tokens: {data['prompt_tokens']}")
    print(f"Completion tokens: {data['completion_tokens']}")
    print(f"Estimated cost: ${data['estimated_cost_usd']:.6f}")
    print(f"Cost per checked node: ${data['cost_per_checked_node']:.6f}")
    for row in data["by_model"]:
        print(f"- {row['model']}: {row['calls']} call(s), {row['tokens']} token(s), ${row['estimated_cost_usd']:.6f}")
    return 0


def cmd_init_ledger(args: argparse.Namespace) -> int:
    config = qedesk_ledger.load_config(project_path(args.config))
    conn = qedesk_ledger.connect(config)
    print(f"Ledger ready: {qedesk_ledger.ledger_path(config)}")
    conn.close()
    return 0


def add_stage_parser(subparsers: Any, name: str, default_out: str) -> None:
    parser = subparsers.add_parser(name)
    parser.add_argument("path", nargs="?", default="src/main.tex")
    parser.add_argument("--lean", default="src/Proof.lean")
    parser.add_argument("--node")
    parser.add_argument("--worksheet")
    parser.add_argument("--tier", choices=["flash", "pro", "critic"])
    parser.add_argument("--max-nodes", type=int, default=0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--out", default=default_out)
    parser.add_argument("--config", default=str(qedesk_ledger.DEFAULT_CONFIG))
    if name == "repair":
        parser.add_argument("--lean-error", default="")
        parser.add_argument("--error-file")
        parser.add_argument("--error-type")
    parser.set_defaults(func=lambda args, stage=name: run_stage(args, stage))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="QEDesk OpenRouter model router and cost ledger.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_stage_parser(subparsers, "audit", "build/qedesk-audit.json")
    add_stage_parser(subparsers, "formalize", "build/qedesk-formalize.json")
    add_stage_parser(subparsers, "repair", "build/qedesk-repair.json")

    route = subparsers.add_parser("route")
    route.add_argument("node_id")
    route.add_argument("--worksheet")
    route.add_argument("--error-type")
    route.add_argument("--config", default=str(qedesk_ledger.DEFAULT_CONFIG))
    route.set_defaults(func=cmd_route)

    cost = subparsers.add_parser("cost")
    cost.add_argument("--worksheet")
    cost.add_argument("--json", action="store_true")
    cost.add_argument("--config", default=str(qedesk_ledger.DEFAULT_CONFIG))
    cost.set_defaults(func=cmd_cost)

    init_ledger = subparsers.add_parser("init-ledger")
    init_ledger.add_argument("--config", default=str(qedesk_ledger.DEFAULT_CONFIG))
    init_ledger.set_defaults(func=cmd_init_ledger)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.func(args) or 0)
    except RuntimeError as exc:
        print(f"qedesk router: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
