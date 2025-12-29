#!/usr/bin/env python3
import os
import re

def read(p):
    with open(p) as f:
        return f.read()

def validate():
    for f in ["variables.tf", "locals.tf", "main.tf"]:
        if not os.path.exists(f):
            return False, f"{f} missing."

    vars_tf   = read("variables.tf")
    locals_tf = read("locals.tf")
    main_tf   = read("main.tf")

    # variable
    if not re.search(r'variable\s+"env"', vars_tf):
        return False, 'Variable "env" missing.'

    # conditional logic
    if not re.search(r'instance_count\s*=\s*var\.env\s*==\s*"prod"\s*\?', locals_tf):
        return False, "Conditional logic for instance_count missing."

    # resource count usage
    if not re.search(r'count\s*=\s*local\.instance_count', main_tf):
        return False, "Resource must use local.instance_count."

    # no duplicated resources
    if len(re.findall(r'resource\s+"aws_instance"', main_tf)) > 1:
        return False, "Duplicate aws_instance resources found."

    return True, "Terraform Expert challenge passed!"
