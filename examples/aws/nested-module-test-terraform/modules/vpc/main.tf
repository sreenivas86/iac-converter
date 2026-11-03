variable "cidr_block" {
  type = string
}

variable "environment" {
  type = string
}

resource "aws_vpc" "main" {
  cidr_block = var.cidr_block
}

output "vpc_id" {
  value = aws_vpc.main.id
}
