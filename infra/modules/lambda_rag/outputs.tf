output "indexer_function_name" {
  value = aws_lambda_function.indexer.function_name
}

output "retriever_function_name" {
  value = aws_lambda_function.retriever.function_name
}
