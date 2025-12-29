"""
Configuration loader for Joblet SDK.

This module handles loading configuration from various sources:
1. Default location: ~/.rnx/rnx-config.yml
2. Custom config file specified by RNX_CONFIG_PATH environment variable
3. Direct parameters passed to the client

The configuration file supports multiple nodes/profiles and includes
connection details and mTLS certificates.
"""

import os
import tempfile
from pathlib import Path
from typing import Dict, Optional, Tuple, cast

import yaml


class ConfigLoader:
    """Handles loading and parsing Joblet configuration files."""

    DEFAULT_CONFIG_PATH = Path.home() / ".rnx" / "rnx-config.yml"

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration loader.

        Args:
            config_path: Optional path to configuration file. If not provided,
                        checks RNX_CONFIG_PATH env var, then uses default location.
        """
        if config_path:
            self.config_path = Path(config_path)
        elif os.environ.get("RNX_CONFIG_PATH"):
            self.config_path = Path(os.environ["RNX_CONFIG_PATH"])
        else:
            self.config_path = self.DEFAULT_CONFIG_PATH

        self.config: Optional[Dict] = None
        self._temp_files: list[str] = []

    def load(self) -> bool:
        """
        Load the configuration file.

        Returns:
            bool: True if config was loaded successfully, False otherwise.
        """
        if not self.config_path.exists():
            return False

        try:
            with open(self.config_path, "r") as f:
                self.config = yaml.safe_load(f)
            return True
        except (yaml.YAMLError, IOError):
            return False

    def get_node_config(self, node_name: str = "default") -> Optional[Dict]:
        """
        Get configuration for a specific node.

        Args:
            node_name: Name of the node/profile to retrieve. Defaults to "default".

        Returns:
            Dict containing node configuration or None if not found.
        """
        if not self.config or "nodes" not in self.config:
            return None

        result = self.config["nodes"].get(node_name)
        return cast(Optional[Dict], result)

    def extract_connection_info(self, node_name: str = "default") -> Optional[Dict]:
        """
        Extract connection information from node configuration.

        Args:
            node_name: Name of the node/profile to use.

        Returns:
            Dict with host, port, node_id, and certificate paths, or None if not found.

        Raises:
            ValueError: If required field 'address' is missing.
        """
        node_config = self.get_node_config(node_name)
        if not node_config:
            return None

        # Validate required fields
        if "address" not in node_config:
            raise ValueError(f"Missing required field 'address' in node '{node_name}'")

        # Parse address (host:port)
        address = node_config.get("address", "")
        if ":" in address:
            host, port_str = address.rsplit(":", 1)
            try:
                port = int(port_str)
            except ValueError:
                port = 50051
        else:
            host = address
            port = 50051

        # Get nodeId if present
        node_id = node_config.get("nodeId", "")

        # Create temporary files for certificates if they're embedded
        cert_paths = self._create_cert_files(node_config)
        if not cert_paths:
            return None

        ca_cert_path, client_cert_path, client_key_path = cert_paths

        return {
            "host": host,
            "port": port,
            "node_id": node_id,
            "ca_cert_path": ca_cert_path,
            "client_cert_path": client_cert_path,
            "client_key_path": client_key_path,
        }

    def _create_cert_files(self, node_config: Dict) -> Optional[Tuple[str, str, str]]:
        """
        Create temporary certificate files from embedded certificate strings.

        Args:
            node_config: Node configuration containing certificates.

        Returns:
            Tuple of (ca_cert_path, client_cert_path, client_key_path) or None.
        """
        # Check if we have cert and key in the config
        cert_content = node_config.get("cert")
        key_content = node_config.get("key")

        if not cert_content or not key_content:
            return None

        # Get CA certificate from parent directory or config
        ca_cert_path = None

        # First try to find ca.crt or ca.pem in ~/.rnx/
        rnx_dir = Path.home() / ".rnx"
        for ca_file in ["ca.crt", "ca.pem"]:
            ca_path = rnx_dir / ca_file
            if ca_path.exists():
                ca_cert_path = str(ca_path)
                break

        # If not found, check if it's in the config
        if not ca_cert_path and "ca" in node_config:
            ca_temp = tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False)
            ca_temp.write(node_config["ca"])
            ca_temp.close()
            ca_cert_path = ca_temp.name
            self._temp_files.append(ca_cert_path)

        if not ca_cert_path:
            return None

        # Create temp files for client cert and key
        cert_temp = tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False)
        cert_temp.write(cert_content)
        cert_temp.close()
        self._temp_files.append(cert_temp.name)

        key_temp = tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False)
        key_temp.write(key_content)
        key_temp.close()
        self._temp_files.append(key_temp.name)

        return ca_cert_path, cert_temp.name, key_temp.name

    def cleanup(self):
        """Clean up temporary certificate files created during configuration loading.

        This method removes temporary files created when certificates were embedded
        in the configuration file. It's automatically called when the client is closed
        or when the object is deleted.
        """
        for temp_file in self._temp_files:
            try:
                os.unlink(temp_file)
            except OSError:
                pass
        self._temp_files.clear()

    def __del__(self):
        """Cleanup temporary files on deletion."""
        self.cleanup()
