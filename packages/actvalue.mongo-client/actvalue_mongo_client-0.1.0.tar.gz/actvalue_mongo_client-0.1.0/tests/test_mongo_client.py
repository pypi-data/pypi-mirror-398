"""Tests for MongoDB client singleton."""

import os
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mongo_client import mongo


@pytest.fixture(autouse=True)
async def setup_env() -> AsyncGenerator[None]:
    """Set up test environment variables."""
    os.environ["MONGO_URL"] = "mongodb://localhost:27017/testdb"
    os.environ["MONGO_POOL_SIZE"] = "10"
    yield
    # Reset the singleton state after each test
    mongo._db = None
    mongo._is_connecting = False


@pytest.fixture
def mock_client() -> MagicMock:
    """Create a mock MongoDB client."""
    mock_db = MagicMock()
    mock_client = MagicMock()
    mock_client.get_database.return_value = mock_db
    return mock_client


@pytest.mark.unit
@patch("mongo_client.client.AsyncMongoClient")
async def test_mongo_client_basic(mock_mongo_client: MagicMock, mock_client: MagicMock) -> None:
    """Test basic MongoDB client functionality."""
    # Setup mock
    mock_mongo_client.return_value = mock_client
    mock_db = mock_client.get_database.return_value
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection

    # Mock insert_one
    mock_result = MagicMock()
    mock_result.inserted_id = "test_id"
    mock_collection.insert_one = AsyncMock(return_value=mock_result)

    # Mock find
    mock_cursor = MagicMock()
    mock_cursor.to_list = AsyncMock(return_value=[{"username": "test123", "password": "test123"}])
    mock_collection.find.return_value = mock_cursor

    # Mock delete_many
    mock_collection.delete_many = AsyncMock()

    # Test
    db = await mongo.get_db()
    assert db is mock_db

    users = db["users"]
    result = await users.insert_one({"username": "test123", "password": "test123"})
    assert result.inserted_id is not None

    docs = await users.find({"username": "test123"}).to_list(length=None)
    assert len(docs) == 1
    assert docs[0]["username"] == "test123"

    # Cleanup
    await users.delete_many({"username": "test123"})


@pytest.mark.unit
@patch("mongo_client.client.AsyncMongoClient")
async def test_mongo_client_reuse(mock_mongo_client: MagicMock, mock_client: MagicMock) -> None:
    """Test that the same connection is reused."""
    # Setup mock
    mock_mongo_client.return_value = mock_client
    mock_db = mock_client.get_database.return_value
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection

    # Mock operations
    mock_collection.insert_one = AsyncMock()
    mock_collection.find_one = AsyncMock(return_value={"username": "test123"})
    mock_collection.delete_many = AsyncMock()

    # Test
    db1 = await mongo.get_db()
    users = db1["users1"]
    await users.insert_one({"username": "test123", "password": "test123"})

    db2 = await mongo.get_db()
    users2 = db2["users1"]
    result = await users2.find_one({"username": "test123"})
    assert result is not None

    # Verify same database instance
    assert db1 is db2

    # Cleanup
    await users.delete_many({"username": "test123"})


@pytest.mark.unit
@patch("mongo_client.client.AsyncMongoClient")
async def test_mongo_client_concurrent_reuse(
    mock_mongo_client: MagicMock, mock_client: MagicMock
) -> None:
    """Test concurrent connections return the same instance."""
    import asyncio

    # Setup mock
    mock_mongo_client.return_value = mock_client
    mock_db = mock_client.get_database.return_value
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection

    # Mock operations
    mock_collection.insert_one = AsyncMock()
    mock_collection.find_one = AsyncMock(return_value={"username": "test123"})
    mock_collection.delete_many = AsyncMock()

    # Request connections concurrently
    db1, db2 = await asyncio.gather(mongo.get_db(), mongo.get_db())

    users = db1["users2"]
    await users.insert_one({"username": "test123", "password": "test123"})

    users2 = db2["users2"]
    result = await users2.find_one({"username": "test123"})
    assert result is not None

    # Verify same database instance
    assert db1 is db2

    # Cleanup
    await users.delete_many({"username": "test123"})
