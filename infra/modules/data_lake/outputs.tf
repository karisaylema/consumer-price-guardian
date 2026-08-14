output "raw_bucket_name" {
  value = aws_s3_bucket.raw.bucket
}

output "processed_bucket_name" {
  value = aws_s3_bucket.processed.bucket
}

output "raw_bucket_id" {
  value = aws_s3_bucket.raw.id
}

output "raw_bucket_arn" {
  value = aws_s3_bucket.raw.arn
}

output "processed_bucket_arn" {
  value = aws_s3_bucket.processed.arn
}
