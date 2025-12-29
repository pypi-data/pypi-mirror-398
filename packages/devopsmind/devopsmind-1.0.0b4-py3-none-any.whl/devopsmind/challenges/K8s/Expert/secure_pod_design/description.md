### 🧠 Kubernetes Expert — Secure Pod Design (Static)

Create a file named `pod.yaml`.

Your Pod must meet the following requirements:

- apiVersion: v1
- kind: Pod
- metadata.name: secure-pod
- Uses image: nginx:alpine

Security requirements:
- runAsNonRoot: true
- runAsUser: 1000
- allowPrivilegeEscalation: false
- readOnlyRootFilesystem: true

⚠️ Rules:
- Use securityContext (pod or container level)
- No kubectl or cluster required
- Validator checks static YAML only

🎯 Goal:
Demonstrate expert-level Kubernetes security hardening.
