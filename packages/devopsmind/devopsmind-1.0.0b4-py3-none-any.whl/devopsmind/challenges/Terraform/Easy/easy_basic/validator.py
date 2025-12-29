#!/usr/bin/env python3
import os
import re

def validate():
    if not os.path.exists("main.tf"):
        return False, "main.tf is missing."

    with open("main.tf") as f:
        content = f.read()

    # Check provider block
    if not re.search(r'provider\s+"aws"\s*\{', content):
        return False, 'Provider "aws" block is missing.'

    # Check region
    if not re.search(r'region\s*=\s*"us-east-1"', content):
        return False, 'Provider aws must define region = "us-east-1".'

    return True, "Terraform provider block is correct!"
