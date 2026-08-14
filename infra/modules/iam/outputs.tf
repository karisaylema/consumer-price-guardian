output "indexer_role_arn" {
  value = aws_iam_role.indexer.arn
}

output "retriever_role_arn" {
  value = aws_iam_role.retriever.arn
}
