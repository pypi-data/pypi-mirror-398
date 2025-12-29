Create a full Helm integration between a Deployment and a templated ConfigMap.

File requirements:

1. In mychart/values.yaml add:
     config:
       message: "Hello from Helm"

2. Create template: mychart/templates/configmap.yaml
     - apiVersion: v1
       kind: ConfigMap
       metadata.name: {{ .Chart.Name }}-config
       data:
         message: {{ .Values.config.message }}

3. Modify templates/deployment.yaml:
     - Add a volume referencing the ConfigMap:
         volumes:
           - name: cfg
             configMap:
               name: {{ .Chart.Name }}-config

     - Add volumeMount:
         volumeMounts:
           - mountPath: /config
             name: cfg

Validator checks structure and templating usage.
