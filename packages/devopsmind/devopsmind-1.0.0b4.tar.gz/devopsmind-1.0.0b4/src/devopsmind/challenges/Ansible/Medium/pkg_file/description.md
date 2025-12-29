Modify or create playbook.yml to perform two tasks:

1. Install the package: tree  
2. Create a file: /tmp/info.txt  
   - Owner does not matter
   - Content must be exactly: Ansible Works

Use modules:
- package (or apt/yum depending on the OS)
- copy or file module with content parameter

The validator checks structure (not actual system changes).
