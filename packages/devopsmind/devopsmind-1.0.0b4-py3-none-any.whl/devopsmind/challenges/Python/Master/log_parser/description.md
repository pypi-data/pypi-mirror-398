### 🧠 Master Challenge — Log Parser & Summary

You are provided a log file named `app.log`.

Each line follows this format:
TIMESTAMP LEVEL MESSAGE

Example:
2025-12-10 10:00:00 INFO Service started

Your task:

1. Create a Python file named `log_parser.py`
2. Parse `app.log`
3. Count how many times each log LEVEL appears
4. Print the summary **exactly** in this format:

INFO: <count>
ERROR: <count>
WARN: <count>

⚠️ Rules:
- Do NOT modify `app.log`
- Do NOT hardcode values
- Use only Python standard library
- Output order must be INFO, ERROR, WARN

🎯 Goal:
Demonstrate robust parsing, aggregation, and deterministic output.
