#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSHEETS_DIR = PROJECT_ROOT / "worksheets"

UNICODE_PREAMBLE = r"""\usepackage[utf8]{inputenc}
\DeclareUnicodeCharacter{00B7}{\ensuremath{\cdot}}
\DeclareUnicodeCharacter{03B1}{\ensuremath{\alpha}}
\DeclareUnicodeCharacter{03B2}{\ensuremath{\beta}}
\DeclareUnicodeCharacter{03B3}{\ensuremath{\gamma}}
\DeclareUnicodeCharacter{03B4}{\ensuremath{\delta}}
\DeclareUnicodeCharacter{03B5}{\ensuremath{\varepsilon}}
\DeclareUnicodeCharacter{03B6}{\ensuremath{\zeta}}
\DeclareUnicodeCharacter{03B7}{\ensuremath{\eta}}
\DeclareUnicodeCharacter{03B8}{\ensuremath{\theta}}
\DeclareUnicodeCharacter{03BB}{\ensuremath{\lambda}}
\DeclareUnicodeCharacter{03BC}{\ensuremath{\mu}}
\DeclareUnicodeCharacter{03C0}{\ensuremath{\pi}}
\DeclareUnicodeCharacter{03C1}{\ensuremath{\rho}}
\DeclareUnicodeCharacter{03C3}{\ensuremath{\sigma}}
\DeclareUnicodeCharacter{03C4}{\ensuremath{\tau}}
\DeclareUnicodeCharacter{03C6}{\ensuremath{\varphi}}
\DeclareUnicodeCharacter{03C8}{\ensuremath{\psi}}
\DeclareUnicodeCharacter{03C9}{\ensuremath{\omega}}
\DeclareUnicodeCharacter{0393}{\ensuremath{\Gamma}}
\DeclareUnicodeCharacter{0394}{\ensuremath{\Delta}}
\DeclareUnicodeCharacter{0398}{\ensuremath{\Theta}}
\DeclareUnicodeCharacter{03A0}{\ensuremath{\Pi}}
\DeclareUnicodeCharacter{03A3}{\ensuremath{\Sigma}}
\DeclareUnicodeCharacter{03A6}{\ensuremath{\Phi}}
\DeclareUnicodeCharacter{03A8}{\ensuremath{\Psi}}
\DeclareUnicodeCharacter{03A9}{\ensuremath{\Omega}}
\DeclareUnicodeCharacter{2115}{\ensuremath{\mathbb{N}}}
\DeclareUnicodeCharacter{2124}{\ensuremath{\mathbb{Z}}}
\DeclareUnicodeCharacter{211A}{\ensuremath{\mathbb{Q}}}
\DeclareUnicodeCharacter{211D}{\ensuremath{\mathbb{R}}}
\DeclareUnicodeCharacter{2200}{\ensuremath{\forall}}
\DeclareUnicodeCharacter{2203}{\ensuremath{\exists}}
\DeclareUnicodeCharacter{2205}{\ensuremath{\emptyset}}
\DeclareUnicodeCharacter{2208}{\ensuremath{\in}}
\DeclareUnicodeCharacter{2209}{\ensuremath{\notin}}
\DeclareUnicodeCharacter{2212}{\ensuremath{-}}
\DeclareUnicodeCharacter{2218}{\ensuremath{\circ}}
\DeclareUnicodeCharacter{2227}{\ensuremath{\land}}
\DeclareUnicodeCharacter{2228}{\ensuremath{\lor}}
\DeclareUnicodeCharacter{2260}{\ensuremath{\ne}}
\DeclareUnicodeCharacter{2261}{\ensuremath{\equiv}}
\DeclareUnicodeCharacter{2264}{\ensuremath{\le}}
\DeclareUnicodeCharacter{2265}{\ensuremath{\ge}}
\DeclareUnicodeCharacter{2282}{\ensuremath{\subset}}
\DeclareUnicodeCharacter{2286}{\ensuremath{\subseteq}}
\DeclareUnicodeCharacter{2190}{\ensuremath{\leftarrow}}
\DeclareUnicodeCharacter{2192}{\ensuremath{\to}}
\DeclareUnicodeCharacter{2194}{\ensuremath{\leftrightarrow}}
\DeclareUnicodeCharacter{21D2}{\ensuremath{\Rightarrow}}
\DeclareUnicodeCharacter{21D4}{\ensuremath{\Leftrightarrow}}
\DeclareUnicodeCharacter{27E8}{\ensuremath{\langle}}
\DeclareUnicodeCharacter{27E9}{\ensuremath{\rangle}}"""


def safe_slug(slug: str) -> Path:
    cleaned = slug.strip().strip("/\\")
    if not cleaned:
        raise SystemExit("Worksheet slug cannot be empty.")
    if cleaned.startswith(".") or ".." in Path(cleaned).parts:
        raise SystemExit("Worksheet slug cannot contain parent-directory segments.")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]*", cleaned):
        raise SystemExit("Use only letters, numbers, dots, underscores, hyphens, and slashes in worksheet slugs.")
    return Path(cleaned)


def worksheet_dir(slug: str) -> Path:
    path = WORKSHEETS_DIR / safe_slug(slug)
    resolved = path.resolve()
    root = WORKSHEETS_DIR.resolve()
    if root != resolved and root not in resolved.parents:
        raise SystemExit("Worksheet path escaped the worksheets directory.")
    return path


def title_from_slug(slug: str) -> str:
    leaf = Path(slug).name
    return leaf.replace("-", " ").replace("_", " ").title()


def lean_template(title: str) -> str:
    return f"""import Mathlib.Data.Set.Basic

/-!
{title}

Keep this worksheet local: stabilize one statement at a time, then let Lean
verify it.
-/

section Worksheet

-- Replace this starter theorem with the worksheet's first Lean target.
theorem starter_example (P : Prop) (h : P) : P := by
  exact h

end Worksheet
"""


def tex_template(title: str) -> str:
    return rf"""\documentclass[11pt]{{article}}

\usepackage[a4paper,margin=1in]{{geometry}}
{UNICODE_PREAMBLE}
\usepackage{{amsmath,amssymb,amsthm}}
\usepackage{{mathtools}}
\usepackage[outputdir=build]{{minted}}
\usepackage{{hyperref}}

\title{{{title}}}
\author{{}}
\date{{\today}}

\newtheorem{{theorem}}{{Theorem}}

\begin{{document}}
\maketitle

\section{{Problem}}

Write the problem statement here.

\section{{Proof Blueprint}}

% QEDesk[node=starter_definition][kind=definition][title=Starter definition][status=open]
Record the first useful definition or assumption here.

% QEDesk[node=starter_example][kind=theorem][title=Starter example][lean=starter_example][status=checked]
% QEDesk[uses=starter_definition]
If $P$ is true, then $P$ is true.

\section{{Proof Idea}}

Write the student's natural-language proof attempt here. QEDesk should audit
local gaps before asking Lean or an AI model to repair anything.

\subsection*{{Generated Lean Map}}

% QEDesk generated lean-map begin
This section is generated from \texttt{{Proof.lean}} by \texttt{{qedesk sync}}.
% QEDesk generated lean-map end

\end{{document}}
"""


def cmd_new(args: argparse.Namespace) -> int:
    target = worksheet_dir(args.slug)
    title = args.title or title_from_slug(args.slug)
    target.mkdir(parents=True, exist_ok=True)

    files = {
        target / "Proof.lean": lean_template(title),
        target / "main.tex": tex_template(title),
    }
    for path, content in files.items():
        if path.exists() and not args.force:
            raise SystemExit(f"{path.relative_to(PROJECT_ROOT)} already exists. Use --force to overwrite.")
        path.write_text(content, encoding="utf-8", newline="\n")

    print(f"Created worksheet: {target.relative_to(PROJECT_ROOT)}")
    print(f"  Lean: {target.relative_to(PROJECT_ROOT) / 'Proof.lean'}")
    print(f"  TeX:  {target.relative_to(PROJECT_ROOT) / 'main.tex'}")
    return 0


def cmd_list(_args: argparse.Namespace) -> int:
    WORKSHEETS_DIR.mkdir(exist_ok=True)
    entries = []
    for path in sorted(WORKSHEETS_DIR.rglob("main.tex")):
        root = path.parent
        if (root / "Proof.lean").exists():
            entries.append(root.relative_to(PROJECT_ROOT).as_posix())
    if not entries:
        print("No worksheets yet. Create one with:")
        print("  ./bin/qedesk new number-theory/fermat-little")
        return 0
    for entry in entries:
        print(entry)
    return 0


def cmd_info(args: argparse.Namespace) -> int:
    target = worksheet_dir(args.slug)
    print(f"Worksheet: {target.relative_to(PROJECT_ROOT)}")
    print(f"  Lean:      {target.relative_to(PROJECT_ROOT) / 'Proof.lean'}")
    print(f"  TeX:       {target.relative_to(PROJECT_ROOT) / 'main.tex'}")
    print(f"  PDF:       {target.relative_to(PROJECT_ROOT) / 'build' / 'main.pdf'}")
    print(f"  Blueprint: {target.relative_to(PROJECT_ROOT) / 'blueprint' / 'web' / 'index.html'}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage QEDesk worksheet directories.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    new = subparsers.add_parser("new")
    new.add_argument("slug")
    new.add_argument("--title")
    new.add_argument("--force", action="store_true")
    new.set_defaults(func=cmd_new)

    list_parser = subparsers.add_parser("list")
    list_parser.set_defaults(func=cmd_list)

    info = subparsers.add_parser("info")
    info.add_argument("slug")
    info.set_defaults(func=cmd_info)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    return int(args.func(args) or 0)


if __name__ == "__main__":
    raise SystemExit(main())
