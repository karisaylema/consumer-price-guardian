# Execution roles for the RAG Lambdas. Kept in their own module so the
# OpenSearch module can reference the role ARNs in its data-access policy
# without creating a module dependency cycle with lambda_rag.
#
# Note on aoss: OpenSearch Serverless authorizes data-plane calls via its own
# access policy (see modules/opensearch). The IAM side only needs the coarse
# aoss:APIAccessAll action, so it is granted on "*" here rather than the
# collection ARN — which also avoids a cycle with the collection resource.

locals {
  prefix = "${var.project_name}-${var.environment}"
}

data "aws_iam_policy_document" "lambda_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

# --- Indexer role: read raw text, embed via Bedrock, write to OpenSearch ---
resource "aws_iam_role" "indexer" {
  name               = "${local.prefix}-rag-indexer"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

data "aws_iam_policy_document" "indexer" {
  statement {
    sid       = "ReadRawLawText"
    actions   = ["s3:GetObject"]
    resources = ["${var.raw_bucket_arn}/consumer-law-text/*"]
  }
  statement {
    sid       = "InvokeBedrockEmbeddings"
    actions   = ["bedrock:InvokeModel"]
    resources = ["*"]
  }
  statement {
    sid       = "OpenSearchDataPlane"
    actions   = ["aoss:APIAccessAll"]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "indexer" {
  name   = "indexer"
  role   = aws_iam_role.indexer.id
  policy = data.aws_iam_policy_document.indexer.json
}

resource "aws_iam_role_policy_attachment" "indexer_logs" {
  role       = aws_iam_role.indexer.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# --- Retriever role: embed via Bedrock, read from OpenSearch ---
resource "aws_iam_role" "retriever" {
  name               = "${local.prefix}-rag-retriever"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

data "aws_iam_policy_document" "retriever" {
  statement {
    sid       = "InvokeBedrockEmbeddings"
    actions   = ["bedrock:InvokeModel"]
    resources = ["*"]
  }
  statement {
    sid       = "OpenSearchDataPlane"
    actions   = ["aoss:APIAccessAll"]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "retriever" {
  name   = "retriever"
  role   = aws_iam_role.retriever.id
  policy = data.aws_iam_policy_document.retriever.json
}

resource "aws_iam_role_policy_attachment" "retriever_logs" {
  role       = aws_iam_role.retriever.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}
