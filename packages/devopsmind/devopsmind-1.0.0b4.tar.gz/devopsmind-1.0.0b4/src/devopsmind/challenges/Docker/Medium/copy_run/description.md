Create a Dockerfile that:

1. Uses base image: python:3.10-alpine  
2. Copies a file named app.py from the current directory into /app/app.py  
3. Sets WORKDIR to /app  
4. Runs app.py using CMD ["python3", "app.py"]

Validator only checks Dockerfile structure — no actual build required.
