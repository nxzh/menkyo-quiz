#!/usr/bin/env python3
"""Are the files this repository shares with the app repository still the same?

    python3 tools/check_mirrors.py [--app ../menkyo]

`docs/glossary-v7.md`, `docs/search-aliases-v1.md` and
`tools/build_search_terms.py` are copies, byte for byte, of files authored in
the app repository. They are copied rather than imported because this
repository has to build its packs on a CI runner that has only this checkout.
A copy that has drifted is the one way the published vocabulary can stop
agreeing with the glossary the translations follow, so it is checked rather
than trusted.

Skipped, loudly, when the app repository is not beside this one — on a CI
runner it is not, and the check that matters there is
`build_search_terms.py --validate`, which reads the glossary in this
repository.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# this repository -> the app repository
MIRRORS = {
    "docs/glossary-v7.md": "assets/术语表_v7_JA-ZH-EN-VI-PT.md",
    "docs/search-aliases-v1.md": "assets/搜索别名_v1.md",
    "tools/build_search_terms.py": "assets/tools/build_search_terms.py",
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--app", default=str(ROOT.parent / "menkyo"))
    args = ap.parse_args()

    app = Path(args.app).expanduser().resolve()
    if not app.exists():
        print(f"check_mirrors: {app} is not here — skipped")
        return 0

    problems = []
    for here, there in MIRRORS.items():
        mine, theirs = ROOT / here, app / there
        if not theirs.exists():
            problems.append(f"{there} is missing from {app}")
        elif not mine.exists():
            problems.append(f"{here} is missing from this repository")
        elif mine.read_bytes() != theirs.read_bytes():
            problems.append(f"{here} and {there} have drifted apart")

    for problem in problems:
        print(f"check_mirrors: {problem}", file=sys.stderr)
    if problems:
        return 1
    print(f"{len(MIRRORS)} mirrored files are identical to {app.name}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
