# Instructions for Codex

## Branch and publishing workflow

- Make project changes on the `work` branch.
- At the end of each completed implementation or documentation task, inspect `git status`, `git diff`, and `git diff --cached`. Stage only files related to that task, create a concise descriptive commit, and push it to `origin work`.
- Report the commit SHA and confirm the push result. Do not wait for the user to ask for commit/push again.
- Never push directly to `main`. Do not merge `work` into `main`, open a merge, or delete branches unless the user explicitly asks.
- Before editing, verify the current branch. If it is not `work`, preserve any existing changes and move to `work` safely; if that cannot be done without risking work, stop and explain the situation instead of pushing to another branch.
- If the task is analysis, explanation, or planning only and changes no project files, do not create an empty commit.
- If relevant validation fails, do not claim the task is complete. Fix the failure if within scope; otherwise report it and do not push an unverified change as complete.

## Project and teaching workflow

- Read the current source and `instruction.md` before changing code. Do not assume earlier chat snippets match the current repository.
- Work in small, scoped steps. Before each step, explain what will change and why. At the end, summarize files changed, validation performed, and the next planned step.
- Explain in Vietnamese at a beginner-friendly level. Add Vietnamese notes before each class, method, and function, and explain the control flow in `main.py`.
- Preserve the agreed game rules, especially straight and diagonal jumps, legal wall placement, and BFS validation that neither player loses all paths to their goal.
- Separate what was verified in the Codex/Linux environment from what still needs a manual Windows GUI check.
- Do not add bots or broad refactors while a current two-player step remains unresolved.
