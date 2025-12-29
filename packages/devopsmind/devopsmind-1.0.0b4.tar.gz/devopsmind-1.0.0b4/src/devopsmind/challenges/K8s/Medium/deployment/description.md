Create deployment.yaml.

Requirements:
- apiVersion: apps/v1
- kind: Deployment
- metadata.name = web-deploy
- spec.replicas = 3
- spec.template.spec.containers:
    - name: web
    - image: nginx:1.21

Validator checks full structure including nested fields.
