terraform {
  required_version = ">= 1.5.0"
}

provider "aws" {
  region = "us-east-1"
}

resource "aws_s3_bucket" "example" {
  bucket = "replace-with-your-unique-bucket-name"

  tags = {
    Name        = "iac-converter-example"
    Environment = "development"
  }
}
