#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = PROJECT_ROOT / "blueprint" / "web"

NAV = """<nav class="qedesk-blueprint-switcher" aria-label="QEDesk Blueprint views">
  <a href="index.html">Blueprint</a>
  <a href="dep_graph_document.html">Dependency graph</a>
</nav>
"""

CSS = """<style>
.qedesk-blueprint-switcher {
  position: fixed;
  z-index: 20;
  right: 1rem;
  bottom: 1rem;
  display: flex;
  gap: .4rem;
  padding: .35rem;
  border: 1px solid #b8c2cc;
  border-radius: .35rem;
  background: rgba(255, 255, 255, .94);
  box-shadow: 0 8px 24px rgba(0, 0, 0, .12);
}
.qedesk-blueprint-switcher a {
  padding: .35rem .55rem;
  border-radius: .25rem;
  color: #1f2933;
  text-decoration: none;
  font-size: .9rem;
}
.qedesk-blueprint-switcher a:hover {
  background: #e8f1fb;
}
</style>
"""


def inject(path: Path) -> None:
    if not path.exists():
        return
    html = path.read_text(encoding="utf-8")
    if "qedesk-blueprint-switcher" in html:
        return
    if "</head>" in html:
        html = html.replace("</head>", CSS + "\n</head>", 1)
    if "<body>" in html:
        html = html.replace("<body>", "<body>\n" + NAV, 1)
    else:
        html = NAV + html
    path.write_text(html, encoding="utf-8", newline="\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Inject QEDesk view switcher into Lean Blueprint HTML output.")
    parser.add_argument("web_dir", nargs="?", default=str(WEB_DIR))
    args = parser.parse_args()
    web_dir = Path(args.web_dir)
    if not web_dir.is_absolute():
        web_dir = PROJECT_ROOT / web_dir
    inject(web_dir / "index.html")
    inject(web_dir / "dep_graph_document.html")
    print(f"QEDesk Blueprint switcher updated in {web_dir}")


if __name__ == "__main__":
    main()
