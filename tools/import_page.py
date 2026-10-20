"""Copy a page built in the StreamMUSE repo into this site.

The StreamMUSE build scripts (scripts/build_rap_demo_page.py,
scripts/build_model_upgrade_page.py) write ``<out>/site/index.html`` as a
fragment with its data inlined, next to ``audio/``. This script:

- wraps the fragment in a full HTML document and adds the site's top bar;
- removes run details that only make sense on the machine that recorded them
  (local paths, command lines) and refuses to write if any local path is left;
- copies ``audio/`` (only files that changed).

    python3 tools/import_page.py ../StreamMUSE-v1/output/rap_demo_page_2026-10/site versions
    python3 tools/import_page.py ../StreamMUSE-v1/output/model_upgrade_20261014/site model-upgrade
"""

from __future__ import annotations

import argparse
import filecmp
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = [("versions", "Versions"), ("model-upgrade", "Model upgrade")]
DROP_KEYS = {"argv", "streammuse_package", "wav", "session"}
LOCAL = re.compile(r"/Users/|/data/home|/home/|127\.0\.0\.1|localhost")
DATA = re.compile(r'(<script type="application/json" id="data">)(.*?)(</script>)', re.S)

NAV = """<nav class="site-nav" aria-label="StreamMUSE-Rap">
<a class="site-home" href="../">StreamMUSE-Rap</a>
{links}
</nav>
<style>
.site-nav {{ display: flex; flex-wrap: wrap; gap: 6px 18px; align-items: center; max-width: 1180px; margin: 0 auto;
  padding: 14px 20px; border-bottom: 1px solid var(--line); font: 500 0.88rem/1.2 var(--body); }}
.site-nav a {{ color: var(--muted); text-decoration: none; }}
.site-nav a:hover {{ color: var(--ink); }}
.site-nav a[aria-current="page"] {{ color: var(--accent); }}
.site-nav .site-home {{ font: 800 1.05rem/1 var(--display); font-stretch: 78%; color: var(--ink); margin-right: auto; }}
</style>
"""


def strip(value: object) -> object:
    if isinstance(value, dict):
        return {k: strip(v) for k, v in value.items() if k not in DROP_KEYS}
    if isinstance(value, list):
        return [strip(v) for v in value]
    return value


def sanitize(fragment: str) -> str:
    match = DATA.search(fragment)
    if not match:
        raise SystemExit("no inline data block found")
    data = strip(json.loads(match.group(2)))
    text = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
    fragment = fragment[: match.start(2)] + text + fragment[match.end(2):]
    leaks = sorted(set(LOCAL.findall(fragment)))
    if leaks:
        raise SystemExit(f"local details left in the page: {leaks}")
    return fragment


def wrap(fragment: str, slug: str) -> str:
    head, sep, body = fragment.partition("</style>")
    if not sep:
        raise SystemExit("expected the fragment to open with <title>, fonts and one <style> block")
    current = ' aria-current="page"'
    links = "\n".join(f'<a href="../{s}/"{current if s == slug else ""}>{label}</a>' for s, label in PAGES)
    return (
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"{head}</style>\n<style>body {{ margin: 0; }}</style>\n</head>\n<body>\n"
        f"{NAV.format(links=links)}{body.lstrip()}\n</body>\n</html>\n"
    )


def copy_audio(src: Path, dst: Path) -> tuple[int, int]:
    dst.mkdir(parents=True, exist_ok=True)
    copied = 0
    names = set()
    for f in sorted(src.iterdir()):
        names.add(f.name)
        target = dst / f.name
        if not target.exists() or not filecmp.cmp(f, target, shallow=False):
            shutil.copy2(f, target)
            copied += 1
    removed = 0
    for f in dst.iterdir():
        if f.name not in names:
            f.unlink()
            removed += 1
    return copied, removed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("site", type=Path, help="the built page's directory (index.html + audio/)")
    parser.add_argument("slug", choices=[s for s, _ in PAGES])
    args = parser.parse_args()
    out = ROOT / args.slug
    out.mkdir(exist_ok=True)
    page = wrap(sanitize((args.site / "index.html").read_text()), args.slug)
    (out / "index.html").write_text(page)
    copied, removed = copy_audio(args.site / "audio", out / "audio")
    print(f"{out / 'index.html'}: {len(page) // 1024} KB; audio {copied} copied, {removed} removed")


if __name__ == "__main__":
    main()
