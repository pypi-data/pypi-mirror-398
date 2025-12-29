### 🧠 Terraform Expert — Multi-Environment Design (Static)

You must design Terraform code that supports **multiple environments**
without duplicating resources.

Create the following files:

### 1. variables.tf
```hcl
variable "env" {
  type = string
}
```
### 2. locals.tf
```hcl
locals {
  instance_count = var.env == "prod" ? 3 : 1
}
```
### 3. main.tf
```hcl
resource "aws_instance" "app" {
  count = local.instance_count
}
```

### ⚠️ Rules:

- No duplicate resources

- No hardcoded environment logic inside resource blocks

- Use conditionals only in locals

### 🎯 Goal:
* Demonstrate expert-level Terraform design thinking.
