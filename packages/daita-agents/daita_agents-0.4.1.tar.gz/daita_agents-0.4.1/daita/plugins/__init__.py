"""
Plugin system for Daita Agents.

This module provides database, vector database, API, cloud storage, search, collaboration, and MCP integrations:

Database Plugins:
- PostgreSQL plugin for async database operations (with pgvector support)
- MySQL plugin for async database operations
- MongoDB plugin for async document database operations
- Snowflake plugin for cloud data warehouse operations

Vector Database Plugins:
- Pinecone plugin for managed cloud vector database
- ChromaDB plugin for local/embedded vector database
- Qdrant plugin for self-hosted vector database
- PostgreSQL with pgvector extension for vector operations

Integration Plugins:
- REST API plugin for HTTP client functionality
- AWS S3 plugin for cloud object storage operations
- Slack plugin for team collaboration and notifications
- Elasticsearch plugin for search and analytics
- MCP plugin for Model Context Protocol server integration

All plugins follow async patterns and provide simple, clean interfaces
without over-engineering.

Usage:
    ```python
    from daita.plugins import postgresql, mysql, mongodb, snowflake
    from daita.plugins import pinecone, chroma, qdrant
    from daita.plugins import rest, s3, slack, elasticsearch, mcp
    from daita import SubstrateAgent

    # Database plugins
    async with postgresql(host="localhost", database="mydb") as db:
        results = await db.query("SELECT * FROM users")

    # Vector database plugins
    async with pinecone(api_key="...", index="docs") as db:
        results = await db.query(vector=[0.1, 0.2, ...], top_k=5)

    async with chroma(path="./vectors", collection="docs") as db:
        results = await db.query(vector=[0.1, 0.2, ...], top_k=5)

    async with qdrant(url="http://localhost:6333", collection="docs") as db:
        results = await db.query(vector=[0.1, 0.2, ...], top_k=5)

    # PostgreSQL with pgvector
    async with postgresql(host="localhost", database="mydb") as db:
        results = await db.vector_search(
            table="documents",
            vector_column="embedding",
            query_vector=[0.1, 0.2, ...],
            top_k=5
        )

    # REST API plugin
    async with rest(base_url="https://api.example.com") as api:
        data = await api.get("/users")

    # S3 plugin
    async with s3(bucket="my-bucket", region="us-west-2") as storage:
        data = await storage.get_object("data/file.csv", format="pandas")

    # Slack plugin
    async with slack(token="xoxb-token") as slack_client:
        await slack_client.send_agent_summary("#alerts", agent_results)

    # Elasticsearch plugin
    async with elasticsearch(hosts=["localhost:9200"]) as es:
        results = await es.search("logs", {"match": {"level": "ERROR"}}, focus=["timestamp", "message"])

    # MCP plugin with agent integration
    agent = SubstrateAgent(
        name="file_analyzer",
        mcp=mcp.server(command="uvx", args=["mcp-server-filesystem", "/data"])
    )
    result = await agent.process("Read report.csv and calculate totals")
    ```
"""

# Database plugins
from .postgresql import PostgreSQLPlugin, postgresql
from .mysql import MySQLPlugin, mysql
from .mongodb import MongoDBPlugin, mongodb
from .snowflake import SnowflakePlugin, snowflake

# Vector database plugins
from .pinecone import PineconePlugin, pinecone
from .chroma import ChromaPlugin, chroma
from .qdrant import QdrantPlugin, qdrant

# API plugins  
from .rest import RESTPlugin, rest

# Cloud storage plugins
from .s3 import S3Plugin, s3

# Collaboration plugins
from .slack import SlackPlugin, slack

# Search and analytics plugins
from .elasticsearch import ElasticsearchPlugin, elasticsearch

# Messaging plugins
from .redis_messaging import RedisMessagingPlugin, redis_messaging

# MCP plugin
from . import mcp

# Simple plugin access class for SDK
class PluginAccess:
    """
    Simple plugin access for the SDK.
    
    Provides clean interface: sdk.plugins.postgresql(...)
    """
    
    def postgresql(self, **kwargs) -> PostgreSQLPlugin:
        """Create PostgreSQL plugin."""
        return postgresql(**kwargs)
    
    def mysql(self, **kwargs) -> MySQLPlugin:
        """Create MySQL plugin."""
        return mysql(**kwargs)
    
    def mongodb(self, **kwargs) -> MongoDBPlugin:
        """Create MongoDB plugin."""
        return mongodb(**kwargs)

    def snowflake(self, **kwargs) -> SnowflakePlugin:
        """Create Snowflake plugin."""
        return snowflake(**kwargs)

    def pinecone(self, **kwargs) -> PineconePlugin:
        """Create Pinecone plugin."""
        return pinecone(**kwargs)

    def chroma(self, **kwargs) -> ChromaPlugin:
        """Create ChromaDB plugin."""
        return chroma(**kwargs)

    def qdrant(self, **kwargs) -> QdrantPlugin:
        """Create Qdrant plugin."""
        return qdrant(**kwargs)

    def rest(self, **kwargs) -> RESTPlugin:
        """Create REST API plugin."""
        return rest(**kwargs)
    
    def s3(self, **kwargs) -> S3Plugin:
        """Create S3 plugin."""
        return s3(**kwargs)
    
    def slack(self, **kwargs) -> SlackPlugin:
        """Create Slack plugin."""
        return slack(**kwargs)
    
    def elasticsearch(self, **kwargs) -> ElasticsearchPlugin:
        """Create Elasticsearch plugin."""
        return elasticsearch(**kwargs)
    
    def redis_messaging(self, **kwargs) -> RedisMessagingPlugin:
        """Create Redis messaging plugin."""
        return redis_messaging(**kwargs)

# Export everything needed
__all__ = [
    # Plugin classes
    'PostgreSQLPlugin',
    'MySQLPlugin',
    'MongoDBPlugin',
    'SnowflakePlugin',
    'PineconePlugin',
    'ChromaPlugin',
    'QdrantPlugin',
    'RESTPlugin',
    'S3Plugin',
    'SlackPlugin',
    'ElasticsearchPlugin',
    'RedisMessagingPlugin',

    # Factory functions
    'postgresql',
    'mysql',
    'mongodb',
    'snowflake',
    'pinecone',
    'chroma',
    'qdrant',
    'rest',
    's3',
    'slack',
    'elasticsearch',
    'redis_messaging',

    # MCP module
    'mcp',

    # SDK access class
    'PluginAccess',
]