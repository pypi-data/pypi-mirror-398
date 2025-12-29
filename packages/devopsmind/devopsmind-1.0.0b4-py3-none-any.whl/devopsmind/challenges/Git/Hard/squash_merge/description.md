This challenge simulates a production-style history hygiene task.

Preconditions:
- There is a branch named `feature/login` (it may contain one or multiple commits).
- There is a `main` branch.

Tasks:
1. On main, integrate the work from `feature/login` using a squash strategy so that main receives a SINGLE commit representing the feature.
2. The final commit message on main that represents the squashed feature must contain (case-sensitive substring):
   Add auth feature
3. Main must not contain merge commits introduced by this operation. In other words, there should be no commits on main with two or more parents.
4. After the operation, `login.txt` must exist in the root of the repository on main and contain exactly:
   login implemented

Notes / teaching points:
- Use `git checkout main` then `git merge --squash feature/login` and `git commit` (or an equivalent flow).
- This teaches clean history management for code-reviewable artifacts.
