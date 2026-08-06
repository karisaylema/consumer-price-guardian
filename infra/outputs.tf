output "raw_data_bucket" {
  value = module.data_lake.raw_bucket_name
}

output "processed_data_bucket" {
  value = module.data_lake.processed_bucket_name
}
