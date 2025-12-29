#!/usr/bin/env python3
import os
import re

def read(path):
    with open(path) as f:
        return f.read()

def validate():
    # Required files
    for f in ["variables.tf", "main.tf", "outputs.tf"]:
        if not os.path.exists(f):
            return False, f"{f} missing."

    vars_tf = read("variables.tf")
    main_tf = read("main.tf")
    out_tf  = read("outputs.tf")

    # Validate variables
    if not re.search(r'variable\s+"instance_type"\s*\{', vars_tf):
        return False, 'variable "instance_type" missing.'
    if not re.search(r'variable\s+"ami"\s*\{', vars_tf):
        return False, 'variable "ami" missing.'

    # Validate resource
    if not re.search(r'resource\s+"aws_instance"\s+"dev"\s*\{', main_tf):
        return False, 'Resource "aws_instance" "dev" missing.'

    if not re.search(r'instance_type\s*=\s*var\.instance_type', main_tf):
        return False, "instance_type must reference var.instance_type."

    if not re.search(r'ami\s*=\s*var\.ami', main_tf):
        return False, "ami must reference var.ami."

    # Ensure no hardcoded literals
    if re.search(r'instance_type\s*=\s*"', main_tf):
        return False, "instance_type must not be hardcoded."
    if re.search(r'ami\s*=\s*"', main_tf):
        return False, "ami must not be hardcoded."

    # Validate output
    if not re.search(r'output\s+"instance_id"\s*\{', out_tf):
        return False, 'Output "instance_id" missing.'

    if not re.search(r'value\s*=\s*aws_instance\.dev\.id', out_tf):
        return False, "Output instance_id must reference aws_instance.dev.id."

    return True, "Hard Terraform challenge is correct!"
