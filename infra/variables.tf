variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Prefix used for naming all resources"
  type        = string
  default     = "consumer-price-guardian"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "sandbox"
}
