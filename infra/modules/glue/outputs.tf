output "database_name" {
  value = aws_glue_catalog_database.this.name
}

output "athena_workgroup" {
  value = aws_athena_workgroup.this.name
}

output "athena_output_location" {
  value = "s3://${var.processed_bucket_name}/athena-results/"
}

output "table_names" {
  value = [for t in aws_glue_catalog_table.source : t.name]
}
