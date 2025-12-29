### 🧠 Kubernetes Master — Resource Management (Static)

Create a file named `deployment.yaml`.

Your Deployment must meet the following requirements:

- apiVersion: apps/v1
- kind: Deployment
- metadata.name: resource-deploy
- spec.replicas: 2

Container requirements:
- name: app
- image: nginx:alpine

Resource configuration:
- requests:
    cpu: "100m"
    memory: "128Mi"
- limits:
    cpu: "500m"
    memory: "256Mi"

⚠️ Rules:
- Resources must be defined under containers[].resources
- No kubectl or cluster required
- Validator performs static YAML validation only

🎯 Goal:
Demonstrate production-ready Kubernetes resource management.
