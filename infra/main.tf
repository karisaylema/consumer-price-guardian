# Root module — wires up all sub-modules.
# Currently only the data lake module is implemented; Glue, OpenSearch, and
# Lambda modules land in Phase 2/3 (see docs/roadmap.md).

module "data_lake" {
  source = "./modules/data_lake"

  project_name = var.project_name
  environment  = var.environment
}
