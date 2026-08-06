"""
AWS client factory.

A single place that builds boto3 clients, all pinned to the configured region.
Clients are cached so repeated tool calls in the same process reuse one client
(boto3 clients are thread-safe for this) instead of paying setup cost each time.

Import the helpers, not boto3 directly, from ingestion/rag/agent code — it keeps
region wiring and any future credential/session tweaks in one file.
"""

from functools import lru_cache

import boto3

from src.shared.config import config


@lru_cache(maxsize=None)
def _client(service: str):
    return boto3.client(service, region_name=config.aws_region)


def s3():
    return _client("s3")


def glue():
    return _client("glue")


def athena():
    return _client("athena")


def bedrock_runtime():
    return _client("bedrock-runtime")
