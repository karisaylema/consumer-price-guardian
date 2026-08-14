# RAG Lambdas: indexer (S3-triggered, chunk+embed+index) and retriever
# (invoked by the agent). Both share one deployment package; the handler string
# selects which entrypoint runs.

locals {
  prefix = "${var.project_name}-${var.environment}"
  env = {
    OPENSEARCH_COLLECTION_ENDPOINT = var.opensearch_endpoint
    OPENSEARCH_INDEX_NAME          = var.opensearch_index_name
    AWS_REGION                     = var.aws_region
  }
}

resource "aws_lambda_function" "indexer" {
  function_name = "${local.prefix}-rag-indexer"
  role          = var.indexer_role_arn
  runtime       = "python3.11"
  handler       = "src.rag.indexer.handler"
  filename      = var.package_path
  timeout       = 300
  memory_size   = 512

  environment {
    variables = local.env
  }
}

resource "aws_lambda_function" "retriever" {
  function_name = "${local.prefix}-rag-retriever"
  role          = var.retriever_role_arn
  runtime       = "python3.11"
  handler       = "src.rag.retriever.handler"
  filename      = var.package_path
  timeout       = 30
  memory_size   = 512

  environment {
    variables = local.env
  }
}

# Fire the indexer whenever a law-text object lands under consumer-law-text/.
resource "aws_lambda_permission" "s3_invoke_indexer" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.indexer.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = var.raw_bucket_arn
}

resource "aws_s3_bucket_notification" "law_text_upload" {
  bucket = var.raw_bucket_id

  lambda_function {
    lambda_function_arn = aws_lambda_function.indexer.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "consumer-law-text/"
  }

  depends_on = [aws_lambda_permission.s3_invoke_indexer]
}
