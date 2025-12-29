### 🔐 Challenge — Analyze Firewall Rules (Offline)

You are provided a firewall status output in `ufw_status.txt`.

Your task:
1. Write a script `analyze_firewall.sh`
2. The script must verify:
   - Port 80 is ALLOWED
   - All other inbound ports are DENIED
3. Print exactly:
   Firewall correctly allows HTTP only
