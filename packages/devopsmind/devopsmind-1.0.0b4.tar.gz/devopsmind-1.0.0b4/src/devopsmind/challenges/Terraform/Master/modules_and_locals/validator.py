#!/usr/bin/env python3
import os
import re

def read(p):
    with open(p) as f:
        return f.read()

def validate():
    required = [
        "locals.tf",
        "main.tf",
        "modules/compute/main.tf",
    ]

    for f in required:
        if not os.path.exists(f):
            return False, f"{f} missing."

    locals_tf = read("locals.tf")
    main_tf   = read("main.tf")
    mod_tf    = read("modules/compute/main.tf")

    # locals.tf
    if not re.search(r'locals\s*\{', locals_tf):
        return False, "locals block missing."
    if not re.search(r'env\s*=\s*"dev"', locals_tf):
        return False, "local env must be 'dev'."
    if not re.search(r'tags\s*=\s*\{', locals_tf):
        return False, "local tags map missing."

    # main.tf module usage
    if not re.search(r'module\s+"compute"', main_tf):
        return False, 'Module "compute" missing.'
    if not re.search(r'tags\s*=\s*local\.tags', main_tf):
        return False, "Module must receive local.tags."

    # module internals
    if not re.search(r'variable\s+"tags"', mod_tf):
        return False, "Module variable 'tags' missing."
    if not re.search(r'tags\s*=\s*var\.tags', mod_tf):
        return False, "Resource must use var.tags."

    return True, "Terraform Master challenge passed!"
