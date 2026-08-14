#!/usr/bin/env bash
# Build the RAG Lambda deployment package that infra/modules/lambda_rag deploys.
#
# Bundles the application source (src/) together with the third-party runtime
# dependencies the RAG functions need, into infra/build/rag_lambda.zip. Both
# Lambdas (indexer + retriever) share this one package; their handler strings
# select the entrypoint.
#
# Usage: scripts/build_lambda.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD_DIR="$ROOT/infra/build"
STAGE="$BUILD_DIR/stage"
ZIP="$BUILD_DIR/rag_lambda.zip"

# Only the deps the RAG path imports at runtime — keep the package lean.
RUNTIME_DEPS=(
  "boto3"
  "opensearch-py>=2.6.0"
  "requests-aws4auth>=1.2.3"
  "pydantic>=2.6.0"
  "python-dotenv>=1.0.0"
)

rm -rf "$STAGE" "$ZIP"
mkdir -p "$STAGE"

echo "Installing runtime deps into staging dir..."
pip install --quiet --target "$STAGE" "${RUNTIME_DEPS[@]}"

echo "Copying application source..."
cp -R "$ROOT/src" "$STAGE/src"

echo "Zipping -> $ZIP"
(cd "$STAGE" && zip -qr "$ZIP" .)

echo "Done: $ZIP"
