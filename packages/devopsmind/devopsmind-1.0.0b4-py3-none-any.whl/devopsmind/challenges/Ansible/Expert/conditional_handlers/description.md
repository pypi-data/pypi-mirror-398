### 🧠 Ansible Expert — Conditionals & Handlers (Static)

You must design a playbook that demonstrates **handlers** and **conditional logic**.

Create a file named `playbook.yml`:

```yaml
- hosts: all
  tasks:
    - name: Update configuration
      copy:
        dest: /etc/myapp.conf
        content: "enabled=true"
      notify: restart app
      when: enable_app

  handlers:
    - name: restart app
      debug:
        msg: "Restarting application"
```
### ⚠️ Rules:

- Task must use when

- Task must notify a handler

- Handler must exist and be named correctly

- Do NOT run Ansible

### 🎯 Goal:  

* Demonstrate expert-level Ansible control flow.
