terraform {
  required_version = ">= 1.7"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Local state for now — solo project. Move to S3 backend + DynamoDB lock
  # if this becomes collaborative:
  #
  # backend "s3" {
  #   bucket         = "consumer-price-guardian-tfstate"
  #   key            = "global/terraform.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "consumer-price-guardian-tflock"
  #   encrypt        = true
  # }
}

provider "aws" {
  region = var.aws_region

  # Tag every resource for cost attribution and ownership. Given OpenSearch
  # Serverless and Bedrock bill by usage, tag-based cost tracking is the natural
  # companion to the cost warnings in the READMEs.
  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
