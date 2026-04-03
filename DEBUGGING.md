
### Bug 1 — Nested git folder blocked commit
What broke: `git add .` failed with "unable to index file"
What I tried: `Remove-Item Cloud-Guardian-Lite` without flags
Root cause: `git init` had been run inside a nested `Cloud-Guardian-Lite/` 
folder inside the repo root, creating a `.git` directory that blocked deletion
Fix: `Remove-Item -Recurse -Force Cloud-Guardian-Lite`
Interview story: Diagnosed by running `ls` and spotting the duplicate folder 
name. Lesson: always check `ls` before running git commands in a new terminal.

---

### Bug 2 — ModuleNotFoundError for report.py
What broke: `ModuleNotFoundError: No module named 'report'`
What I tried: `from report import`, `from src.report import`, `from . import report`
Root cause: report.py did not exist in src/ — file was never created
Fix: `New-Item src/report.py`, run as `python -m src.scanner`
Interview story: Chased an import error for 10 minutes. Root cause was the 
file simply didn't exist — not a path issue, not a package issue. 
Always check the obvious before going deep.

---

### Lesson: Subscription ID in public git history
What happened: SUBSCRIPTION_ID hardcoded in scanner.py and committed 
to public repo before environment variables were set up
What I tried: N/A — caught before exploitation
Root cause: .gitignore was set up after the first commit, not before
Fix: Subscription ID is not a credential so no rotation needed. 
Will move to .env in Phase 2 when GitHub Secrets are configured.
Key rule: For real secrets — rotate first, scrub history second, 
force push third, notify team fourth. Bots scan GitHub in under 60 seconds.
Interview story: "Caught my subscription ID in public git history. Not a 
credential so no rotation needed, but taught me .gitignore must be set up 
before the first commit — not after."