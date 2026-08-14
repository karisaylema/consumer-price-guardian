variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "processed_bucket_name" {
  description = "Name of the processed-data S3 bucket the tables read from"
  type        = string
}
