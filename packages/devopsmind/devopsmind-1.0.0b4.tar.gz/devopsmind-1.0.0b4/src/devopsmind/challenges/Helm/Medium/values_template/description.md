Enhance your Helm chart by adding value substitution.

Requirements:

1. In mychart/values.yaml define:
     image: nginx:alpine

2. In templates/deployment.yaml template:
     - Container image must use templating:
         image: {{ .Values.image }}

3. Deployment metadata.name must be templated:
         name: {{ .Chart.Name }}-deploy

Validator performs static templating pattern checks (not actual Helm rendering).
