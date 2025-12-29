Create two files:
1. deployment.yaml  
2. service.yaml  

Requirements:

### Deployment (deployment.yaml)
- apiVersion: apps/v1
- kind: Deployment
- metadata.name: web-deploy
- spec.template.metadata.labels:
    app: web
- spec.replicas: 2
- spec.template.spec.containers:
    - name: web
    - image: nginx:alpine

### Service (service.yaml)
- apiVersion: v1
- kind: Service
- metadata.name: web-service
- spec.type: ClusterIP
- spec.selector:
    app: web
- spec.ports:
    - port: 80
      targetPort: 80

Validator checks cross-file consistency:
- Service selector must match Deployment labels
- Correct ports and types
