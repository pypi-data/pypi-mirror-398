Create a Dockerfile implementing a multi-stage build.

Requirements:

Stage 1 (builder):
- Base: python:3.10-slim
- Copy requirements.txt → install dependencies

Stage 2:
- Base: python:3.10-slim
- Copy ONLY:
    - installed dependencies from stage 1
    - app.py
- Must run: python app.py
- Image must NOT include requirements.txt or cached build files.

Validator checks:
- Multi-stage syntax exists (two FROM statements)
- requirements installation appears only in the builder stage
- final stage CMD/ENTRYPOINT runs python app.py
