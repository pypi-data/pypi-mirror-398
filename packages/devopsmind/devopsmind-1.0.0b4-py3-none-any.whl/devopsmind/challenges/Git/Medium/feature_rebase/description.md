Repository has an existing `main` branch (or equivalent default branch).  

Tasks:
1. Create a branch named `feature/login`.
2. On that branch, add a file `login.txt` with exactly:
   login implemented
   (no extra whitespace).
3. Commit the change on feature/login.
4. Rebase `feature/login` onto the latest `main` (so the feature commit is on top of main). Do NOT create a merge commit.
5. Leave branch `feature/login` present locally.

What the validator checks:
- Branch feature/login exists.
- login.txt exists with exact content.
- The tip commit of feature/login must have a single parent (i.e. not a merge commit).
- The tip commit should contain the change that added login.txt.
