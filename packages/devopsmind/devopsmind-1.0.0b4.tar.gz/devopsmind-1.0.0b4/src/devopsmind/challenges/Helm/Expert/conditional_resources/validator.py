#!/usr/bin/env python3
import os
import yaml

def validate():
    values_path = "mychart/values.yaml"
    cm_path = "mychart/templates/configmap.yaml"

    if not os.path.exists(values_path):
        return False, "values.yaml missing."
    if not os.path.exists(cm_path):
        return False, "configmap.yaml missing."

    try:
        values = yaml.safe_load(open(values_path))
    except Exception as e:
        return False, f"Invalid YAML in values.yaml: {e}"

    cfg = values.get("config", {})
    if cfg.get("enabled") is not True:
        return False, "config.enabled must be true."
    if cfg.get("message") != "Hello Helm":
        return False, "config.message must be 'Hello Helm'."

    content = open(cm_path).read()

    if "{{- if .Values.config.enabled }}" not in content and "{{ if .Values.config.enabled }}" not in content:
        return False, "ConfigMap must be conditionally rendered using if .Values.config.enabled."

    if "{{ .Values.config.message }}" not in content:
        return False, "ConfigMap must use {{ .Values.config.message }}."

    if "{{ .Chart.Name }}-config" not in content:
        return False, "ConfigMap name must use {{ .Chart.Name }}-config."

    return True, "Helm Expert challenge passed!"
