### 🧩 Challenge — Test Open Ports

Write a script named **check_ports.sh** that checks whether the following ports are open on localhost:
- 22 (SSH)
- 80 (HTTP)
- 443 (HTTPS)

Each open port should print:

✅ Port <port> is open

and closed ports should print:


❌ Port <port> is closed


**Requirements**
- Use `nc -zv` or `bash` socket syntax (`/dev/tcp/`).
- The script must be executable and run without errors.

**Goal**
> Demonstrate ability to test basic connectivity in Linux
