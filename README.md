# ValveTrials.com

A cardiology-facing reference of major trans catheter valve-disease trials (aortic, mitral, tricuspid),
generated as a static website from a single data file.

## How the pieces fit

| File | Role |
|------|------|
| **`trials.json`** | **The single source of truth — all trials live here.** This is the only file you edit to change content. |
| `model.py` | The `Trial` data schema + the master list of categories and (in `valve_trials.py`) their colors. |
| `data.py` | Loads `trials.json` into trial objects. |
| `valve_trials.py` | The generator. Run it to (re)build the HTML pages. |
| `trials_data.py` | Legacy Python data (no longer read; kept only as a backup). |
| `.github/workflows/deploy.yml` | Rebuilds and publishes the site to GitHub Pages on every push. |

## Editing trials — three ways

### 1. The Editor page (no code)
Open **`editor.html`** (the **✎ Editor** link in the site header). You can:
- pick any existing trial to **edit**,
- create a **new** trial,
- **delete** a trial.

When you're done, click **⬇ Export trials.json**. Your browser downloads an updated
`trials.json`. Replace the `trials.json` in the repository with that file and commit it
(drag-and-drop works in GitHub's web UI). The Action rebuilds the live site automatically.

### 2. Edit `trials.json` directly on GitHub
Open `trials.json` in GitHub, click the pencil ✏️, edit, and commit. Same auto-rebuild.

### 3. Locally
```bash
python valve_trials.py            # builds index/aortic/mitral/tricuspid/editor into ./
python valve_trials.py site       # builds into ./site (what CI does)
```
No dependencies — standard-library Python 3 only.

## One-time GitHub setup

1. Create a repo and add these files (keep the folder layout, including `.github/workflows/`).
2. In **Settings → Pages**, set **Source = GitHub Actions**.
3. Push to `main`. The workflow builds and publishes; the live URL appears in the
   **Actions** run and under **Settings → Pages**.

That's it — after setup, editing `trials.json` (via the Editor or directly) and committing
is all it takes for the site to update.

## Notes
- Negative-result trials are excluded from the list views but remain in `trials.json`
  (toggle via `EXCLUDE_SIGNALS` in `valve_trials.py`).
- Paper links use the verified DOI/PubMed record when present; otherwise a
  "Find on PubMed" search link is generated (never a fabricated identifier).
- This is a reference aid, not clinical advice.
