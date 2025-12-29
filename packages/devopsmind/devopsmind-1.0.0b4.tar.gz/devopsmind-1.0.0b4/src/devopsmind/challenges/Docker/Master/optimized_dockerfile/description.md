### 🧠 Docker Master — Optimized Dockerfile (Static)

Your task is to write a **production-quality Dockerfile**.

Create a file named `Dockerfile` with the following requirements:

1. Base image must be:
   python:3.10-slim
2. Must set a working directory:
   /app
3. Must copy ONLY:
   - app.py
4. Must define a single CMD that runs:
   python app.py
5. Must NOT:
   - use latest tag
   - install unnecessary packages
   - copy entire context (no COPY . .)

⚠️ Rules:
- No Docker build or run required
- Validator performs static analysis only

🎯 Goal:
Demonstrate Docker image optimization and best practices.

