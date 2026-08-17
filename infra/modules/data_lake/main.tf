# S3 data lake: a raw bucket (source files, law text) and a processed bucket
# (partitioned Parquet the Glue tables read). Both are private, versioned,
# encrypted at rest, TLS-only in transit, and expire noncurrent versions.

data "aws_caller_identity" "current" {}

locals {
  # S3 bucket names share one global namespace, so a bare
  # "<project>-raw-<env>" would collide with any other account that picked the
  # same project name. Suffixing the account id keeps them globally unique.
  suffix          = "${var.environment}-${data.aws_caller_identity.current.account_id}"
  raw_bucket_name = "${var.project_name}-raw-${local.suffix}"
  processed_name  = "${var.project_name}-processed-${local.suffix}"
}

resource "aws_s3_bucket" "raw" {
  bucket = local.raw_bucket_name
}

resource "aws_s3_bucket" "processed" {
  bucket = local.processed_name
}

resource "aws_s3_bucket_versioning" "raw" {
  bucket = aws_s3_bucket.raw.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_versioning" "processed" {
  bucket = aws_s3_bucket.processed.id
  versioning_configuration {
    status = "Enabled"
  }
}

# SSE-S3 (AES256) on both buckets — a data lake should never store objects
# unencrypted at rest. Swap to aws:kms with a CMK if key-level audit/rotation
# is required.
resource "aws_s3_bucket_server_side_encryption_configuration" "raw" {
  bucket = aws_s3_bucket.raw.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "processed" {
  bucket = aws_s3_bucket.processed.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "raw" {
  bucket                  = aws_s3_bucket.raw.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "processed" {
  bucket                  = aws_s3_bucket.processed.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Deny any request that isn't over TLS. Encryption at rest without enforced
# encryption in transit leaves a gap; this closes it on both buckets.
data "aws_iam_policy_document" "tls_only" {
  for_each = {
    raw       = aws_s3_bucket.raw.arn
    processed = aws_s3_bucket.processed.arn
  }

  statement {
    sid       = "DenyInsecureTransport"
    effect    = "Deny"
    actions   = ["s3:*"]
    resources = [each.value, "${each.value}/*"]

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

resource "aws_s3_bucket_policy" "raw" {
  bucket = aws_s3_bucket.raw.id
  policy = data.aws_iam_policy_document.tls_only["raw"].json

  # A bucket policy must not race the public-access block, which vets policies.
  depends_on = [aws_s3_bucket_public_access_block.raw]
}

resource "aws_s3_bucket_policy" "processed" {
  bucket     = aws_s3_bucket.processed.id
  policy     = data.aws_iam_policy_document.tls_only["processed"].json
  depends_on = [aws_s3_bucket_public_access_block.processed]
}

# Housekeeping: drop abandoned multipart uploads, and expire old object
# versions so versioning doesn't accumulate storage cost forever.
resource "aws_s3_bucket_lifecycle_configuration" "raw" {
  bucket = aws_s3_bucket.raw.id

  rule {
    id     = "expire-noncurrent-and-abort-mpu"
    status = "Enabled"

    filter {}

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }

    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "processed" {
  bucket = aws_s3_bucket.processed.id

  rule {
    id     = "expire-noncurrent-and-abort-mpu"
    status = "Enabled"

    filter {}

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }

    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }
}
