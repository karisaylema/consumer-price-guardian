# Glue Data Catalog: one database, one partitioned Parquet table per source.
# The ingestion jobs (src/ingestion/*) write to these locations and register
# year/month partitions via boto3; the table schema here must match the
# non-partition columns those jobs write (see writer.write_parquet).

locals {
  # Table name == the PriceRecord.source value, so the ingestion job can derive
  # the target table from the records it produced.
  sources = ["ipc", "canasta_basica", "canasta_vital"]

  # Non-partition columns, in the order writer.write_parquet emits them.
  columns = [
    { name = "city", type = "string" },
    { name = "region", type = "string" },
    { name = "category", type = "string" },
    { name = "metric", type = "string" },
    { name = "value", type = "double" },
    { name = "unit", type = "string" },
  ]
}

resource "aws_glue_catalog_database" "this" {
  name = replace("${var.project_name}_${var.environment}", "-", "_")
}

resource "aws_glue_catalog_table" "source" {
  for_each = toset(local.sources)

  name          = each.key
  database_name = aws_glue_catalog_database.this.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    classification        = "parquet"
    "parquet.compression" = "SNAPPY"
    EXTERNAL              = "TRUE"
  }

  # Partition keys mirror the Hive-style S3 layout year=<yyyy>/month=<mm>.
  partition_keys {
    name = "year"
    type = "int"
  }
  partition_keys {
    name = "month"
    type = "string"
  }

  storage_descriptor {
    location      = "s3://${var.processed_bucket_name}/${each.key}/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"

    ser_de_info {
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
    }

    dynamic "columns" {
      for_each = local.columns
      content {
        name = columns.value.name
        type = columns.value.type
      }
    }
  }
}

# Dedicated Athena workgroup so query results land in a known prefix and cost
# controls / result encryption can be tuned in one place.
resource "aws_athena_workgroup" "this" {
  name = "${var.project_name}-${var.environment}"

  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true

    result_configuration {
      output_location = "s3://${var.processed_bucket_name}/athena-results/"
      encryption_configuration {
        encryption_option = "SSE_S3"
      }
    }
  }

  force_destroy = true
}
