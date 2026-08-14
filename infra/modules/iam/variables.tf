variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "raw_bucket_arn" {
  description = "ARN of the raw-data bucket the indexer reads the law text from"
  type        = string
}
