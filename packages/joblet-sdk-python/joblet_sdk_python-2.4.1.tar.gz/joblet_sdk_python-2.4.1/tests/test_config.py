"""Unit tests for config file loading functionality"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from joblet.config import ConfigLoader


class TestConfigLoader:
    """Test ConfigLoader class functionality"""

    @pytest.fixture
    def sample_config(self):
        """Sample configuration for testing"""
        return {
            "version": "3.0",
            "nodes": {
                "default": {
                    "address": "192.168.1.100:50051",
                    "persistAddress": "192.168.1.100:50052",
                    "nodeId": "test-node-default",
                    "cert": (
                        "-----BEGIN CERTIFICATE-----\n"
                        "test_cert\n"
                        "-----END CERTIFICATE-----"
                    ),
                    "key": (
                        "-----BEGIN PRIVATE KEY-----\n"
                        "test_key\n"
                        "-----END PRIVATE KEY-----"
                    ),
                    "ca": (
                        "-----BEGIN CERTIFICATE-----\n"
                        "test_ca\n"
                        "-----END CERTIFICATE-----"
                    ),
                },
                "production": {
                    "address": "prod.example.com:50051",
                    "cert": (
                        "-----BEGIN CERTIFICATE-----\n"
                        "prod_cert\n"
                        "-----END CERTIFICATE-----"
                    ),
                    "key": (
                        "-----BEGIN PRIVATE KEY-----\n"
                        "prod_key\n"
                        "-----END PRIVATE KEY-----"
                    ),
                    "ca": (
                        "-----BEGIN CERTIFICATE-----\n"
                        "prod_ca\n"
                        "-----END CERTIFICATE-----"
                    ),
                },
            },
        }

    @pytest.fixture
    def temp_config_file(self, sample_config):
        """Create a temporary config file"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            yaml.dump(sample_config, f)
            config_path = f.name

        yield config_path

        # Cleanup
        try:
            os.unlink(config_path)
        except OSError:
            pass

    def test_init_with_custom_path(self, temp_config_file):
        """Test initialization with custom config path"""
        loader = ConfigLoader(config_path=temp_config_file)
        assert loader.config_path == Path(temp_config_file)

    def test_init_with_env_variable(self, temp_config_file):
        """Test initialization with RNX_CONFIG_PATH environment variable"""
        with patch.dict(os.environ, {"RNX_CONFIG_PATH": temp_config_file}):
            loader = ConfigLoader()
            assert loader.config_path == Path(temp_config_file)

    def test_init_with_default_path(self):
        """Test initialization with default path"""
        loader = ConfigLoader()
        assert loader.config_path == Path.home() / ".rnx" / "rnx-config.yml"

    def test_load_valid_config(self, temp_config_file):
        """Test loading a valid config file"""
        loader = ConfigLoader(config_path=temp_config_file)
        assert loader.load() is True
        assert loader.config is not None
        assert "nodes" in loader.config

    def test_load_missing_config(self):
        """Test loading when config file doesn't exist"""
        loader = ConfigLoader(config_path="/non/existent/path.yml")
        assert loader.load() is False
        assert loader.config is None

    def test_load_invalid_yaml(self):
        """Test loading invalid YAML file"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            invalid_path = f.name

        try:
            loader = ConfigLoader(config_path=invalid_path)
            assert loader.load() is False
        finally:
            os.unlink(invalid_path)

    def test_get_node_config(self, temp_config_file):
        """Test getting node configuration"""
        loader = ConfigLoader(config_path=temp_config_file)
        loader.load()

        # Get default node
        default_node = loader.get_node_config("default")
        assert default_node is not None
        assert default_node["address"] == "192.168.1.100:50051"

        # Get production node
        prod_node = loader.get_node_config("production")
        assert prod_node is not None
        assert prod_node["address"] == "prod.example.com:50051"

        # Get non-existent node
        missing_node = loader.get_node_config("nonexistent")
        assert missing_node is None

    def test_extract_connection_info_with_port(self, temp_config_file):
        """Test extracting connection info with port in address"""
        loader = ConfigLoader(config_path=temp_config_file)
        loader.load()

        conn_info = loader.extract_connection_info("default")
        assert conn_info is not None
        assert conn_info["host"] == "192.168.1.100"
        assert conn_info["port"] == 50051
        assert conn_info["node_id"] == "test-node-default"

    def test_extract_connection_info_without_port(self, sample_config):
        """Test extracting connection info without port in address"""
        # Modify config to have address without port
        sample_config["nodes"]["default"]["address"] = "192.168.1.100"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            yaml.dump(sample_config, f)
            config_path = f.name

        try:
            loader = ConfigLoader(config_path=config_path)
            loader.load()

            conn_info = loader.extract_connection_info("default")
            assert conn_info is not None
            assert conn_info["host"] == "192.168.1.100"
            assert conn_info["port"] == 50051  # Should use default port
            assert conn_info["node_id"] == "test-node-default"
        finally:
            os.unlink(config_path)

    @patch("os.path.exists")
    def test_extract_connection_info_with_ca_cert(self, mock_exists, temp_config_file):
        """Test extracting connection info finds CA certificate"""
        mock_exists.return_value = True

        loader = ConfigLoader(config_path=temp_config_file)
        loader.load()

        with patch("pathlib.Path.exists", return_value=True):
            conn_info = loader.extract_connection_info("default")
            assert conn_info is not None
            # Should find ca.crt in ~/.rnx/
            assert "ca_cert_path" in conn_info

    def test_create_cert_files(self, temp_config_file):
        """Test creating temporary certificate files"""
        loader = ConfigLoader(config_path=temp_config_file)
        loader.load()

        node_config = loader.get_node_config("default")

        # Mock the CA cert path
        with patch("pathlib.Path.exists", return_value=True):
            cert_paths = loader._create_cert_files(node_config)
            assert cert_paths is not None

            ca_path, client_cert_path, client_key_path = cert_paths

            # Check that temp files were created
            assert os.path.exists(client_cert_path)
            assert os.path.exists(client_key_path)

            # Cleanup
            loader.cleanup()

            # Files should be deleted after cleanup
            assert not os.path.exists(client_cert_path)
            assert not os.path.exists(client_key_path)

    def test_cleanup_temp_files(self, temp_config_file):
        """Test cleanup of temporary files"""
        loader = ConfigLoader(config_path=temp_config_file)
        loader.load()

        # Create some temp files
        with patch("pathlib.Path.exists", return_value=True):
            loader.extract_connection_info("default")

            # Record temp files
            temp_files = loader._temp_files.copy()
            assert len(temp_files) > 0

            # Cleanup
            loader.cleanup()

            # Check files are deleted
            for temp_file in temp_files:
                # Skip CA cert
                if temp_file != str(Path.home() / ".rnx" / "ca.crt"):
                    assert not os.path.exists(temp_file)

            # Temp files list should be empty
            assert len(loader._temp_files) == 0

    def test_config_loader_with_embedded_ca_cert(self, sample_config):
        """Test config with embedded CA certificate"""
        # Add CA cert to config
        sample_config["nodes"]["default"][
            "ca_cert"
        ] = "-----BEGIN CERTIFICATE-----\nca_cert\n-----END CERTIFICATE-----"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            yaml.dump(sample_config, f)
            config_path = f.name

        try:
            loader = ConfigLoader(config_path=config_path)
            loader.load()

            conn_info = loader.extract_connection_info("default")
            assert conn_info is not None
            assert "ca_cert_path" in conn_info

            # CA cert should be a temp file
            assert os.path.exists(conn_info["ca_cert_path"])

            # Cleanup
            loader.cleanup()
        finally:
            os.unlink(config_path)

    def test_missing_address_field(self, sample_config):
        """Test that missing address field raises ValueError"""
        # Remove address field
        del sample_config["nodes"]["default"]["address"]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            yaml.dump(sample_config, f)
            config_path = f.name

        try:
            loader = ConfigLoader(config_path=config_path)
            loader.load()

            # Should raise ValueError for missing address
            with pytest.raises(ValueError, match="Missing required field 'address'"):
                loader.extract_connection_info("default")
        finally:
            os.unlink(config_path)

    def test_persistAddress_is_optional(self, sample_config):
        """Test that persistAddress field is optional (proto v2.3.0)"""
        # Remove persistAddress field - should still work
        if "persistAddress" in sample_config["nodes"]["default"]:
            del sample_config["nodes"]["default"]["persistAddress"]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            yaml.dump(sample_config, f)
            config_path = f.name

        try:
            loader = ConfigLoader(config_path=config_path)
            loader.load()

            # Should work fine without persistAddress
            conn_info = loader.extract_connection_info("default")
            assert conn_info is not None
            assert conn_info["host"] == "192.168.1.100"
            assert conn_info["port"] == 50051
        finally:
            os.unlink(config_path)


class TestJobletClientWithConfig:
    """Test JobletClient with config file support"""

    @pytest.fixture
    def mock_config_file(self):
        """Create a mock config file setup"""
        config_data = {
            "version": "3.0",
            "nodes": {
                "default": {
                    "address": "test-server:50051",
                    "persistAddress": "test-server:50052",
                    "nodeId": "test-node",
                    "cert": (
                        "-----BEGIN CERTIFICATE-----\n"
                        "test\n"
                        "-----END CERTIFICATE-----"
                    ),
                    "key": (
                        "-----BEGIN PRIVATE KEY-----\n"
                        "test\n"
                        "-----END PRIVATE KEY-----"
                    ),
                    "ca": (
                        "-----BEGIN CERTIFICATE-----\n"
                        "test_ca\n"
                        "-----END CERTIFICATE-----"
                    ),
                }
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name

        yield config_path

        try:
            os.unlink(config_path)
        except OSError:
            pass

    @patch("joblet.client.grpc.secure_channel")
    def test_client_init_with_config(self, mock_secure_channel, mock_config_file):
        """Test JobletClient initialization with config file"""
        from pathlib import Path

        from joblet import JobletClient

        # Create a selective mock that returns False only for ca.crt/ca.pem in ~/.rnx/
        original_exists = Path.exists

        def mock_exists_selective(self):
            # Return False for ca.crt/ca.pem checks
            if self.name in ["ca.crt", "ca.pem"] and ".rnx" in str(self):
                return False
            # For all other paths, use the real exists() method
            return original_exists(self)

        with patch("pathlib.Path.exists", new=mock_exists_selective):
            mock_channel = Mock()
            mock_secure_channel.return_value = mock_channel

            # Initialize client with config
            client = JobletClient(config_path=mock_config_file)

            assert client.host == "test-server"
            assert client.port == 50051

            # Cleanup
            client.close()

    @patch("joblet.client.grpc.secure_channel")
    def test_client_init_with_explicit_params_override(
        self, mock_secure_channel, temp_cert_files
    ):
        """Test that explicit parameters override config values"""
        from joblet import JobletClient

        mock_channel = Mock()
        mock_secure_channel.return_value = mock_channel

        # Initialize with explicit parameters
        client = JobletClient(
            host="explicit-host",
            port=9999,
            ca_cert_path=temp_cert_files["ca_cert_path"],
            client_cert_path=temp_cert_files["client_cert_path"],
            client_key_path=temp_cert_files["client_key_path"],
        )

        assert client.host == "explicit-host"
        assert client.port == 9999

        client.close()

    def test_client_init_missing_params_and_config(self, temp_cert_files):
        """Test client initialization fails when params and
        config are missing"""
        from joblet import JobletClient

        # Try to initialize without enough parameters
        with pytest.raises(ValueError) as exc_info:
            JobletClient(
                host="test-host",
                # Missing port, certificates and no config
                config_path="/non/existent/config.yml",
            )

        assert "Missing required parameters" in str(exc_info.value)
