### 🧠 Ansible Master — Role Structure & Variables (Static)

Your task is to design a **proper Ansible role structure**.

You must create the following files:

### 1. roles/web/defaults/main.yml
```yaml
app_port: 8080
```

### 2. roles/web/tasks/main.yml
```yam
- name: Print application port
  debug:
    msg: "App running on port {{ app_port }}"
```

### ⚠️ Rules:

- Use variables from defaults (do not hardcode values)

- Follow standard Ansible role directory structure

- Do NOT run Ansible

### 🎯 Goal:
* Demonstrate understanding of Ansible roles and variable precedence.
