### 🧠 Helm Expert — Conditional Resource Rendering (Static)

You must implement **conditional templating** in a Helm chart.

Create or modify the following:

### 1. mychart/values.yaml
```yaml
config:
  enabled: true
  message: "Hello Helm"
```

### 2. mychart/templates/configmap.yaml

* The ConfigMap must:

- Be rendered ONLY if:
{{ .Values.config.enabled }}

- Use:
{{ .Values.config.message }}

- Be named:
{{ .Chart.Name }}-config

### ⚠️ Rules:

- Use Helm if conditionals

- Do NOT hardcode values

- Do NOT run Helm

### 🎯 Goal:

* Demonstrate expert-level Helm conditional logic.
