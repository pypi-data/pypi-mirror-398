### 🧠 Linux Master — Log Metrics Pipeline (Offline)

You are provided a file named `access.log`.

Each line format:
IP METHOD STATUS

Example:
10.0.0.1 GET 200

Your task:

1. Create a script named `metrics.sh`
2. Read `access.log`
3. Count how many times each STATUS code appears
4. Print output exactly in this format (sorted numerically):

200: <count>
404: <count>
500: <count>

⚠️ Rules:
- Use standard Linux tools only (grep, awk, sort, uniq)
- Do NOT modify `access.log`
- Do NOT hardcode counts
- Output order and format must match exactly

🎯 Goal:
Demonstrate mastery of Linux text pipelines and reporting.
