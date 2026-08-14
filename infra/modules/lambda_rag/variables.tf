variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "indexer_role_arn" {
  type = string
}

variable "retriever_role_arn" {
  type = string
}

variable "raw_bucket_id" {
  description = "Raw-data bucket name (for the S3 -> indexer trigger)"
  type        = string
}

variable "raw_bucket_arn" {
  type = string
}

variable "opensearch_endpoint" {
  type = string
}

variable "opensearch_index_name" {
  type    = string
  default = "consumer-law-text"
}

variable "package_path" {
  description = <<-EOT
    Path to the built Lambda deployment zip. CI builds this (source under src/
    plus third-party deps) and Terraform deploys the artifact — the standard
    build-in-CI / deploy-artifact split. See scripts/build_lambda.sh.
  EOT
  type        = string
  default     = "../build/rag_lambda.zip"
}

variable "aws_region" {
  type = string
}
