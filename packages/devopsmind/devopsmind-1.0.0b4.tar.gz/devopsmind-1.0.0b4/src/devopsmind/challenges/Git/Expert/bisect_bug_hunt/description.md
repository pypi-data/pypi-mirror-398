### 🧠 Git Expert — Bug Hunt with Git Bisect

You are given a Git repository where:
- A bug exists in the current HEAD
- Earlier commits worked correctly

---

## ⚠️ Setup (Required)

Before starting this challenge, you must initialize the Git repository.

From inside the challenge workspace, run:

```bash
python seed.py
```
- This will:

- Initialize a Git repository

- Create a commit history

- Introduce a bug in a later commit

- Only after running this step should you proceed.

### 🎯 Your Task

- Use git bisect to identify the commit that introduced the bug.

- Create a file named bug_commit.txt.

- The file must contain:

- The full commit hash that introduced the bug

- Nothing else (no extra text or whitespace)

## ⚠️ Rules

- Use git bisect or equivalent reasoning

- Do NOT modify commit history

- Do NOT fix the bug

- Only identify the commit

### 🏁 Goal
 
- Demonstrate expert-level Git debugging and regression analysis skills.
