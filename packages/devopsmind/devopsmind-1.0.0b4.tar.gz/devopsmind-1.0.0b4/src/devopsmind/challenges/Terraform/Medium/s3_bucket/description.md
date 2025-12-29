Extend main.tf to include the following resource:

resource "aws_s3_bucket" "devops_bucket" {
  bucket = "devopsmind-bucket"
}

Provider block from EASY challenge may remain.

Validator ensures:
- Resource exists
- Name matches devops_bucket
- bucket property matches expected value
- Validator performs static Terraform syntax validation.

