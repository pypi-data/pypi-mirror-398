### 🧠 Linux Expert — Safe Cleanup Script (Offline)

You are provided a directory named `workspace/` containing files.

Your task:

1. Create a script named `cleanup.sh`
2. The script must accept:
   --dry-run
3. When run with --dry-run:
   - It must NOT delete anything
   - It must PRINT which files *would* be deleted
4. Only files ending with `.tmp` are eligible

5. 📁 Files provided by DevOpsMind:
workspace/
├── cache.tmp
├── session.tmp
└── notes.txt

⚠️ Rules:
- Do NOT delete files (validator checks dry-run only)
- Do NOT use rm without dry-run protection
- Output must list filenames only (one per line)

🎯 Goal:
Demonstrate expert-level Linux safety and defensive scripting.
