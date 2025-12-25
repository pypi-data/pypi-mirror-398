"""Tests for mssql-mcp configuration."""

from mssql_mcp.config import MSSQLConfig


class TestMSSQLConfig:
    """Tests for MSSQLConfig settings class."""

    def test_config_loads_required_vars(self, mock_env):
        """Test required env vars are loaded."""
        config = MSSQLConfig()
        assert config.host == "test-host.example.com"
        assert config.user == "test-user"
        assert config.password == "test-password"
        assert config.database == "TestDB"

    def test_config_loads_optional_vars(self, mock_env):
        """Test optional env vars are loaded."""
        config = MSSQLConfig()
        assert config.port == 1433
        assert config.read_only is False
        assert config.max_rows == 1000
        assert config.query_timeout == 60

    def test_config_blocked_commands_parsing(self, mock_env):
        """Test parsing of blocked commands."""
        config = MSSQLConfig()
        assert "DROP" in config.blocked_commands
        assert "TRUNCATE" in config.blocked_commands
        assert "ALTER" in config.blocked_commands
        assert "CREATE" in config.blocked_commands

    def test_config_read_only_mode(self, mock_env_read_only):
        """Test read-only mode configuration."""
        config = MSSQLConfig()
        assert config.read_only is True

    def test_config_allowed_schemas_empty(self, mock_env):
        """Test allowed schemas defaults to empty list."""
        config = MSSQLConfig()
        assert config.allowed_schemas == []

    def test_config_http_settings_defaults(self, mock_env):
        """Test HTTP server settings have defaults."""
        config = MSSQLConfig()
        assert config.http_host == "127.0.0.1"
        assert config.http_port == 8080
        assert config.http_cors_origins == ["*"]

    def test_config_audit_disabled_by_default(self, mock_env):
        """Test audit logging is disabled by default."""
        config = MSSQLConfig()
        assert config.audit_enabled is False
