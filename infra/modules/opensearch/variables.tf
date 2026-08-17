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

variable "allow_public_network_access" {
  description = <<-EOT
    If true, the collection's data plane is reachable from the public internet
    (still SigV4-authenticated). Convenient for a solo sandbox. Set to false and
    front the collection with a VPC endpoint (aws_opensearchserverless_vpc_endpoint)
    for anything beyond that.
  EOT
  type        = bool
  default     = true
}
