#!/usr/bin/env python3
import os
import re

def validate():
    if not os.path.exists("main.tf"):
        return False, "main.tf is missing."

    with open("main.tf") as f:
        content = f.read()

    # Check resource block
    if not re.search(r'resource\s+"aws_s3_bucket"\s+"devops_bucket"\s*\{', content):
        return False, 'Resource "aws_s3_bucket" "devops_bucket" is missing.'

    # Check bucket name
    if not re.search(r'bucket\s*=\s*"devopsmind-bucket"', content):
        return False, 'Bucket name must be "devopsmind-bucket".'

    return True, "S3 bucket resource is correct!"
