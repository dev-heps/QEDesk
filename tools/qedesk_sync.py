#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from importlib import resources
from pathlib import Path


GENERATED_BEGIN = "% QEDesk generated lean-map begin"
GENERATED_END = "% QEDesk generated lean-map end"

BLUEPRINT_TEMPLATE_CONFIG = {
    "author": "",
    "dochome": "",
    "documentclass": "article",
    "github": "",
    "home": "",
    "localtoc_level": 0,
    "paper": "a4paper",
    "showmore": True,
    "split_level": 0,
    "title": "QEDesk Blueprint",
    "toc_depth": 3,
}


@dataclass
class LeanDecl:
    kind: str
    name: str
    start_line: int
    end_line: int
    block: str
    statement: str
    checked: bool


@dataclass
class BlueprintNode:
    id: str
    kind: str
    title: str
    lean_decl: str | None
    status: str
    uses: list[str]
    body: str
    start_line: int
    end_line: int


@dataclass
class ProofGap:
    id: str
    node_id: str
    type: str
    status: str
    hint_level: int
    start_line: int
    end_line: int
    message: str | None


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def leanblueprint_template_root() -> Path | None:
    try:
        return Path(str(resources.files("leanblueprint"))) / "templates"
    except (ModuleNotFoundError, FileNotFoundError):
        return None


def render_leanblueprint_template(root: Path, template_name: str) -> str:
    from jinja2 import Environment, FileSystemLoader

    env = Environment(
        loader=FileSystemLoader(root),
        variable_start_string="{|",
        variable_end_string="|}",
        comment_start_string="{--",
        comment_end_string="--}",
    )
    return env.get_template(template_name).render(BLUEPRINT_TEMPLATE_CONFIG)


def render_upstream_blueprint_scaffold(src_dir: Path) -> bool:
    root = leanblueprint_template_root()
    if root is None or not root.exists():
        return False

    for template_name in [
        "web.tex",
        "print.tex",
        "plastex.cfg",
        "blueprint.sty",
        "extra_styles.css",
        "macros/common.tex",
        "macros/web.tex",
        "macros/print.tex",
    ]:
        write_text(src_dir / template_name, render_leanblueprint_template(root, template_name))

    return True


def extract_lean_decls(lean_text: str) -> list[LeanDecl]:
    lines = lean_text.splitlines()
    starts: list[tuple[int, str, str]] = []
    decl_re = re.compile(r"^(theorem|lemma|def)\s+([A-Za-z_][A-Za-z0-9_']*)\b")

    for index, line in enumerate(lines):
        match = decl_re.match(line)
        if match:
            starts.append((index, match.group(1), match.group(2)))

    decls: list[LeanDecl] = []
    for pos, (start, kind, name) in enumerate(starts):
        next_start = starts[pos + 1][0] if pos + 1 < len(starts) else len(lines)
        block_lines = lines[start:next_start]
        block = "\n".join(block_lines).rstrip()
        statement_lines: list[str] = []
        for line in block_lines:
            statement_lines.append(line)
            if ":= by" in line or ":=" in line:
                break
        statement = "\n".join(statement_lines)
        checked = "sorry" not in block
        decls.append(
            LeanDecl(
                kind=kind,
                name=name,
                start_line=start + 1,
                end_line=next_start,
                block=block,
                statement=statement,
                checked=checked,
            )
        )
    return decls


def tex_ident(name: str) -> str:
    match = re.fullmatch(r"([A-Za-z]+)([0-9]+)", name)
    if match:
        return f"{match.group(1)}_{match.group(2)}"
    return name.replace("_", r"\_")


def lean_statement_to_tex(statement: str) -> str:
    compact = " ".join(part.strip() for part in statement.splitlines())
    ascii_mem_image_preimage = re.search(
        r"\(\s*[^:]+:\s*Set\.image\s+([A-Za-z_][A-Za-z0-9_']*)\s+"
        r"\(Set\.preimage\s+\1\s+([A-Za-z_][A-Za-z0-9_']*)\)\s+"
        r"([A-Za-z_][A-Za-z0-9_']*)\s*\)\s*:\s*\2\s+\3",
        compact,
    )
    if ascii_mem_image_preimage:
        f_name, set_name, point_name = ascii_mem_image_preimage.groups()
        point_tex = tex_ident(point_name)
        f_tex = tex_ident(f_name)
        set_tex = tex_ident(set_name)
        return (
            rf"{point_tex} \in {f_tex}\bigl({f_tex}^{{-1}}({set_tex})\bigr)"
            rf" \Rightarrow {point_tex} \in {set_tex}"
        )

    mem_image_preimage = re.search(
        r"\(\s*[^:]+:\s*([A-Za-z_][A-Za-z0-9_']*)\s*∈\s*"
        r"Set\.image\s+([A-Za-z_][A-Za-z0-9_']*)\s+"
        r"\(Set\.preimage\s+\2\s+([A-Za-z_][A-Za-z0-9_']*)\)\s*\)\s*:\s*"
        r"\1\s*∈\s*\3",
        compact,
    )
    if mem_image_preimage:
        point_name, f_name, set_name = mem_image_preimage.groups()
        point_tex = tex_ident(point_name)
        f_tex = tex_ident(f_name)
        set_tex = tex_ident(set_name)
        return (
            rf"{point_tex} \in {f_tex}\bigl({f_tex}^{{-1}}({set_tex})\bigr)"
            rf" \Rightarrow {point_tex} \in {set_tex}"
        )

    image_preimage = re.search(
        r"Set\.image\s+([A-Za-z_][A-Za-z0-9_']*)\s+"
        r"\(Set\.preimage\s+\1\s+([A-Za-z_][A-Za-z0-9_']*)\)\s+"
        r"<=\s+([A-Za-z_][A-Za-z0-9_']*)",
        compact,
    )
    if image_preimage:
        f_name, subset_name, rhs_name = image_preimage.groups()
        if subset_name == rhs_name:
            f_tex = tex_ident(f_name)
            set_tex = tex_ident(subset_name)
            return rf"{f_tex}\bigl({f_tex}^{{-1}}({set_tex})\bigr) \subseteq {set_tex}"

    return r"\texttt{" + compact.replace("\\", r"\textbackslash{}").replace("_", r"\_") + "}"


def generated_latex_section(lean_text: str, decls: list[LeanDecl]) -> str:
    theorem_decls = [decl for decl in decls if decl.kind in {"theorem", "lemma"}]
    mapped = "\n\n".join(
        "\\paragraph{" + decl.name.replace("_", r"\_") + ".}\n"
        "\\[\n  "
        + lean_statement_to_tex(decl.statement)
        + "\n\\]\n"
        + ("Lean status: checked." if decl.checked else "Lean status: contains \\texttt{sorry}.")
        for decl in theorem_decls
    )
    if not mapped:
        mapped = "No theorem or lemma declarations were found."

    return (
        "\\subsection*{Generated Lean Map}\n\n"
        f"{GENERATED_BEGIN}\n"
        "This section is generated from \\texttt{src/Proof.lean} by \\texttt{qedesk sync}.\n\n"
        "\\paragraph{Mapped statements.}\n\n"
        f"{mapped}\n\n"
        "\\paragraph{Lean source.}\n\n"
        "\\begin{minted}{lean}\n"
        f"{lean_text.rstrip()}\n"
        "\\end{minted}\n"
        f"{GENERATED_END}\n"
    )


def update_main_tex(tex_text: str, generated_section: str) -> str:
    marked = re.compile(
        re.escape(GENERATED_BEGIN) + r".*?" + re.escape(GENERATED_END),
        re.DOTALL,
    )
    if marked.search(tex_text):
        replacement = (
            GENERATED_BEGIN
            + generated_section.split(GENERATED_BEGIN, 1)[1].rsplit(GENERATED_END, 1)[0]
            + GENERATED_END
        )
        return marked.sub(lambda _match: replacement, tex_text)

    lean_section = re.compile(
        r"\\subsection\*\{Lean Verification\}.*?(?=\\end\{document\})",
        re.DOTALL,
    )
    if lean_section.search(tex_text):
        return lean_section.sub(lambda _match: generated_section + "\n", tex_text)

    return tex_text.replace("\\end{document}", generated_section + "\n\\end{document}")


def parse_qedesk_attrs(line: str) -> dict[str, str] | None:
    match = re.match(r"^\s*%\s*QEDesk((?:\[[^\]]+\])+)\s*$", line)
    if not match:
        return None
    attrs: dict[str, str] = {}
    for key, value in re.findall(r"\[([A-Za-z0-9_-]+)=([^\]]*)\]", match.group(1)):
        attrs[key] = value.strip()
    return attrs


def split_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def clean_latex_body(lines: list[str]) -> str:
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)


def normalize_kind(kind: str | None) -> str:
    if not kind:
        return "lemma"
    kind = kind.strip().lower()
    if kind == "def":
        return "definition"
    allowed = {"definition", "theorem", "lemma", "proposition", "corollary", "example", "fact", "goal"}
    return kind if kind in allowed else "lemma"


def blueprint_env(kind: str) -> str:
    if kind in {"definition", "theorem", "lemma", "proposition", "corollary"}:
        return kind
    if kind == "goal":
        return "theorem"
    return "lemma"


def label_prefix(kind: str) -> str:
    return {
        "definition": "def",
        "theorem": "thm",
        "lemma": "lem",
        "proposition": "prop",
        "corollary": "cor",
        "example": "ex",
        "fact": "lem",
        "goal": "thm",
    }.get(kind, "lem")


def node_label(node: BlueprintNode) -> str:
    return f"{label_prefix(node.kind)}:{node.id}"


def tex_escape_text(text: str) -> str:
    return text.replace("_", r"\_")


def extract_blueprint_nodes(tex_text: str, decls: list[LeanDecl]) -> tuple[list[BlueprintNode], list[ProofGap]]:
    decl_by_name = {decl.name: decl for decl in decls}
    lines = tex_text.splitlines()
    nodes: list[BlueprintNode] = []
    gaps: list[ProofGap] = []
    current: BlueprintNode | None = None
    body_lines: list[str] = []

    def finish(end_line: int) -> None:
        nonlocal current, body_lines
        if current is None:
            return
        current.body = clean_latex_body(body_lines)
        current.end_line = max(current.start_line, end_line)
        nodes.append(current)
        current = None
        body_lines = []

    for index, line in enumerate(lines, start=1):
        if GENERATED_BEGIN in line:
            finish(index - 1)
            break

        attrs = parse_qedesk_attrs(line)
        if attrs and "node" in attrs:
            finish(index - 1)
            lean_decl = attrs.get("lean") or None
            decl = decl_by_name.get(lean_decl or "")
            status = attrs.get("status")
            if status is None:
                status = "checked" if decl and decl.checked else "candidate" if lean_decl else "open"
            current = BlueprintNode(
                id=attrs["node"],
                kind=normalize_kind(attrs.get("kind")),
                title=attrs.get("title", attrs["node"].replace("_", " ")),
                lean_decl=lean_decl,
                status=status,
                uses=split_list(attrs.get("uses")),
                body="",
                start_line=index,
                end_line=index,
            )
            body_lines = []
            continue

        if attrs and current is not None:
            current.uses.extend(split_list(attrs.get("uses")))
            if "gap" in attrs:
                gaps.append(
                    ProofGap(
                        id=attrs["gap"],
                        node_id=current.id,
                        type=attrs.get("type", "unspecified"),
                        status=attrs.get("status", "open"),
                        hint_level=int(attrs.get("hint", "1")),
                        start_line=index,
                        end_line=index,
                        message=attrs.get("message"),
                    )
                )
            continue

        if current is not None:
            if body_lines and re.match(r"^\s*\\(?:section|subsection|subsubsection|paragraph)\*?\{", line):
                finish(index - 1)
                continue
            body_lines.append(line)

    finish(len(lines))
    return nodes, gaps


def fallback_nodes_from_decls(decls: list[LeanDecl], known_lean_decls: set[str]) -> list[BlueprintNode]:
    nodes: list[BlueprintNode] = []
    for decl in decls:
        if decl.kind not in {"theorem", "lemma"} or decl.name in known_lean_decls:
            continue
        nodes.append(
            BlueprintNode(
                id=decl.name,
                kind=decl.kind,
                title=decl.name.replace("_", " "),
                lean_decl=decl.name,
                status="checked" if decl.checked else "candidate",
                uses=[],
                body="\\[\n  " + lean_statement_to_tex(decl.statement) + "\n\\]",
                start_line=decl.start_line,
                end_line=decl.end_line,
            )
        )
    return nodes


def all_blueprint_nodes(decls: list[LeanDecl], parsed_nodes: list[BlueprintNode]) -> list[BlueprintNode]:
    known_lean_decls = {node.lean_decl for node in parsed_nodes if node.lean_decl}
    return parsed_nodes + fallback_nodes_from_decls(decls, known_lean_decls)


def resolve_use_label(use: str, node_by_id: dict[str, BlueprintNode]) -> str:
    if ":" in use:
        return use
    node = node_by_id.get(use)
    return node_label(node) if node else use


def generated_blueprint(decls: list[LeanDecl], parsed_nodes: list[BlueprintNode]) -> str:
    nodes = all_blueprint_nodes(decls, parsed_nodes)
    parts = [
        "% Generated by qedesk sync. Do not edit this file as the source of truth.",
        "% Source of truth: src/main.tex and src/Proof.lean.",
        "",
        "\\section{Generated Blueprint}",
        "",
    ]

    node_by_id = {node.id: node for node in nodes}
    for node in nodes:
        env = blueprint_env(node.kind)
        title = tex_escape_text(node.title)
        uses = [resolve_use_label(use, node_by_id) for use in node.uses]
        parts.extend(
            [
                f"% QEDesk[node={node.id}][kind={node.kind}][status={node.status}]",
                f"\\begin{{{env}}}[{title}]",
                f"\\label{{{node_label(node)}}}",
            ]
        )
        if node.lean_decl:
            parts.append(f"\\lean{{{node.lean_decl}}}")
        parts.append("\\leanok" if node.status == "checked" else "\\notready")
        if uses:
            parts.append("\\uses{" + ", ".join(uses) + "}")
        parts.extend([node.body or "No informal statement recorded.", f"\\end{{{env}}}", ""])
    return "\n".join(parts).rstrip() + "\n"


def edges_from_nodes(nodes: list[BlueprintNode]) -> list[dict]:
    node_by_id = {node.id: node for node in nodes}
    label_to_id = {node_label(node): node.id for node in nodes}
    edges = []
    for node in nodes:
        for use in node.uses:
            target = use
            if use in node_by_id:
                target = use
            elif use in label_to_id:
                target = label_to_id[use]
            edges.append(
                {
                    "from": node.id,
                    "to": target,
                    "type": "uses",
                    "evidence": "qedesk-comment",
                }
            )
    return edges


def gaps_to_json(gaps: list[ProofGap]) -> list[dict]:
    return [
        {
            "id": gap.id,
            "node_id": gap.node_id,
            "type": gap.type,
            "status": gap.status,
            "hint_level": gap.hint_level,
            "span": {
                "start_line": gap.start_line,
                "end_line": gap.end_line,
            },
            **({"message": gap.message} if gap.message else {}),
        }
        for gap in gaps
    ]


def generated_mermaid(nodes: list[BlueprintNode], edges: list[dict]) -> str:
    parts = ["flowchart TD"]
    for node in nodes:
        title = node.title.replace('"', "'")
        parts.append(f'  {node.id}["{title}<br/>{node.kind} - {node.status}"]')
    for edge in edges:
        source = edge["from"]
        target = edge["to"]
        if source and target:
            parts.append(f"  {target} --> {source}")
    parts.extend(
        [
            "  classDef checked fill:#9CEC8B,stroke:#1C7C54,color:#111;",
            "  classDef candidate fill:#A3D6FF,stroke:#1D5F91,color:#111;",
            "  classDef open fill:#F8F8F8,stroke:#777,color:#111;",
            "  classDef blocked fill:#FFB6A8,stroke:#933,color:#111;",
            "  classDef draft fill:#FFE2A8,stroke:#946200,color:#111;",
        ]
    )
    for node in nodes:
        status = node.status if node.status in {"checked", "candidate", "open", "blocked", "draft"} else "open"
        parts.append(f"  class {node.id} {status};")
    return "\n".join(parts) + "\n"


def ensure_blueprint_scaffold(src_dir: Path) -> None:
    macros_dir = src_dir / "macros"
    macros_dir.mkdir(parents=True, exist_ok=True)

    if render_upstream_blueprint_scaffold(src_dir):
        return

    write_text(
        src_dir / "web.tex",
        r"""% Generated QEDesk Lean Blueprint web entrypoint.
\documentclass{article}

\usepackage{amssymb, amsthm, amsmath}
\usepackage{hyperref}
\usepackage[showmore, dep_graph]{blueprint}

\input{macros/common}
\input{macros/web}

\home{}
\github{}
\dochome{}

\title{QEDesk Blueprint}
\author{}

\begin{document}
\maketitle
\input{content}
\end{document}
""",
    )
    write_text(
        src_dir / "print.tex",
        r"""% Generated QEDesk Lean Blueprint print entrypoint.
\documentclass[a4paper]{article}

\usepackage{geometry}
\usepackage{expl3}
\usepackage{amssymb, amsthm, mathtools}
\usepackage[unicode,colorlinks=true,linkcolor=blue,urlcolor=magenta,citecolor=blue]{hyperref}

\input{macros/common}
\input{macros/print}

\title{QEDesk Blueprint}
\author{}

\begin{document}
\maketitle
\input{content}
\end{document}
""",
    )
    write_text(
        src_dir / "plastex.cfg",
        """[general]
renderer=HTML5
copy-theme-extras=yes
plugins=plastexdepgraph plastexshowmore leanblueprint

[document]
toc-depth=3
toc-non-files=True

[files]
directory=../web/
split-level=0

[html5]
localtoc-level=0
extra-css=extra_styles.css
mathjax-dollars=False
""",
    )
    write_text(
        src_dir / "blueprint.sty",
        r"""\DeclareOption*{}
\ProcessOptions

\newcommand{\graphcolor}[3]{}
""",
    )
    write_text(
        src_dir / "extra_styles.css",
        """/* QEDesk Blueprint custom styles. */
.content {
  max-width: 960px;
}
""",
    )
    write_text(
        macros_dir / "common.tex",
        r"""\newtheorem{theorem}{Theorem}
\newtheorem{proposition}[theorem]{Proposition}
\newtheorem{lemma}[theorem]{Lemma}
\newtheorem{corollary}[theorem]{Corollary}

\theoremstyle{definition}
\newtheorem{definition}[theorem]{Definition}
""",
    )
    write_text(macros_dir / "web.tex", "% QEDesk web-only macros.\n")
    write_text(
        macros_dir / "print.tex",
        r"""% QEDesk print-only macros.
\newcommand{\lean}[1]{}
\newcommand{\discussion}[1]{}
\newcommand{\leanok}{}
\newcommand{\mathlibok}{}
\newcommand{\notready}{}
\ExplSyntaxOn
\NewDocumentCommand{\uses}{m}
 {\clist_map_inline:nn{#1}{\vphantom{\ref{##1}}}\ignorespaces}
\NewDocumentCommand{\proves}{m}
 {\clist_map_inline:nn{#1}{\vphantom{\ref{##1}}}\ignorespaces}
\ExplSyntaxOff
""",
    )


def generated_dag(nodes: list[BlueprintNode], edges: list[dict], gaps: list[ProofGap]) -> dict:
    node_payloads = [
        {
            "id": node.id,
            "kind": node.kind,
            "label": node_label(node),
            "title": node.title,
            **({"lean_decl": node.lean_decl} if node.lean_decl else {}),
            "status": node.status,
            "span": {
                "start_line": node.start_line,
                "end_line": node.end_line,
            },
        }
        for node in nodes
    ]
    return {
        "document": "src/main.tex",
        "version": "0.2",
        "nodes": node_payloads,
        "edges": edges,
        "gaps": gaps_to_json(gaps),
    }


def validate_dag(dag: dict, schema_path: Path) -> None:
    if not schema_path.exists():
        return
    try:
        import jsonschema
    except ImportError:
        return
    schema = json.loads(read_text(schema_path))
    jsonschema.validate(instance=dag, schema=schema)


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync Lean declarations into QEDesk TeX, blueprint, and DAG artifacts.")
    parser.add_argument("--lean", default="src/Proof.lean")
    parser.add_argument("--tex", default="src/main.tex")
    parser.add_argument("--blueprint", default="blueprint/src/content.tex")
    parser.add_argument("--dag", default="build/qedesk-dag.json")
    parser.add_argument("--mermaid", default="build/qedesk-dag.mmd")
    parser.add_argument("--schema", default="schemas/qedesk-dag.schema.json")
    args = parser.parse_args()

    lean_path = Path(args.lean)
    tex_path = Path(args.tex)
    blueprint_path = Path(args.blueprint)
    dag_path = Path(args.dag)
    mermaid_path = Path(args.mermaid)
    schema_path = Path(args.schema)

    lean_text = read_text(lean_path)
    tex_text = read_text(tex_path)
    decls = extract_lean_decls(lean_text)
    parsed_nodes, gaps = extract_blueprint_nodes(tex_text, decls)
    nodes = all_blueprint_nodes(decls, parsed_nodes)
    edges = edges_from_nodes(nodes)

    new_tex = update_main_tex(tex_text, generated_latex_section(lean_text, decls))
    write_text(tex_path, new_tex)
    ensure_blueprint_scaffold(blueprint_path.parent)
    blueprint_text = generated_blueprint(decls, parsed_nodes)
    write_text(blueprint_path, blueprint_text)

    dag = generated_dag(nodes, edges, gaps)
    validate_dag(dag, schema_path)
    write_text(dag_path, json.dumps(dag, indent=2) + "\n")
    write_text(mermaid_path, generated_mermaid(nodes, edges))

    theorem_count = sum(1 for decl in decls if decl.kind in {"theorem", "lemma"})
    print(f"qedesk sync: mapped {theorem_count} theorem/lemma declaration(s)")
    print(f"qedesk sync: generated {len(nodes)} blueprint node(s) and {len(edges)} edge(s)")
    print(f"qedesk sync: updated {tex_path}")
    print(f"qedesk sync: updated {blueprint_path}")
    print(f"qedesk sync: wrote {dag_path}")
    print(f"qedesk sync: wrote {mermaid_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
