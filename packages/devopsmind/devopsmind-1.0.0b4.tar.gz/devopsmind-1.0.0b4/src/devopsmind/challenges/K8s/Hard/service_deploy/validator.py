#!/usr/bin/env python3
import os, yaml

def load_yaml(path):
    if not os.path.exists(path):
        return None, f"{path} missing."
    try:
        with open(path) as f:
            return yaml.safe_load(f), None
    except Exception as e:
        return None, f"Invalid YAML in {path}: {e}"

def validate():
    deploy, err = load_yaml("deployment.yaml")
    if err: return False, err

    svc, err = load_yaml("service.yaml")
    if err: return False, err

    # Validate Deployment
    if deploy.get("kind") != "Deployment":
        return False, "deployment.yaml must define a Deployment."

    dmeta = deploy.get("metadata", {})
    if dmeta.get("name") != "web-deploy":
        return False, "Deployment name must be web-deploy."

    replicas = deploy.get("spec", {}).get("replicas")
    if replicas != 2:
        return False, "Deployment replicas must be 2."

    labels = deploy.get("spec", {}).get("template", {}).get("metadata", {}).get("labels", {})
    if labels.get("app") != "web":
        return False, "Deployment must set label app=web."

    containers = deploy.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [])
    if not containers:
        return False, "Deployment must have containers."
    c = containers[0]
    if c.get("name") != "web":
        return False, "Deployment container name must be web."
    if c.get("image") != "nginx:alpine":
        return False, "Deployment container image must be nginx:alpine."

    # Validate Service
    if svc.get("kind") != "Service":
        return False, "service.yaml must define a Service."

    smeta = svc.get("metadata", {})
    if smeta.get("name") != "web-service":
        return False, "Service name must be web-service."

    if svc.get("spec", {}).get("type") != "ClusterIP":
        return False, "Service type must be ClusterIP."

    selector = svc.get("spec", {}).get("selector", {})
    if selector.get("app") != "web":
        return False, "Service selector must match app=web."

    ports = svc.get("spec", {}).get("ports", [])
    if not ports:
        return False, "Service must define port 80."

    p = ports[0]
    if p.get("port") != 80 or p.get("targetPort") != 80:
        return False, "Service port and targetPort must both be 80."

    return True, "Deployment + Service integration is correct!"

