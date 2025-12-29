### 🌐 Master Challenge — DNS vs Network Diagnosis (Offline)

You are provided with two log files:

- `ping.log` — shows ICMP connectivity results
- `dns.log` — shows DNS lookup output

Your task:

1. Analyze both files
2. Determine whether the problem is:
   - Network connectivity
   - OR DNS resolution

3. Write a script named `diagnose_network.sh` that prints **exactly**:

Network reachable but DNS resolution failing

⚠️ Rules:
- Do NOT perform real network requests
- Do NOT modify system configuration
- Only analyze the provided files

🎯 Goal:
Demonstrate correct reasoning between Layer 3 connectivity and DNS (Layer 7).
