"""Tests for ORQ CLI."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from orq.cli import app
from orq.config import load_config, save_config, DEFAULT_CONFIG


runner = CliRunner()


class TestConfig:
    """Tests for configuration management."""

    def test_load_default_config(self, tmp_path, monkeypatch):
        """Test loading default config when file doesn't exist."""
        monkeypatch.setattr("orq.config.CONFIG_FILE", tmp_path / "config.yaml")
        config = load_config()
        assert config == DEFAULT_CONFIG

    def test_save_and_load_config(self, tmp_path, monkeypatch):
        """Test saving and loading configuration."""
        config_file = tmp_path / "config.yaml"
        monkeypatch.setattr("orq.config.CONFIG_FILE", config_file)
        monkeypatch.setattr("orq.config.CONFIG_DIR", tmp_path)

        test_config = {"api_key": "test-key", "environment": "staging"}
        save_config(test_config)

        loaded = load_config()
        assert loaded["api_key"] == "test-key"
        assert loaded["environment"] == "staging"


class TestCLI:
    """Tests for CLI commands."""

    def test_version(self):
        """Test version flag."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "orq-cli version" in result.stdout

    def test_help(self):
        """Test help output."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "deployments" in result.stdout
        assert "datasets" in result.stdout
        assert "files" in result.stdout

    def test_config_show(self, tmp_path, monkeypatch):
        """Test config show command."""
        config_file = tmp_path / "config.yaml"
        monkeypatch.setattr("orq.config.CONFIG_FILE", config_file)
        monkeypatch.setattr("orq.config.CONFIG_DIR", tmp_path)

        result = runner.invoke(app, ["config", "show"])
        assert result.exit_code == 0
        assert "Configuration" in result.stdout

    def test_config_set_get(self, tmp_path, monkeypatch):
        """Test config set and get commands."""
        config_file = tmp_path / "config.yaml"
        monkeypatch.setattr("orq.config.CONFIG_FILE", config_file)
        monkeypatch.setattr("orq.config.CONFIG_DIR", tmp_path)
        monkeypatch.setattr("orq.commands.config_cmd.CONFIG_FILE", config_file)

        result = runner.invoke(app, ["config", "set", "environment", "staging"])
        assert result.exit_code == 0

        result = runner.invoke(app, ["config", "get", "environment"])
        assert result.exit_code == 0
        assert "staging" in result.stdout


class TestDeployments:
    """Tests for deployment commands."""

    @patch("orq.commands.deployments.get_client")
    def test_list_deployments(self, mock_get_client):
        """Test listing deployments."""
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.data = [
            MagicMock(key="test-deployment", description="Test", created="2024-01-01")
        ]
        mock_client.deployments.list.return_value = mock_result
        mock_get_client.return_value = mock_client

        result = runner.invoke(app, ["deployments", "list", "--api-key", "test"])
        assert result.exit_code == 0

    @patch("orq.commands.deployments.get_client")
    def test_invoke_deployment(self, mock_get_client):
        """Test invoking a deployment."""
        mock_client = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Hello, World!"
        mock_result = MagicMock()
        mock_result.choices = [mock_choice]
        mock_client.deployments.invoke.return_value = mock_result
        mock_get_client.return_value = mock_client

        result = runner.invoke(app, [
            "deployments", "invoke", "test-key",
            "--api-key", "test",
            "--output", "json"
        ])
        assert result.exit_code == 0


class TestDatasets:
    """Tests for dataset commands."""

    @patch("orq.commands.datasets.get_client")
    def test_list_datasets(self, mock_get_client):
        """Test listing datasets."""
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.data = [
            MagicMock(id="ds-1", display_name="Test Dataset", created_at="2024-01-01")
        ]
        mock_client.datasets.list.return_value = mock_result
        mock_get_client.return_value = mock_client

        result = runner.invoke(app, ["datasets", "list", "--api-key", "test"])
        assert result.exit_code == 0

    @patch("orq.commands.datasets.get_client")
    def test_create_dataset(self, mock_get_client):
        """Test creating a dataset."""
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.id = "ds-new"
        mock_client.datasets.create.return_value = mock_result
        mock_get_client.return_value = mock_client

        result = runner.invoke(app, [
            "datasets", "create",
            "--name", "New Dataset",
            "--api-key", "test"
        ])
        assert result.exit_code == 0
        assert "ds-new" in result.stdout


class TestFiles:
    """Tests for file commands."""

    @patch("orq.commands.files.get_client")
    def test_list_files(self, mock_get_client):
        """Test listing files."""
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.data = [
            MagicMock(id="f-1", file_name="test.txt", purpose="retrieval", created_at="2024-01-01")
        ]
        mock_client.files.list.return_value = mock_result
        mock_get_client.return_value = mock_client

        result = runner.invoke(app, ["files", "list", "--api-key", "test"])
        assert result.exit_code == 0


class TestQuickCommands:
    """Tests for quick shortcut commands."""

    @patch("orq.client.get_client")
    def test_quick_list(self, mock_get_client):
        """Test quick list command."""
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.data = [MagicMock(key="test", description="Test")]
        mock_client.deployments.list.return_value = mock_result
        mock_get_client.return_value = mock_client

        result = runner.invoke(app, ["list", "deployments", "--api-key", "test"])
        assert result.exit_code == 0

    @patch("orq.client.get_client")
    def test_quick_invoke(self, mock_get_client):
        """Test quick invoke command."""
        mock_client = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Response"
        mock_result = MagicMock()
        mock_result.choices = [mock_choice]
        mock_client.deployments.invoke.return_value = mock_result
        mock_get_client.return_value = mock_client

        result = runner.invoke(app, [
            "invoke", "test-key",
            "-m", "Hello",
            "--api-key", "test"
        ])
        assert result.exit_code == 0
        assert "Response" in result.stdout


class TestIntegration:
    """Integration tests using real API (requires ORQ_API_KEY env var)."""

    @pytest.fixture
    def api_key(self):
        """Get API key from environment."""
        key = os.environ.get("ORQ_API_KEY")
        if not key:
            pytest.skip("ORQ_API_KEY not set")
        return key

    def test_real_list_deployments(self, api_key):
        """Test listing deployments with real API."""
        result = runner.invoke(app, [
            "deployments", "list",
            "--api-key", api_key,
            "--limit", "5"
        ])
        assert result.exit_code == 0
