In this challenge you must implement:

### 1. variables.tf
variable "instance_type" {
  type = string
}

variable "ami" {
  type = string
}

### 2. main.tf
resource "aws_instance" "dev" {
  instance_type = var.instance_type
  ami           = var.ami
}

### 3. outputs.tf
output "instance_id" {
  value = aws_instance.dev.id
}

Validator checks:
- Variables defined
- Resource references variables (no literal values)
- Output block is correct
- Validator performs static Terraform structure validation.
