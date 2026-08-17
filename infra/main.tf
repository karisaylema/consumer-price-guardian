# Root module — wires up all sub-modules.
#
# Dependency order (Terraform resolves this from the references below):
#   data_lake ─┬─> glue        (tables read from the processed bucket)
#              ├─> iam         (indexer reads law text from the raw bucket)
#              └─> lambda_rag  (indexer triggered by the raw bucket)
#   iam ───────> opensearch    (data-access policy scoped to the Lambda roles)
#   opensearch ─> lambda_rag   (functions need the collection endpoint)

module "data_lake" {
  source = "./modules/data_lake"

  project_name = var.project_name
  environment  = var.environment
}

module "glue" {
  source = "./modules/glue"

  project_name          = var.project_name
  environment           = var.environment
  processed_bucket_name = module.data_lake.processed_bucket_name
}

module "iam" {
  source = "./modules/iam"

  project_name   = var.project_name
  environment    = var.environment
  raw_bucket_arn = module.data_lake.raw_bucket_arn
}

module "opensearch" {
  source = "./modules/opensearch"

  project_name       = var.project_name
  environment        = var.environment
  indexer_role_arn   = module.iam.indexer_role_arn
  retriever_role_arn = module.iam.retriever_role_arn
}

module "lambda_rag" {
  source = "./modules/lambda_rag"

  project_name        = var.project_name
  environment         = var.environment
  indexer_role_arn    = module.iam.indexer_role_arn
  retriever_role_arn  = module.iam.retriever_role_arn
  raw_bucket_id       = module.data_lake.raw_bucket_id
  raw_bucket_arn      = module.data_lake.raw_bucket_arn
  opensearch_endpoint = module.opensearch.collection_endpoint
}
