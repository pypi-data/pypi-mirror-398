### 🧠 Expert Challenge — Dependency Resolver

You are given a dependency definition file named `deps.txt`.

Each line represents:
task -> dependency

Meaning:
- task depends on dependency

Your task:

1. Create a Python file named `resolve_deps.py`
2. Read `deps.txt`
3. Compute a valid execution order that satisfies all dependencies
4. Print the tasks **one per line** in execution order

⚠️ Rules:
- Use only Python standard library
- Do NOT hardcode the order
- The order must be valid (dependency always comes first)
- Cycles do NOT exist in the input

🎯 Goal:
Demonstrate expert-level algorithmic reasoning and graph traversal.
