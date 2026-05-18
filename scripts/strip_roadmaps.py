"""Remove the Roadmap to v1.0.0 section from each project page.

The pattern is consistent across 0X-name.html files:

<section data-screen-label="NN Roadmap">
  ...heading + roadmap-list ol...
</section>

We strip the whole block (and the trailing blank line) since all
checkpoints are already marked done and the section adds clutter.
"""
from __future__ import annotations

import re
from pathlib import Path

PROJ_DIR = Path("C:/Users/Usuario/ai-portfolio/projects")

# Match the entire <section data-screen-label="XX Roadmap"> ... </section>
# (non-greedy, multiline, including the trailing blank line)
PATTERN = re.compile(
    r'<section(?:\s+data-screen-label="\d+ Roadmap")?>\s*'
    r'<div class="container">\s*'
    r'<div class="section-head">\s*'
    r'<div class="section-eyebrow">\d+ · Roadmap to v1\.0\.0</div>'
    r'.*?'
    r'</section>\s*\n',
    re.DOTALL,
)


def strip(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    new = PATTERN.sub("", text, count=1)
    if new == text:
        return False
    path.write_text(new, encoding="utf-8")
    return True


def main() -> None:
    n = 0
    for f in sorted(PROJ_DIR.glob("0*.html")):
        if strip(f):
            print(f"  stripped: {f.name}")
            n += 1
        else:
            print(f"  no-op:    {f.name}")
    print(f"\nTotal: {n} files updated")


if __name__ == "__main__":
    main()
