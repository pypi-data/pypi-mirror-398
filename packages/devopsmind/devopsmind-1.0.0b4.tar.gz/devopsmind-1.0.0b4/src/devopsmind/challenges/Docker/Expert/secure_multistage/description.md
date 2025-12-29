### 🧠 Docker Expert — Secure Multi-Stage Build (Static)

Your task is to design a **secure multi-stage Dockerfile**.

Create a file named `Dockerfile` with these requirements:

### Stage 1 (builder)
- Base: python:3.10-slim
- Install dependencies using requirements.txt

### Stage 2 (runtime)
- Base: python:3.10-slim
- Copy ONLY:
  - installed dependencies from builder
  - app.py
- Must create and use a **non-root user**
- Must run:
  python app.py

⚠️ Rules:
- Must use multi-stage build (multiple FROM)
- Must NOT copy requirements.txt into final image
- Must NOT run as root
- No Docker build/run required

🎯 Goal:
Demonstrate expert-level Docker security and image design.
