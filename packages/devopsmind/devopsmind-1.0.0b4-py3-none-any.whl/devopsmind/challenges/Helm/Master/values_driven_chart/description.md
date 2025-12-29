### 🧠 Helm Master — Values-Driven Chart Design (Static)

You must enhance a Helm chart so that it is **fully configurable via values.yaml**.

Create or modify the following files:

### 1. mychart/values.yaml
```yaml
replicaCount: 3
image:
  repository: nginx
  tag: alpine
```
### 2. mychart/templates/deployment.yaml

* The Deployment must:

- Use replicaCount from values.yaml

- Use image from:
{{ .Values.image.repository }}:{{ .Values.image.tag }}

- Set metadata.name to:
{{ .Chart.Name }}-deploy

### ⚠️ Rules:

- No hardcoded replicas or image values

- Use Helm templating only

- Do NOT run Helm

### 🎯 Goal:

* Demonstrate Helm mastery through reusable chart design.
