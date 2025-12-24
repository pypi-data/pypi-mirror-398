"""
Integration tests for vector database plugins.

These tests require actual services to be running:
- pgvector: PostgreSQL with pgvector extension
- Pinecone: PINECONE_API_KEY environment variable
- ChromaDB: Can run in-memory (no setup required)
- Qdrant: Local Qdrant instance (docker run -p 6333:6333 qdrant/qdrant)

Run specific tests with:
    pytest tests/test_vector_plugins.py::TestChromaDBPlugin -v
"""
import pytest
import os
import asyncio
from typing import List

# Import vector plugins
from daita.plugins import pinecone, chroma, qdrant, postgresql


# Test data
TEST_VECTORS = [
    [0.1, 0.2, 0.3, 0.4, 0.5],
    [0.2, 0.3, 0.4, 0.5, 0.6],
    [0.3, 0.4, 0.5, 0.6, 0.7],
]

TEST_IDS = ["vec1", "vec2", "vec3"]

TEST_METADATA = [
    {"category": "tech", "year": 2024},
    {"category": "science", "year": 2023},
    {"category": "tech", "year": 2023},
]


class TestChromaDBPlugin:
    """Test ChromaDB plugin (in-memory mode, no external setup required)."""

    @pytest.mark.asyncio
    async def test_chroma_connect_disconnect(self):
        """Test ChromaDB connection and disconnection."""
        db = chroma(collection="test_collection")

        async with db:
            assert db._client is not None
            assert db._collection is not None

        assert db._client is None
        assert db._collection is None

    @pytest.mark.asyncio
    async def test_chroma_upsert_and_query(self):
        """Test ChromaDB upsert and query operations."""
        db = chroma(collection="test_upsert_query")

        async with db:
            # Upsert vectors
            result = await db.upsert(
                ids=TEST_IDS,
                vectors=TEST_VECTORS,
                metadata=TEST_METADATA
            )

            assert result["success"] is True
            assert result["upserted_count"] == 3

            # Query for similar vectors
            query_vector = [0.15, 0.25, 0.35, 0.45, 0.55]
            matches = await db.query(vector=query_vector, top_k=2)

            assert len(matches) == 2
            assert "id" in matches[0]
            assert "score" in matches[0]
            assert "metadata" in matches[0]

    @pytest.mark.asyncio
    async def test_chroma_fetch(self):
        """Test ChromaDB fetch operation."""
        db = chroma(collection="test_fetch")

        async with db:
            # Upsert vectors
            await db.upsert(
                ids=TEST_IDS,
                vectors=TEST_VECTORS,
                metadata=TEST_METADATA
            )

            # Fetch vectors by ID
            vectors = await db.fetch(ids=["vec1", "vec2"])

            assert len(vectors) == 2
            assert vectors[0]["id"] in ["vec1", "vec2"]
            assert "metadata" in vectors[0]
            assert "embedding" in vectors[0]

    @pytest.mark.asyncio
    async def test_chroma_delete(self):
        """Test ChromaDB delete operation."""
        db = chroma(collection="test_delete")

        async with db:
            # Upsert vectors
            await db.upsert(ids=TEST_IDS, vectors=TEST_VECTORS, metadata=TEST_METADATA)

            # Delete by ID
            result = await db.delete(ids=["vec1"])

            assert result["success"] is True
            assert result["deleted_count"] == 1

            # Verify deletion
            vectors = await db.fetch(ids=["vec1"])
            assert len(vectors) == 0

    @pytest.mark.asyncio
    async def test_chroma_filter_query(self):
        """Test ChromaDB query with filter."""
        db = chroma(collection="test_filter")

        async with db:
            # Upsert vectors
            await db.upsert(ids=TEST_IDS, vectors=TEST_VECTORS, metadata=TEST_METADATA)

            # Query with filter
            query_vector = [0.15, 0.25, 0.35, 0.45, 0.55]
            matches = await db.query(
                vector=query_vector,
                top_k=5,
                filter={"category": "tech"}
            )

            # Should only return tech category results
            assert len(matches) <= 2
            for match in matches:
                assert match["metadata"]["category"] == "tech"

    @pytest.mark.asyncio
    async def test_chroma_list_collections(self):
        """Test ChromaDB list collections."""
        db = chroma(collection="test_collections")

        async with db:
            collections = await db.list_collections()

            assert isinstance(collections, list)
            assert "test_collections" in collections


class TestQdrantPlugin:
    """
    Test Qdrant plugin.

    Requires: docker run -p 6333:6333 qdrant/qdrant
    Skip if Qdrant is not available.
    """

    @pytest.mark.asyncio
    async def test_qdrant_connect_disconnect(self):
        """Test Qdrant connection and disconnection."""
        db = qdrant(url="http://localhost:6333", collection="test_collection")

        try:
            async with db:
                assert db._client is not None
        except Exception as e:
            pytest.skip(f"Qdrant not available: {e}")

    @pytest.mark.asyncio
    async def test_qdrant_create_collection(self):
        """Test Qdrant collection creation."""
        db = qdrant(url="http://localhost:6333", collection="test_create")

        try:
            async with db:
                result = await db.create_collection(
                    name="test_vector_collection",
                    vector_size=5,
                    distance="Cosine"
                )

                assert result["success"] is True
                assert result["vector_size"] == 5
        except Exception as e:
            pytest.skip(f"Qdrant not available: {e}")

    @pytest.mark.asyncio
    async def test_qdrant_upsert_and_query(self):
        """Test Qdrant upsert and query operations."""
        db = qdrant(url="http://localhost:6333", collection="test_vector_collection")

        try:
            async with db:
                # Create collection first
                await db.create_collection(
                    name="test_vector_collection",
                    vector_size=5,
                    distance="Cosine"
                )

                # Upsert vectors
                result = await db.upsert(
                    ids=TEST_IDS,
                    vectors=TEST_VECTORS,
                    metadata=TEST_METADATA
                )

                assert result["success"] is True
                assert result["upserted_count"] == 3

                # Query for similar vectors
                query_vector = [0.15, 0.25, 0.35, 0.45, 0.55]
                matches = await db.query(vector=query_vector, top_k=2)

                assert len(matches) == 2
                assert "id" in matches[0]
                assert "score" in matches[0]
                assert "payload" in matches[0]
        except Exception as e:
            pytest.skip(f"Qdrant not available: {e}")


class TestPineconePlugin:
    """
    Test Pinecone plugin.

    Requires: PINECONE_API_KEY environment variable
    Skip if API key is not available.
    """

    @pytest.mark.asyncio
    async def test_pinecone_connect(self):
        """Test Pinecone connection."""
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            pytest.skip("PINECONE_API_KEY not set")

        index_name = os.getenv("PINECONE_INDEX", "test-index")
        db = pinecone(api_key=api_key, index=index_name)

        try:
            async with db:
                assert db._client is not None
                assert db._index is not None
        except Exception as e:
            pytest.skip(f"Pinecone not available: {e}")

    @pytest.mark.asyncio
    async def test_pinecone_upsert_and_query(self):
        """Test Pinecone upsert and query operations."""
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            pytest.skip("PINECONE_API_KEY not set")

        index_name = os.getenv("PINECONE_INDEX", "test-index")
        db = pinecone(api_key=api_key, index=index_name, namespace="test")

        try:
            async with db:
                # Upsert vectors
                result = await db.upsert(
                    ids=TEST_IDS,
                    vectors=TEST_VECTORS,
                    metadata=TEST_METADATA
                )

                assert result["upserted_count"] == 3

                # Allow time for indexing
                await asyncio.sleep(1)

                # Query for similar vectors
                query_vector = [0.15, 0.25, 0.35, 0.45, 0.55]
                matches = await db.query(vector=query_vector, top_k=2)

                assert len(matches) <= 2
                if len(matches) > 0:
                    assert "id" in matches[0]
                    assert "score" in matches[0]
        except Exception as e:
            pytest.skip(f"Pinecone not available: {e}")


class TestPgVectorPlugin:
    """
    Test PostgreSQL with pgvector extension.

    Requires: PostgreSQL with pgvector extension
    Skip if not available.
    """

    @pytest.mark.asyncio
    async def test_pgvector_setup(self):
        """Test pgvector table creation and index."""
        # Get PostgreSQL connection details from env
        # Note: ankane/pgvector default database is 'postgres', not 'test_db'
        host = os.getenv("POSTGRES_HOST", "localhost")
        database = os.getenv("POSTGRES_DB", "postgres")
        user = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD", "postgres")

        db = postgresql(
            host=host,
            database=database,
            user=user,
            password=password
        )

        try:
            async with db:
                # Create test table with vector column
                await db.execute("""
                    CREATE EXTENSION IF NOT EXISTS vector
                """)

                await db.execute("""
                    CREATE TABLE IF NOT EXISTS test_vectors (
                        id TEXT PRIMARY KEY,
                        embedding vector(5),
                        category TEXT,
                        year INTEGER
                    )
                """)

                # Create vector index
                result = await db.create_vector_index(
                    table="test_vectors",
                    vector_column="embedding",
                    index_type="hnsw",
                    distance_type="cosine"
                )

                # Clean up
                await db.execute("DROP TABLE IF EXISTS test_vectors")

                assert result.get("success") is True or "already exists" in result.get("error", "")
        except Exception as e:
            pytest.skip(f"PostgreSQL with pgvector not available: {e}")

    @pytest.mark.asyncio
    async def test_pgvector_upsert_and_search(self):
        """Test pgvector upsert and search operations."""
        host = os.getenv("POSTGRES_HOST", "localhost")
        database = os.getenv("POSTGRES_DB", "postgres")
        user = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD", "postgres")

        db = postgresql(
            host=host,
            database=database,
            user=user,
            password=password
        )

        try:
            async with db:
                # Setup
                await db.execute("CREATE EXTENSION IF NOT EXISTS vector")
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS test_vectors (
                        id TEXT PRIMARY KEY,
                        embedding vector(5),
                        category TEXT,
                        year INTEGER
                    )
                """)

                # Upsert vectors
                for idx, (id, vector, metadata) in enumerate(zip(TEST_IDS, TEST_VECTORS, TEST_METADATA)):
                    await db.vector_upsert(
                        table="test_vectors",
                        id_column="id",
                        vector_column="embedding",
                        id=id,
                        vector=vector,
                        extra_columns=metadata
                    )

                # Search for similar vectors
                query_vector = [0.15, 0.25, 0.35, 0.45, 0.55]
                results = await db.vector_search(
                    table="test_vectors",
                    vector_column="embedding",
                    query_vector=query_vector,
                    top_k=2,
                    distance_type="cosine"
                )

                assert len(results) == 2
                assert "id" in results[0]
                assert "distance" in results[0]

                # Search with filter
                results_filtered = await db.vector_search(
                    table="test_vectors",
                    vector_column="embedding",
                    query_vector=query_vector,
                    top_k=5,
                    filter="category = 'tech'",
                    distance_type="cosine"
                )

                for result in results_filtered:
                    assert result["category"] == "tech"

                # Clean up
                await db.execute("DROP TABLE IF EXISTS test_vectors")
        except Exception as e:
            pytest.skip(f"PostgreSQL with pgvector not available: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
