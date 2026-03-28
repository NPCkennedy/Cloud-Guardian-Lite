Decision: SUBSCRIPTION_ID left as constant in scanner.py for Phase 1.
Will move to environment variable in Phase 2 when GitHub Secrets are configured.

What broke: git add failed — nested Cloud-Guardian-Lite folder inside repo root
What I tried: Remove-Item without -Force flag
Root cause: git init had been run inside the nested folder creating a .git directory, 
            preventing deletion without -Force
Fix: Remove-Item -Recurse -Force Cloud-Guardian-Lite
Interview story: Nested git repo caused index failure — diagnosed by checking 
                 ls output and spotting duplicate folder name