# These map 1:1 to the variables in .env.example — copy them into .env after
# `terraform apply` so the Python code can find the deployed resources.

output "raw_data_bucket" {
  value = module.data_lake.raw_bucket_name
}

output "processed_data_bucket" {
  value = module.data_lake.processed_bucket_name
}

output "glue_database_name" {
  value = module.glue.database_name
}

output "athena_workgroup" {
  value = module.glue.athena_workgroup
}

output "athena_output_location" {
  value = module.glue.athena_output_location
}

output "opensearch_collection_endpoint" {
  value = module.opensearch.collection_endpoint
}
