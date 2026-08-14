# OpenSearch Serverless collection for the legal-text vector store.
# Serverless requires three policies (encryption, network, data access) plus the
# collection itself. Access is scoped to the two Lambda roles that need it.

locals {
  collection_name = "${var.project_name}-${var.environment}"
}

data "aws_caller_identity" "current" {}

resource "aws_opensearchserverless_security_policy" "encryption" {
  name = "${local.collection_name}-enc"
  type = "encryption"
  policy = jsonencode({
    Rules = [{
      ResourceType = "collection"
      Resource     = ["collection/${local.collection_name}"]
    }]
    AWSOwnedKey = true
  })
}

# Public network access keeps the sandbox simple; tighten to a VPC endpoint for
# anything beyond a solo dev environment.
resource "aws_opensearchserverless_security_policy" "network" {
  name = "${local.collection_name}-net"
  type = "network"
  policy = jsonencode([{
    Description = "Public access for ${local.collection_name}"
    Rules = [
      { ResourceType = "collection", Resource = ["collection/${local.collection_name}"] },
      { ResourceType = "dashboard", Resource = ["collection/${local.collection_name}"] },
    ]
    AllowFromPublic = true
  }])
}

resource "aws_opensearchserverless_access_policy" "data" {
  name = "${local.collection_name}-data"
  type = "data"
  policy = jsonencode([{
    Description = "Indexer read/write, retriever read"
    Rules = [
      {
        ResourceType = "index"
        Resource     = ["index/${local.collection_name}/*"]
        Permission = [
          "aoss:CreateIndex", "aoss:UpdateIndex", "aoss:DescribeIndex",
          "aoss:ReadDocument", "aoss:WriteDocument",
        ]
      },
      {
        ResourceType = "collection"
        Resource     = ["collection/${local.collection_name}"]
        Permission   = ["aoss:CreateCollectionItems", "aoss:DescribeCollectionItems"]
      },
    ]
    Principal = [
      var.indexer_role_arn,
      var.retriever_role_arn,
      data.aws_caller_identity.current.arn, # let the deploying user manage indices
    ]
  }])
}

resource "aws_opensearchserverless_collection" "this" {
  name = local.collection_name
  type = "VECTORSEARCH"

  depends_on = [
    aws_opensearchserverless_security_policy.encryption,
    aws_opensearchserverless_security_policy.network,
    aws_opensearchserverless_access_policy.data,
  ]
}
