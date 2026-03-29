Decision: SUBSCRIPTION_ID left as constant in scanner.py for Phase 1.
Will move to environment variable in Phase 2 when GitHub Secrets are configured.

What broke: git add failed — nested Cloud-Guardian-Lite folder inside repo root
What I tried: Remove-Item without -Force flag
Root cause: git init had been run inside the nested folder creating a .git directory, preventing deletion without -Force
Fix: Remove-Item -Recurse -Force Cloud-Guardian-Lite

What broke: ModuleNotFoundError — could not import report.py from scanner.py
What I tried: from report import, from src.report import, from . import report
Root cause: report.py did not exist in src/ — file was never created
Fix: New-Item src/report.py, then run as python -m src.scanner
