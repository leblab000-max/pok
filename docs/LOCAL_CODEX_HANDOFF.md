# Windows local setup handoff

This task prepares the existing research project on the owner's Windows computer.
The declared v0.6 cloud confirmation and stress studies completed. Read the latest
RESEARCH_STATUS.md and reports/v06/SUMMARY.md. This handoff still authorizes setup
and verification only; start source edits after a new explicit owner task.

## Task for local Codex

1. Inspect the actual OS, shell, Python, Git and working directory. Use PowerShell
   on native Windows. Do not assume that software is already installed.
2. Use an existing clean checkout of leblab000-max/pok if available; otherwise clone
   https://github.com/leblab000-max/pok.git into a new empty user-owned project folder.
   Preserve existing files. If a checkout has local changes, report them and use an
   isolated worktree rather than resetting, cleaning or overwriting anything.
3. Use branch dev/poker-simulator-v03. Never edit or push main. Read README.md,
   NEXT_STEPS.md, docs/V06_CONTINUATIONS.md and reports/v06/selection.json.
4. Python 3.12 and Git are the only requirements. Missing free software may be
   installed using the normal Windows installer/package manager. Do not disable
   security controls, purchase services or configure paid APIs. Account sign-in is
   handled by the owner in the local client; never ask for passwords or tokens in chat.
5. Verify the checkout and run:

   ```powershell
   py -3.12 -m unittest discover -s tests -v
   py -3.12 scripts/stress_continuation.py
   py -3.12 scripts/play_v06.py
   ```

6. Report actual versions, current branch, test results and the generated local
   report path. Do not claim that commands ran unless their outputs were inspected.
7. For this setup phase, do not modify source code, commit, push, change selection
   parameters or delete databases/results. Keep generated reports under runs/local;
   SQLite files are ignored by Git. Wait for the cloud experiment handoff before
   starting additional development against the same branch.

The frozen selection is a source-checked research candidate, not a guaranteed
profitable player. Never connect to bot-prohibited poker rooms. Local desktop/CLI
Codex is a separate execution session; this file transfers project context, not
remote-control permission to an unrelated cloud chat.

Official Windows app and local terminal guidance:
https://learn.chatgpt.com/docs/windows/windows-app
https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan
