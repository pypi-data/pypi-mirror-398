### 🧠 Git Master — Clean History with Rebase

You are working in an existing Git repository.

Your task:

1. Run `python seed/seed.py` to setup environment
2. Ensure branch `feature/refactor` exists.
3. The branch currently contains **multiple commits**.
4. Rewrite the history so that:
   - `feature/refactor` ends up with **exactly ONE commit**
   - The commit message must be:
     Refactor core logic
5. The commit must:
   - NOT be a merge commit
   - Have exactly **one parent**
6. Branch must remain named `feature/refactor`.

⚠️ Rules:
- Use interactive rebase or equivalent
- Do NOT merge
- Do NOT delete the branch
- Do NOT touch `main`

🎯 Goal:
Demonstrate professional Git history hygiene.
