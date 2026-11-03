terraform {
  required_version = ">= 1.5.0"
}

provider "aws" {
  region = "ap-south-1"
}

module "vpc" {
  source = "./modules/vpc"
  cidr_block = "10.0.0.0/16"
  environment = "production"
}
