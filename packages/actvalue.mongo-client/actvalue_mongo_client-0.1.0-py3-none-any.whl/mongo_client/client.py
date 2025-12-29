"""MongoDB connection singleton implementation."""

import asyncio
import os

from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

CONNECT_TIMEOUT_MS = 30000


class MongoDbConnection:
    """Singleton MongoDB connection manager."""

    def __init__(self) -> None:
        """Initialize the connection manager."""
        self._db: AsyncDatabase | None = None
        self._lock = asyncio.Lock()
        self._is_connecting = False

    async def _mongo_connect(self) -> AsyncDatabase:
        """Establish a new MongoDB connection.

        Returns:
            AsyncDatabase: The connected database instance.

        Raises:
            Exception: If connection fails.
        """
        try:
            self._is_connecting = True

            mongo_url = os.environ.get("MONGO_URL")
            if not mongo_url:
                raise ValueError("MONGO_URL environment variable is required")

            pool_size = int(os.environ.get("MONGO_POOL_SIZE", "5"))

            client = AsyncMongoClient(
                mongo_url,
                minPoolSize=pool_size,
                connectTimeoutMS=CONNECT_TIMEOUT_MS,
                socketTimeoutMS=1440000,  # 24 minutes
                maxIdleTimeMS=3000,
            )

            db = client.get_database()
            self._db = db
            self._is_connecting = False
            return db
        except Exception as error:
            print(f"MongoDB connection error: {error}")
            self._db = None
            self._is_connecting = False
            raise

    async def get_db(self) -> AsyncDatabase:
        """Get the database connection, creating it if necessary.

        This method implements a singleton pattern with concurrent access handling.
        If a connection is being established by another coroutine, this method
        will wait for that connection to complete.

        Returns:
            AsyncDatabase: The connected database instance.
        """
        if self._db is not None:
            return self._db

        # Wait if another coroutine is connecting
        max_iterations = CONNECT_TIMEOUT_MS // 100
        for _ in range(max_iterations):
            if self._is_connecting:
                await asyncio.sleep(0.1)
            else:
                break

        # Check if connection was established while waiting
        if self._db is not None:
            return self._db

        # Establish connection with lock to prevent race conditions
        async with self._lock:
            # Double-check after acquiring lock
            if self._db is not None:
                return self._db
            return await self._mongo_connect()


# Global singleton instance
mongo = MongoDbConnection()
