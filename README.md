# StreamMUSE-Rap webpage

The static site for StreamMUSE-Rap's listening pages.

| Path | Content |
|---|---|
| `index.html` | Home page: what the system does, how it works, and the version timeline |
| `versions/` | Versions v0.0 to v1.1 on the same 15 prompts, in real time and fake real time |
| `model-upgrade/` | Lyric models, TTS models and live sessions behind v1.1 |

Each page is a single HTML file with its data inlined, plus its `audio/` folder. Nothing needs to be built,
so the repository root can be served as is (GitHub Pages: Settings → Pages → Deploy from branch `main`, folder `/`).

## Updating a page

The pages are built in the StreamMUSE repository; `tools/import_page.py` brings a built page in. It wraps it with
the site's top bar, drops run details that only make sense on the recording machine (local paths and command
lines), refuses to write if any local path is left, and syncs `audio/`.

```bash
# in StreamMUSE
uv run python scripts/build_rap_demo_page.py --out output/rap_demo_page_2026-10 --notes demo_page/notes.json
uv run python scripts/build_model_upgrade_page.py --notes demo_page/model_upgrade_notes.json

# here
python3 tools/import_page.py ../StreamMUSE-v1/output/rap_demo_page_2026-10/site versions
python3 tools/import_page.py ../StreamMUSE-v1/output/model_upgrade_20261014/site model-upgrade
```

Preview locally with `python3 -m http.server` and open http://localhost:8000.
