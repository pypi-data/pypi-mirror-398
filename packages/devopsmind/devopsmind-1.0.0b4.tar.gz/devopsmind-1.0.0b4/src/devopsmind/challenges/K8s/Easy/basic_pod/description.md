Create a file named pod.yaml.

Requirements:
- apiVersion: v1
- kind: Pod
- metadata.name: hello-pod
- spec.containers: one container
    - name: web
    - image: nginx

Validator performs static YAML validation — no connection to a Kubernetes cluster.
