#!/usr/bin/env python3
import os, yaml

def validate():
    if not os.path.isdir("mychart"):
        return False, "Directory 'mychart' missing."

    chart_path = "mychart/Chart.yaml"
    if not os.path.exists(chart_path):
        return False, "Chart.yaml missing."

    tmpl_path = "mychart/templates/deployment.yaml"
    if not os.path.exists(tmpl_path):
        return False, "templates/deployment.yaml missing."

    # Validate Chart.yaml
    try:
        with open(chart_path) as f:
            chart = yaml.safe_load(f)
    except Exception as e:
        return False, f"Invalid YAML in Chart.yaml: {e}"

    if chart.get("apiVersion") != "v2":
        return False, "Chart.yaml apiVersion must be v2."

    if chart.get("name") != "mychart":
        return False, "Chart name must be mychart."

    if chart.get("version") != "0.1.0":
        return False, "Chart version must be 0.1.0."

    # Validate deployment.yaml (simple)
    try:
        with open(tmpl_path) as f:
            dep = yaml.safe_load(f)
    except Exception as e:
        return False, f"Invalid YAML in deployment.yaml: {e}"

    if dep.get("kind") != "Deployment":
        return False, "deployment.yaml must define kind: Deployment."

    if dep.get("metadata", {}).get("name") != "mychart-deploy":
        return False, "Deployment name must be mychart-deploy."

    return True, "Basic Helm chart structure is correct!"

