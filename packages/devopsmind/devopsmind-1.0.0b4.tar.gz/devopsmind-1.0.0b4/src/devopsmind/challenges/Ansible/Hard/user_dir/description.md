In playbook.yml, write a fully idempotent configuration:

1. Create a user named: deploy  
2. Ensure a directory exists: /opt/deploy  
   - It must be owned by deploy  
   - Permissions must be 0755  

Modules to use:
- user
- file

Validator checks playbook structure, not system-level execution.

This challenge teaches:
- Idempotent Ansible design
- Module usage for user + directory
- Logical task ordering
