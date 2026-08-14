variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "indexer_role_arn" {
  description = "IAM role ARN (indexer Lambda) granted write access to the collection"
  type        = string
}

variable "retriever_role_arn" {
  description = "IAM role ARN (retriever Lambda) granted read access to the collection"
  type        = string
}
