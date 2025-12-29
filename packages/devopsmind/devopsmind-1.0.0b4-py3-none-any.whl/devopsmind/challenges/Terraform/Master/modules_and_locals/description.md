### 🧠 Terraform Master — Locals & Modules (Static)

Your task is to structure Terraform code using **locals** and **modules**.

You must create the following files:

### 1. locals.tf
```hcl
locals {
  env  = "dev"
  tags = {
    project = "devopsmind"
    env     = local.env
  }
}


###2. main.tf
```hcl
module "compute" {
  source = "./modules/compute"
  tags   = local.tags
}
```
###3. modules/compute/main.tf
```hcl
variable "tags" {
  type = map(string)
}

resource "aws_instance" "example" {
  tags = var.tags
}
```

### ⚠️ Rules:

- Do NOT hardcode tag values in the resource

- Tags must flow: locals → module → resource

- Do NOT run Terraform

### 🎯 Goal:
* Demonstrate clean Terraform composition and reuse.
