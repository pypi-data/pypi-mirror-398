"""
Test suite for Snowflake Plugin - testing Snowflake data warehouse integration.

Comprehensive tests to ensure the Snowflake plugin works correctly with all features
including connection management, query operations, warehouse management, stage operations,
and tool registration.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock, Mock
from daita.plugins.snowflake import SnowflakePlugin, snowflake


class TestSnowflakeInitialization:
    """Test Snowflake plugin initialization."""

    def test_basic_initialization_password(self):
        """Test basic Snowflake plugin initialization with password."""
        plugin = SnowflakePlugin(
            account="xy12345",
            warehouse="COMPUTE_WH",
            database="MYDB",
            user="testuser",
            password="testpass"
        )

        assert plugin.account == "xy12345"
        assert plugin.warehouse == "COMPUTE_WH"
        assert plugin.database_name == "MYDB"
        assert plugin.user == "testuser"
        assert plugin.password == "testpass"
        assert plugin.schema == "PUBLIC"
        assert plugin._connection is None
        assert plugin._use_key_pair is False

    def test_initialization_with_key_pair(self):
        """Test initialization with key-pair authentication."""
        plugin = SnowflakePlugin(
            account="xy12345",
            warehouse="COMPUTE_WH",
            database="MYDB",
            user="testuser",
            private_key_path="/path/to/key.p8"
        )

        assert plugin._use_key_pair is True
        assert plugin.private_key_path == "/path/to/key.p8"

    def test_initialization_with_externalbrowser(self):
        """Test initialization with externalbrowser (SSO) authentication."""
        plugin = SnowflakePlugin(
            account="xy12345",
            warehouse="COMPUTE_WH",
            database="MYDB",
            user="testuser",
            authenticator="externalbrowser"
        )

        assert plugin.authenticator == "externalbrowser"
        assert plugin.connection_config['authenticator'] == "externalbrowser"
        assert plugin._use_key_pair is False

    def test_initialization_with_custom_schema(self):
        """Test initialization with custom schema."""
        plugin = SnowflakePlugin(
            account="xy12345",
            warehouse="COMPUTE_WH",
            database="MYDB",
            schema="CUSTOM_SCHEMA",
            user="testuser",
            password="testpass"
        )

        assert plugin.schema == "CUSTOM_SCHEMA"

    def test_initialization_with_role(self):
        """Test initialization with role."""
        plugin = SnowflakePlugin(
            account="xy12345",
            warehouse="COMPUTE_WH",
            database="MYDB",
            user="testuser",
            password="testpass",
            role="ANALYST"
        )

        assert plugin.role == "ANALYST"
        assert plugin.connection_config['role'] == "ANALYST"

    def test_missing_account_raises_error(self):
        """Test that missing account raises ValueError."""
        with pytest.raises(ValueError, match="account is required"):
            SnowflakePlugin(
                warehouse="COMPUTE_WH",
                database="MYDB",
                user="testuser",
                password="testpass"
            )

    def test_missing_warehouse_raises_error(self):
        """Test that missing warehouse raises ValueError."""
        with pytest.raises(ValueError, match="warehouse is required"):
            SnowflakePlugin(
                account="xy12345",
                database="MYDB",
                user="testuser",
                password="testpass"
            )

    def test_missing_database_raises_error(self):
        """Test that missing database raises ValueError."""
        with pytest.raises(ValueError, match="database is required"):
            SnowflakePlugin(
                account="xy12345",
                warehouse="COMPUTE_WH",
                user="testuser",
                password="testpass"
            )

    def test_missing_user_raises_error(self):
        """Test that missing user raises ValueError."""
        with pytest.raises(ValueError, match="user is required"):
            SnowflakePlugin(
                account="xy12345",
                warehouse="COMPUTE_WH",
                database="MYDB",
                password="testpass"
            )

    def test_missing_authentication_raises_error(self):
        """Test that missing password, key, and authenticator raises ValueError."""
        with pytest.raises(ValueError, match="Authentication required"):
            SnowflakePlugin(
                account="xy12345",
                warehouse="COMPUTE_WH",
                database="MYDB",
                user="testuser"
            )

    @patch.dict('os.environ', {
        'SNOWFLAKE_ACCOUNT': 'env_account',
        'SNOWFLAKE_WAREHOUSE': 'ENV_WH',
        'SNOWFLAKE_DATABASE': 'ENV_DB',
        'SNOWFLAKE_USER': 'env_user',
        'SNOWFLAKE_PASSWORD': 'env_pass',
        'SNOWFLAKE_SCHEMA': 'ENV_SCHEMA',
        'SNOWFLAKE_ROLE': 'ENV_ROLE'
    })
    def test_environment_variable_loading(self):
        """Test that environment variables are loaded correctly."""
        plugin = SnowflakePlugin()

        assert plugin.account == 'env_account'
        assert plugin.warehouse == 'ENV_WH'
        assert plugin.database_name == 'ENV_DB'
        assert plugin.user == 'env_user'
        assert plugin.password == 'env_pass'
        assert plugin.schema == 'ENV_SCHEMA'
        assert plugin.role == 'ENV_ROLE'

    @patch.dict('os.environ', {
        'SNOWFLAKE_ACCOUNT': 'env_account',
        'SNOWFLAKE_WAREHOUSE': 'ENV_WH',
        'SNOWFLAKE_DATABASE': 'ENV_DB',
        'SNOWFLAKE_USER': 'env_user',
        'SNOWFLAKE_AUTHENTICATOR': 'externalbrowser',
        'SNOWFLAKE_SCHEMA': 'ENV_SCHEMA'
    })
    def test_environment_variable_loading_with_authenticator(self):
        """Test that SNOWFLAKE_AUTHENTICATOR environment variable is loaded."""
        plugin = SnowflakePlugin()

        assert plugin.account == 'env_account'
        assert plugin.authenticator == 'externalbrowser'
        assert plugin.connection_config['authenticator'] == 'externalbrowser'


class TestSnowflakeConnection:
    """Test Snowflake connection management."""

    @pytest.mark.asyncio
    async def test_connect_disconnect_password(self):
        """Test connection and disconnection with password auth."""
        plugin = SnowflakePlugin(
            account="xy12345",
            warehouse="COMPUTE_WH",
            database="MYDB",
            user="testuser",
            password="testpass"
        )

        # Mock the snowflake module before importing
        mock_snowflake = MagicMock()
        mock_conn = MagicMock()
        mock_snowflake.connector.connect.return_value = mock_conn

        with patch.dict('sys.modules', {'snowflake': mock_snowflake, 'snowflake.connector': mock_snowflake.connector}):
            # Test connect
            await plugin.connect()
            assert plugin._connection == mock_conn
            mock_snowflake.connector.connect.assert_called_once()

            # Verify password auth was used
            call_kwargs = mock_snowflake.connector.connect.call_args[1]
            assert call_kwargs['account'] == "xy12345"
            assert call_kwargs['user'] == "testuser"
            assert call_kwargs['password'] == "testpass"
            assert 'private_key' not in call_kwargs

            # Test disconnect
            await plugin.disconnect()
            mock_conn.close.assert_called_once()
            assert plugin._connection is None

    @pytest.mark.asyncio
    async def test_connect_with_externalbrowser(self):
        """Test connection with externalbrowser authentication."""
        plugin = SnowflakePlugin(
            account="xy12345",
            warehouse="COMPUTE_WH",
            database="MYDB",
            user="testuser",
            authenticator="externalbrowser"
        )

        # Mock the snowflake module
        mock_snowflake = MagicMock()
        mock_conn = MagicMock()
        mock_snowflake.connector.connect.return_value = mock_conn

        with patch.dict('sys.modules', {'snowflake': mock_snowflake, 'snowflake.connector': mock_snowflake.connector}):
            await plugin.connect()
            assert plugin._connection == mock_conn
            mock_snowflake.connector.connect.assert_called_once()

            # Verify externalbrowser auth was used
            call_kwargs = mock_snowflake.connector.connect.call_args[1]
            assert call_kwargs['authenticator'] == "externalbrowser"
            assert 'password' not in call_kwargs
            assert 'private_key' not in call_kwargs

    @pytest.mark.asyncio
    async def test_connect_idempotent(self):
        """Test that multiple connect calls don't create duplicate connections."""
        plugin = SnowflakePlugin(
            account="xy12345",
            warehouse="COMPUTE_WH",
            database="MYDB",
            user="testuser",
            password="testpass"
        )

        # Mock the snowflake module
        mock_snowflake = MagicMock()
        mock_conn = MagicMock()
        mock_snowflake.connector.connect.return_value = mock_conn

        with patch.dict('sys.modules', {'snowflake': mock_snowflake, 'snowflake.connector': mock_snowflake.connector}):
            await plugin.connect()
            await plugin.connect()  # Second call should do nothing

            mock_snowflake.connector.connect.assert_called_once()  # Only called once

    @pytest.mark.asyncio
    async def test_connect_import_error(self):
        """Test connection with missing snowflake-connector-python."""
        from daita.core.exceptions import PluginError

        plugin = SnowflakePlugin(
            account="xy12345",
            warehouse="COMPUTE_WH",
            database="MYDB",
            user="testuser",
            password="testpass"
        )

        # Simulate missing module by not having it in sys.modules
        with patch.dict('sys.modules', {'snowflake': None, 'snowflake.connector': None}, clear=False):
            with pytest.raises(PluginError, match="snowflake-connector-python not installed"):
                await plugin.connect()

    @pytest.mark.asyncio
    async def test_connect_failure(self):
        """Test connection failure."""
        from daita.core.exceptions import ConnectionError as DaitaConnectionError

        plugin = SnowflakePlugin(
            account="xy12345",
            warehouse="COMPUTE_WH",
            database="MYDB",
            user="testuser",
            password="testpass"
        )

        # Mock the snowflake module with connection failure
        mock_snowflake = MagicMock()
        mock_snowflake.connector.connect.side_effect = Exception("Connection failed")

        with patch.dict('sys.modules', {'snowflake': mock_snowflake, 'snowflake.connector': mock_snowflake.connector}):
            with pytest.raises(DaitaConnectionError, match="Connection failed"):
                await plugin.connect()


class MockCursor:
    """Mock cursor for Snowflake connection."""

    def __init__(self):
        self.description = None
        self.rowcount = 0
        self._results = []
        self._execute_called = False

    def execute(self, sql, params=None):
        """Mock execute method."""
        self._execute_called = True
        self._sql = sql
        self._params = params
        return self

    def fetchall(self):
        """Mock fetchall method."""
        return self._results

    def close(self):
        """Mock close method."""
        pass


class TestSnowflakeQueryOperations:
    """Test Snowflake query operations."""

    @pytest.mark.asyncio
    async def test_query(self):
        """Test query execution."""
        plugin = SnowflakePlugin(
            account="xy12345",
            warehouse="COMPUTE_WH",
            database="MYDB",
            user="testuser",
            password="testpass"
        )

        mock_conn = MagicMock()
        mock_cursor = MockCursor()
        mock_cursor.description = [('id',), ('name',), ('age',)]
        mock_cursor._results = [
            (1, 'John', 30),
            (2, 'Jane', 25)
        ]
        mock_conn.cursor.return_value = mock_cursor
        plugin._connection = mock_conn

        result = await plugin.query("SELECT * FROM users")

        expected = [
            {'id': 1, 'name': 'John', 'age': 30},
            {'id': 2, 'name': 'Jane', 'age': 25}
        ]
        assert result == expected

    @pytest.mark.asyncio
    async def test_query_with_params(self):
        """Test query with parameters."""
        plugin = SnowflakePlugin(
            account="xy12345",
            warehouse="COMPUTE_WH",
            database="MYDB",
            user="testuser",
            password="testpass"
        )

        mock_conn = MagicMock()
        mock_cursor = MockCursor()
        mock_cursor.description = [('id',), ('name',), ('age',)]
        mock_cursor._results = [(1, 'John', 30)]
        mock_conn.cursor.return_value = mock_cursor
        plugin._connection = mock_conn

        result = await plugin.query("SELECT * FROM users WHERE age > %s", [25])

        assert len(result) == 1
        assert result[0]['name'] == 'John'

    @pytest.mark.asyncio
    async def test_query_empty_result(self):
        """Test query with empty result."""
        plugin = SnowflakePlugin(
            account="xy12345",
            warehouse="COMPUTE_WH",
            database="MYDB",
            user="testuser",
            password="testpass"
        )

        mock_conn = MagicMock()
        mock_cursor = MockCursor()
        mock_cursor._results = []
        mock_conn.cursor.return_value = mock_cursor
        plugin._connection = mock_conn

        result = await plugin.query("SELECT * FROM empty_table")
        assert result == []

    @pytest.mark.asyncio
    async def test_execute(self):
        """Test execute operation."""
        plugin = SnowflakePlugin(
            account="xy12345",
            warehouse="COMPUTE_WH",
            database="MYDB",
            user="testuser",
            password="testpass"
        )

        mock_conn = MagicMock()
        mock_cursor = MockCursor()
        mock_cursor.rowcount = 3
        mock_conn.cursor.return_value = mock_cursor
        plugin._connection = mock_conn

        result = await plugin.execute("DELETE FROM users WHERE age < %s", [20])

        assert result == 3

    @pytest.mark.asyncio
    async def test_auto_connect_on_query(self):
        """Test that query auto-connects if not connected."""
        plugin = SnowflakePlugin(
            account="xy12345",
            warehouse="COMPUTE_WH",
            database="MYDB",
            user="testuser",
            password="testpass"
        )

        # Mock the snowflake module
        mock_snowflake = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MockCursor()
        mock_cursor._results = []
        mock_conn.cursor.return_value = mock_cursor
        mock_snowflake.connector.connect.return_value = mock_conn

        with patch.dict('sys.modules', {'snowflake': mock_snowflake, 'snowflake.connector': mock_snowflake.connector}):
            await plugin.query("SELECT 1")

            mock_snowflake.connector.connect.assert_called_once()
            assert plugin._connection == mock_conn


class TestSnowflakeMetadataOperations:
    """Test Snowflake metadata operations."""

    @pytest.mark.asyncio
    async def test_tables(self):
        """Test tables listing."""
        plugin = SnowflakePlugin(
            account="xy12345",
            warehouse="COMPUTE_WH",
            database="MYDB",
            user="testuser",
            password="testpass"
        )

        mock_conn = MagicMock()
        mock_cursor = MockCursor()
        mock_cursor.description = [('name',), ('type',), ('schema',)]
        mock_cursor._results = [
            ('users', 'TABLE', 'PUBLIC'),
            ('products', 'TABLE', 'PUBLIC'),
            ('orders', 'TABLE', 'PUBLIC')
        ]
        mock_conn.cursor.return_value = mock_cursor
        plugin._connection = mock_conn

        tables = await plugin.tables()

        assert tables == ['users', 'products', 'orders']

    @pytest.mark.asyncio
    async def test_schemas(self):
        """Test schemas listing."""
        plugin = SnowflakePlugin(
            account="xy12345",
            warehouse="COMPUTE_WH",
            database="MYDB",
            user="testuser",
            password="testpass"
        )

        mock_conn = MagicMock()
        mock_cursor = MockCursor()
        mock_cursor.description = [('name',), ('owner',)]
        mock_cursor._results = [
            ('PUBLIC', 'SYSADMIN'),
            ('ANALYTICS', 'ANALYST'),
            ('STAGING', 'DEV')
        ]
        mock_conn.cursor.return_value = mock_cursor
        plugin._connection = mock_conn

        schemas = await plugin.schemas()

        assert schemas == ['PUBLIC', 'ANALYTICS', 'STAGING']

    @pytest.mark.asyncio
    async def test_describe(self):
        """Test table description."""
        plugin = SnowflakePlugin(
            account="xy12345",
            warehouse="COMPUTE_WH",
            database="MYDB",
            user="testuser",
            password="testpass"
        )

        mock_conn = MagicMock()
        mock_cursor = MockCursor()
        mock_cursor.description = [('name',), ('type',), ('kind',), ('null?',)]
        mock_cursor._results = [
            ('id', 'NUMBER(38,0)', 'COLUMN', 'N'),
            ('name', 'VARCHAR(255)', 'COLUMN', 'Y'),
            ('age', 'NUMBER(38,0)', 'COLUMN', 'Y')
        ]
        mock_conn.cursor.return_value = mock_cursor
        plugin._connection = mock_conn

        columns = await plugin.describe("users")

        assert len(columns) == 3
        assert columns[0]['name'] == 'id'
        assert columns[1]['type'] == 'VARCHAR(255)'

    @pytest.mark.asyncio
    async def test_databases(self):
        """Test databases listing."""
        plugin = SnowflakePlugin(
            account="xy12345",
            warehouse="COMPUTE_WH",
            database="MYDB",
            user="testuser",
            password="testpass"
        )

        mock_conn = MagicMock()
        mock_cursor = MockCursor()
        mock_cursor.description = [('name',), ('owner',)]
        mock_cursor._results = [
            ('PRODUCTION', 'SYSADMIN'),
            ('STAGING', 'SYSADMIN'),
            ('DEV', 'SYSADMIN')
        ]
        mock_conn.cursor.return_value = mock_cursor
        plugin._connection = mock_conn

        databases = await plugin.databases()

        assert databases == ['PRODUCTION', 'STAGING', 'DEV']


class TestSnowflakeWarehouseOperations:
    """Test Snowflake warehouse management."""

    @pytest.mark.asyncio
    async def test_list_warehouses(self):
        """Test warehouse listing."""
        plugin = SnowflakePlugin(
            account="xy12345",
            warehouse="COMPUTE_WH",
            database="MYDB",
            user="testuser",
            password="testpass"
        )

        mock_conn = MagicMock()
        mock_cursor = MockCursor()
        mock_cursor.description = [('name',), ('state',), ('size',)]
        mock_cursor._results = [
            ('COMPUTE_WH', 'STARTED', 'SMALL'),
            ('LOAD_WH', 'SUSPENDED', 'LARGE'),
            ('ANALYTICS_WH', 'STARTED', 'MEDIUM')
        ]
        mock_conn.cursor.return_value = mock_cursor
        plugin._connection = mock_conn

        warehouses = await plugin.list_warehouses()

        assert len(warehouses) == 3
        assert warehouses[0]['name'] == 'COMPUTE_WH'
        assert warehouses[1]['state'] == 'SUSPENDED'

    @pytest.mark.asyncio
    async def test_switch_warehouse(self):
        """Test warehouse switching."""
        plugin = SnowflakePlugin(
            account="xy12345",
            warehouse="COMPUTE_WH",
            database="MYDB",
            user="testuser",
            password="testpass"
        )

        mock_conn = MagicMock()
        mock_cursor = MockCursor()
        mock_conn.cursor.return_value = mock_cursor
        plugin._connection = mock_conn

        await plugin.switch_warehouse("LARGE_WH")

        assert plugin.warehouse == "LARGE_WH"

    @pytest.mark.asyncio
    async def test_get_current_warehouse(self):
        """Test getting current warehouse."""
        plugin = SnowflakePlugin(
            account="xy12345",
            warehouse="COMPUTE_WH",
            database="MYDB",
            user="testuser",
            password="testpass"
        )

        mock_conn = MagicMock()
        mock_cursor = MockCursor()
        mock_cursor.description = [('warehouse',)]
        mock_cursor._results = [('COMPUTE_WH',)]
        mock_conn.cursor.return_value = mock_cursor
        plugin._connection = mock_conn

        result = await plugin.get_current_warehouse()

        assert result['warehouse'] == 'COMPUTE_WH'


class TestSnowflakeStageOperations:
    """Test Snowflake stage operations."""

    @pytest.mark.asyncio
    async def test_list_stages(self):
        """Test stage listing."""
        plugin = SnowflakePlugin(
            account="xy12345",
            warehouse="COMPUTE_WH",
            database="MYDB",
            user="testuser",
            password="testpass"
        )

        mock_conn = MagicMock()
        mock_cursor = MockCursor()
        mock_cursor.description = [('name',), ('url',), ('type',)]
        mock_cursor._results = [
            ('my_stage', '', 'INTERNAL'),
            ('s3_stage', 's3://bucket/path/', 'EXTERNAL')
        ]
        mock_conn.cursor.return_value = mock_cursor
        plugin._connection = mock_conn

        stages = await plugin.list_stages()

        assert len(stages) == 2
        assert stages[0]['name'] == 'my_stage'
        assert stages[1]['type'] == 'EXTERNAL'

    @pytest.mark.asyncio
    async def test_put_file(self):
        """Test file upload to stage."""
        plugin = SnowflakePlugin(
            account="xy12345",
            warehouse="COMPUTE_WH",
            database="MYDB",
            user="testuser",
            password="testpass"
        )

        mock_conn = MagicMock()
        mock_cursor = MockCursor()
        mock_cursor.description = [('source',), ('target',), ('status',)]
        mock_cursor._results = [
            ('data.csv', '@my_stage/data.csv.gz', 'UPLOADED')
        ]
        mock_conn.cursor.return_value = mock_cursor
        plugin._connection = mock_conn

        result = await plugin.put_file("/local/data.csv", "@my_stage/")

        assert result['success'] is True
        assert result['files_uploaded'] == 1

    @pytest.mark.asyncio
    async def test_load_from_stage(self):
        """Test loading data from stage."""
        plugin = SnowflakePlugin(
            account="xy12345",
            warehouse="COMPUTE_WH",
            database="MYDB",
            user="testuser",
            password="testpass"
        )

        mock_conn = MagicMock()
        mock_cursor = MockCursor()
        mock_cursor.description = [('file',), ('rows_loaded',), ('status',)]
        mock_cursor._results = [
            ('data.csv', 1000, 'LOADED')
        ]
        mock_conn.cursor.return_value = mock_cursor
        plugin._connection = mock_conn

        result = await plugin.load_from_stage("my_table", "@my_stage/", "CSV")

        assert result['success'] is True
        assert result['rows_loaded'] == 1000


class TestSnowflakeToolRegistration:
    """Test Snowflake tool registration."""

    def test_get_tools(self):
        """Test that get_tools returns all expected tools."""
        plugin = SnowflakePlugin(
            account="xy12345",
            warehouse="COMPUTE_WH",
            database="MYDB",
            user="testuser",
            password="testpass"
        )

        tools = plugin.get_tools()

        # Should have 12 tools
        assert len(tools) == 12

        # Check tool names
        tool_names = [tool.name for tool in tools]
        expected_tools = [
            'query_database',
            'execute_sql',
            'list_tables',
            'list_schemas',
            'get_table_schema',
            'list_warehouses',
            'switch_warehouse',
            'get_query_history',
            'list_stages',
            'upload_to_stage',
            'load_from_stage',
            'create_stage'
        ]

        for expected in expected_tools:
            assert expected in tool_names

        # Check tool properties
        query_tool = next(t for t in tools if t.name == 'query_database')
        assert query_tool.category == 'database'
        assert query_tool.source == 'plugin'
        assert query_tool.plugin_name == 'Snowflake'
        assert query_tool.timeout_seconds == 60
        assert callable(query_tool.handler)

    @pytest.mark.asyncio
    async def test_tool_query_handler(self):
        """Test query_database tool handler."""
        plugin = SnowflakePlugin(
            account="xy12345",
            warehouse="COMPUTE_WH",
            database="MYDB",
            user="testuser",
            password="testpass"
        )

        mock_conn = MagicMock()
        mock_cursor = MockCursor()
        mock_cursor.description = [('id',), ('name',)]
        mock_cursor._results = [(1, 'John'), (2, 'Jane')]
        mock_conn.cursor.return_value = mock_cursor
        plugin._connection = mock_conn

        result = await plugin._tool_query({"sql": "SELECT * FROM users"})

        assert result['success'] is True
        assert result['row_count'] == 2
        assert len(result['rows']) == 2

    @pytest.mark.asyncio
    async def test_tool_execute_handler(self):
        """Test execute_sql tool handler."""
        plugin = SnowflakePlugin(
            account="xy12345",
            warehouse="COMPUTE_WH",
            database="MYDB",
            user="testuser",
            password="testpass"
        )

        mock_conn = MagicMock()
        mock_cursor = MockCursor()
        mock_cursor.rowcount = 5
        mock_conn.cursor.return_value = mock_cursor
        plugin._connection = mock_conn

        result = await plugin._tool_execute({"sql": "DELETE FROM users WHERE age < 18"})

        assert result['success'] is True
        assert result['affected_rows'] == 5

    @pytest.mark.asyncio
    async def test_tool_list_tables_handler(self):
        """Test list_tables tool handler."""
        plugin = SnowflakePlugin(
            account="xy12345",
            warehouse="COMPUTE_WH",
            database="MYDB",
            user="testuser",
            password="testpass"
        )

        mock_conn = MagicMock()
        mock_cursor = MockCursor()
        mock_cursor.description = [('name',)]
        mock_cursor._results = [('users',), ('products',)]
        mock_conn.cursor.return_value = mock_cursor
        plugin._connection = mock_conn

        result = await plugin._tool_list_tables({})

        assert result['success'] is True
        assert result['count'] == 2
        assert 'users' in result['tables']


class TestSnowflakeContextManager:
    """Test Snowflake context manager."""

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test Snowflake as context manager."""
        plugin = SnowflakePlugin(
            account="xy12345",
            warehouse="COMPUTE_WH",
            database="MYDB",
            user="testuser",
            password="testpass"
        )

        # Mock the snowflake module
        mock_snowflake = MagicMock()
        mock_conn = MagicMock()
        mock_snowflake.connector.connect.return_value = mock_conn

        with patch.dict('sys.modules', {'snowflake': mock_snowflake, 'snowflake.connector': mock_snowflake.connector}):
            async with plugin as sf:
                assert sf == plugin
                assert plugin._connection == mock_conn

            mock_conn.close.assert_called_once()


class TestSnowflakeFactory:
    """Test Snowflake factory function."""

    def test_factory_function(self):
        """Test snowflake factory function."""
        plugin = snowflake(
            account="xy12345",
            warehouse="COMPUTE_WH",
            database="MYDB",
            user="testuser",
            password="testpass"
        )

        assert isinstance(plugin, SnowflakePlugin)
        assert plugin.account == "xy12345"
        assert plugin.warehouse == "COMPUTE_WH"


class TestSnowflakeEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_disconnect_when_not_connected(self):
        """Test disconnect when not connected doesn't raise error."""
        plugin = SnowflakePlugin(
            account="xy12345",
            warehouse="COMPUTE_WH",
            database="MYDB",
            user="testuser",
            password="testpass"
        )

        # Should not raise error
        await plugin.disconnect()
        assert plugin._connection is None

    @pytest.mark.asyncio
    async def test_query_history(self):
        """Test query history retrieval."""
        plugin = SnowflakePlugin(
            account="xy12345",
            warehouse="COMPUTE_WH",
            database="MYDB",
            user="testuser",
            password="testpass"
        )

        mock_conn = MagicMock()
        mock_cursor = MockCursor()
        mock_cursor.description = [('query_id',), ('query_text',), ('status',)]
        mock_cursor._results = [
            ('qid1', 'SELECT * FROM users', 'SUCCESS'),
            ('qid2', 'INSERT INTO logs VALUES (1)', 'SUCCESS')
        ]
        mock_conn.cursor.return_value = mock_cursor
        plugin._connection = mock_conn

        history = await plugin.query_history(limit=10)

        assert len(history) == 2
        assert history[0]['query_id'] == 'qid1'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
