"""Singleton MongoDB client for AWS Lambda and serverless environments."""

from mongo_client.client import mongo

__version__ = "0.1.0"
__all__ = ["mongo"]
