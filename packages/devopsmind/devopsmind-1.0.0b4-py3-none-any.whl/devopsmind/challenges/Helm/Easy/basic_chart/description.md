Task: manually create a minimal Helm chart structure.

Required structure:

mychart/
  Chart.yaml
  templates/
    deployment.yaml

Content requirements:

Chart.yaml must contain:
  apiVersion: v2
  name: mychart
  version: 0.1.0

deployment.yaml must contain a Deployment manifest with:
  kind: Deployment
  metadata:
    name: mychart-deploy

Validator checks only static file presence and minimal YAML fields.
