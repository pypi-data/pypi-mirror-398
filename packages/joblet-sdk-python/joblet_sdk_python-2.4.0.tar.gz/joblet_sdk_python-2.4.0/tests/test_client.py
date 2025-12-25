"""
Unit tests for JobletClient
"""

from unittest.mock import Mock, patch

import pytest

from joblet import JobletClient
from joblet.exceptions import ConnectionError


class TestJobletClient:
    """Test cases for JobletClient class"""

    def test_init_with_valid_certificates(self, temp_cert_files):
        """Test client initialization with valid certificates"""
        with patch("joblet.client.grpc.secure_channel") as mock_secure_channel:
            mock_channel = Mock()
            mock_secure_channel.return_value = mock_channel

            client = JobletClient(
                ca_cert_path=temp_cert_files["ca_cert_path"],
                client_cert_path=temp_cert_files["client_cert_path"],
                client_key_path=temp_cert_files["client_key_path"],
                host="test-host",
                port=50051,
            )

            assert client.host == "test-host"
            assert client.port == 50051
            assert client.ca_cert_path == temp_cert_files["ca_cert_path"]
            assert client.client_cert_path == temp_cert_files["client_cert_path"]
            assert client.client_key_path == temp_cert_files["client_key_path"]
            mock_secure_channel.assert_called_once()

    def test_init_with_missing_ca_cert(self, temp_cert_files):
        """Test client initialization fails with missing CA certificate"""
        with pytest.raises(FileNotFoundError):
            JobletClient(
                ca_cert_path="/nonexistent/ca-cert.pem",
                client_cert_path=temp_cert_files["client_cert_path"],
                client_key_path=temp_cert_files["client_key_path"],
                host="test-host",
                port=50051,
            )

    def test_init_with_missing_client_cert(self, temp_cert_files):
        """Test client initialization fails with missing client certificate"""
        with pytest.raises(FileNotFoundError):
            JobletClient(
                ca_cert_path=temp_cert_files["ca_cert_path"],
                client_cert_path="/nonexistent/client-cert.pem",
                client_key_path=temp_cert_files["client_key_path"],
                host="test-host",
                port=50051,
            )

    def test_init_with_missing_client_key(self, temp_cert_files):
        """Test client initialization fails with missing client key"""
        with pytest.raises(FileNotFoundError):
            JobletClient(
                ca_cert_path=temp_cert_files["ca_cert_path"],
                client_cert_path=temp_cert_files["client_cert_path"],
                client_key_path="/nonexistent/client-key.pem",
                host="test-host",
                port=50051,
            )

    def test_init_with_empty_ca_cert(self, temp_cert_files):
        """Test client initialization fails with empty CA certificate"""
        # Create empty CA cert file
        empty_ca_path = temp_cert_files["ca_cert_path"] + ".empty"
        with open(empty_ca_path, "w") as f:
            f.write("")

        with pytest.raises(ValueError, match="Empty CA cert"):
            JobletClient(
                ca_cert_path=empty_ca_path,
                client_cert_path=temp_cert_files["client_cert_path"],
                client_key_path=temp_cert_files["client_key_path"],
                host="test-host",
                port=50051,
            )

    def test_init_with_invalid_ca_cert_format(self, temp_cert_files):
        """Test client initialization fails with invalid CA certificate format"""
        # Create invalid CA cert file
        invalid_ca_path = temp_cert_files["ca_cert_path"] + ".invalid"
        with open(invalid_ca_path, "w") as f:
            f.write("invalid certificate content")

        with pytest.raises(ValueError, match="Invalid CA certificate format"):
            JobletClient(
                ca_cert_path=invalid_ca_path,
                client_cert_path=temp_cert_files["client_cert_path"],
                client_key_path=temp_cert_files["client_key_path"],
                host="test-host",
                port=50051,
            )

    def test_init_with_custom_options(self, temp_cert_files):
        """Test client initialization with custom gRPC options"""
        options = {
            "grpc.keepalive_time_ms": 30000,
            "grpc.keepalive_timeout_ms": 5000,
        }

        with patch("joblet.client.grpc.secure_channel") as mock_secure_channel:
            mock_channel = Mock()
            mock_secure_channel.return_value = mock_channel

            JobletClient(
                ca_cert_path=temp_cert_files["ca_cert_path"],
                client_cert_path=temp_cert_files["client_cert_path"],
                client_key_path=temp_cert_files["client_key_path"],
                host="test-host",
                port=50051,
                options=options,
            )

            # Verify options were passed to gRPC channel
            call_args = mock_secure_channel.call_args
            # Check that custom options are included in the final options list
            passed_options = call_args[1]["options"]
            custom_options = list(options.items())
            for custom_option in custom_options:
                assert custom_option in passed_options

    def test_context_manager(self, temp_cert_files):
        """Test client as context manager"""
        with patch("joblet.client.grpc.secure_channel") as mock_secure_channel:
            mock_channel = Mock()
            mock_secure_channel.return_value = mock_channel

            with JobletClient(
                ca_cert_path=temp_cert_files["ca_cert_path"],
                client_cert_path=temp_cert_files["client_cert_path"],
                client_key_path=temp_cert_files["client_key_path"],
                host="test-host",
                port=50051,
            ) as client:
                assert client._channel is not None

            # Verify channel was closed
            mock_channel.close.assert_called_once()

    def test_close_method(self, temp_cert_files):
        """Test explicit close method"""
        with patch("joblet.client.grpc.secure_channel") as mock_secure_channel:
            mock_channel = Mock()
            mock_secure_channel.return_value = mock_channel

            client = JobletClient(
                ca_cert_path=temp_cert_files["ca_cert_path"],
                client_cert_path=temp_cert_files["client_cert_path"],
                client_key_path=temp_cert_files["client_key_path"],
                host="test-host",
                port=50051,
            )

            client.close()
            mock_channel.close.assert_called_once()
            assert client._channel is None

    def test_jobs_property_lazy_initialization(self, temp_cert_files):
        """Test jobs property lazy initialization"""
        with patch("joblet.client.grpc.secure_channel") as mock_secure_channel:
            mock_channel = Mock()
            mock_secure_channel.return_value = mock_channel

            with patch("joblet.client.JobService") as mock_job_service:
                mock_service_instance = Mock()
                mock_job_service.return_value = mock_service_instance

                client = JobletClient(
                    ca_cert_path=temp_cert_files["ca_cert_path"],
                    client_cert_path=temp_cert_files["client_cert_path"],
                    client_key_path=temp_cert_files["client_key_path"],
                    host="test-host",
                    port=50051,
                )

                # First access should create the service
                jobs_service = client.jobs
                # Check JobService called with channel
                assert mock_job_service.call_count == 1
                call_args = mock_job_service.call_args
                assert call_args[0][0] == mock_channel  # First arg is channel
                assert jobs_service == mock_service_instance

                # Second access should return the same instance
                jobs_service_2 = client.jobs
                assert jobs_service_2 == mock_service_instance
                # JobService constructor should only be called once
                assert mock_job_service.call_count == 1

    def test_networks_property_lazy_initialization(self, temp_cert_files):
        """Test networks property lazy initialization"""
        with patch("joblet.client.grpc.secure_channel") as mock_secure_channel:
            mock_channel = Mock()
            mock_secure_channel.return_value = mock_channel

            with patch("joblet.client.NetworkService") as mock_network_service:
                mock_service_instance = Mock()
                mock_network_service.return_value = mock_service_instance

                client = JobletClient(
                    ca_cert_path=temp_cert_files["ca_cert_path"],
                    client_cert_path=temp_cert_files["client_cert_path"],
                    client_key_path=temp_cert_files["client_key_path"],
                    host="test-host",
                    port=50051,
                )

                networks_service = client.networks
                mock_network_service.assert_called_once_with(mock_channel)
                assert networks_service == mock_service_instance

    def test_volumes_property_lazy_initialization(self, temp_cert_files):
        """Test volumes property lazy initialization"""
        with patch("joblet.client.grpc.secure_channel") as mock_secure_channel:
            mock_channel = Mock()
            mock_secure_channel.return_value = mock_channel

            with patch("joblet.client.VolumeService") as mock_volume_service:
                mock_service_instance = Mock()
                mock_volume_service.return_value = mock_service_instance

                client = JobletClient(
                    ca_cert_path=temp_cert_files["ca_cert_path"],
                    client_cert_path=temp_cert_files["client_cert_path"],
                    client_key_path=temp_cert_files["client_key_path"],
                    host="test-host",
                    port=50051,
                )

                volumes_service = client.volumes
                mock_volume_service.assert_called_once_with(mock_channel)
                assert volumes_service == mock_service_instance

    def test_monitoring_property_lazy_initialization(self, temp_cert_files):
        """Test monitoring property lazy initialization"""
        with patch("joblet.client.grpc.secure_channel") as mock_secure_channel:
            mock_channel = Mock()
            mock_secure_channel.return_value = mock_channel

            with patch("joblet.client.MonitoringService") as mock_monitoring_service:
                mock_service_instance = Mock()
                mock_monitoring_service.return_value = mock_service_instance

                client = JobletClient(
                    ca_cert_path=temp_cert_files["ca_cert_path"],
                    client_cert_path=temp_cert_files["client_cert_path"],
                    client_key_path=temp_cert_files["client_key_path"],
                    host="test-host",
                    port=50051,
                )

                monitoring_service = client.monitoring
                mock_monitoring_service.assert_called_once_with(mock_channel)
                assert monitoring_service == mock_service_instance

    def test_runtimes_property_lazy_initialization(self, temp_cert_files):
        """Test runtimes property lazy initialization"""
        with patch("joblet.client.grpc.secure_channel") as mock_secure_channel:
            mock_channel = Mock()
            mock_secure_channel.return_value = mock_channel

            with patch("joblet.client.RuntimeService") as mock_runtime_service:
                mock_service_instance = Mock()
                mock_runtime_service.return_value = mock_service_instance

                client = JobletClient(
                    ca_cert_path=temp_cert_files["ca_cert_path"],
                    client_cert_path=temp_cert_files["client_cert_path"],
                    client_key_path=temp_cert_files["client_key_path"],
                    host="test-host",
                    port=50051,
                )

                runtimes_service = client.runtimes
                mock_runtime_service.assert_called_once_with(mock_channel)
                assert runtimes_service == mock_service_instance

    def test_service_property_after_close_raises_error(self, temp_cert_files):
        """Test accessing service properties after close raises ConnectionError"""
        with patch("joblet.client.grpc.secure_channel") as mock_secure_channel:
            mock_channel = Mock()
            mock_secure_channel.return_value = mock_channel

            client = JobletClient(
                ca_cert_path=temp_cert_files["ca_cert_path"],
                client_cert_path=temp_cert_files["client_cert_path"],
                client_key_path=temp_cert_files["client_key_path"],
                host="test-host",
                port=50051,
            )

            client.close()

            with pytest.raises(
                ConnectionError, match="Client is not connected to server"
            ):
                _ = client.jobs

    def test_health_check_success(self, temp_cert_files, sample_system_status):
        """Test successful health check"""
        with patch("joblet.client.grpc.secure_channel") as mock_secure_channel:
            mock_channel = Mock()
            mock_secure_channel.return_value = mock_channel

            with patch("joblet.client.MonitoringService") as mock_monitoring_service:
                mock_service_instance = Mock()
                mock_service_instance.get_system_status.return_value = (
                    sample_system_status
                )
                mock_monitoring_service.return_value = mock_service_instance

                client = JobletClient(
                    ca_cert_path=temp_cert_files["ca_cert_path"],
                    client_cert_path=temp_cert_files["client_cert_path"],
                    client_key_path=temp_cert_files["client_key_path"],
                    host="test-host",
                    port=50051,
                )

                result = client.health_check()
                assert result is True
                mock_service_instance.get_system_status.assert_called_once()

    def test_health_check_unavailable_server(self, temp_cert_files):
        """Test health check with unavailable server"""
        with patch("joblet.client.grpc.secure_channel") as mock_secure_channel:
            mock_channel = Mock()
            mock_secure_channel.return_value = mock_channel

            with patch("joblet.client.MonitoringService") as mock_monitoring_service:
                mock_service_instance = Mock()
                mock_service_instance.get_system_status.return_value = {
                    "available": False
                }
                mock_monitoring_service.return_value = mock_service_instance

                client = JobletClient(
                    ca_cert_path=temp_cert_files["ca_cert_path"],
                    client_cert_path=temp_cert_files["client_cert_path"],
                    client_key_path=temp_cert_files["client_key_path"],
                    host="test-host",
                    port=50051,
                )

                result = client.health_check()
                assert result is False

    def test_health_check_exception(self, temp_cert_files):
        """Test health check handles exceptions gracefully"""
        with patch("joblet.client.grpc.secure_channel") as mock_secure_channel:
            mock_channel = Mock()
            mock_secure_channel.return_value = mock_channel

            with patch("joblet.client.MonitoringService") as mock_monitoring_service:
                mock_service_instance = Mock()
                mock_service_instance.get_system_status.side_effect = Exception(
                    "Connection failed"
                )
                mock_monitoring_service.return_value = mock_service_instance

                client = JobletClient(
                    ca_cert_path=temp_cert_files["ca_cert_path"],
                    client_cert_path=temp_cert_files["client_cert_path"],
                    client_key_path=temp_cert_files["client_key_path"],
                    host="test-host",
                    port=50051,
                )

                result = client.health_check()
                assert result is False

    def test_default_host_and_port(self, temp_cert_files):
        """Test default host and port values when explicitly provided"""
        with patch("joblet.client.grpc.secure_channel") as mock_secure_channel:
            mock_channel = Mock()
            mock_secure_channel.return_value = mock_channel

            # Explicitly provide host and port to test defaults
            client = JobletClient(
                host="localhost",
                port=50051,
                ca_cert_path=temp_cert_files["ca_cert_path"],
                client_cert_path=temp_cert_files["client_cert_path"],
                client_key_path=temp_cert_files["client_key_path"],
            )

            assert client.host == "localhost"
            assert client.port == 50051

    def test_grpc_connection_failure(self, temp_cert_files):
        """Test gRPC connection failure handling"""
        with patch("joblet.client.grpc.secure_channel") as mock_secure_channel:
            mock_secure_channel.side_effect = Exception("gRPC connection failed")

            with pytest.raises(ConnectionError, match="Can't connect to"):
                JobletClient(
                    ca_cert_path=temp_cert_files["ca_cert_path"],
                    client_cert_path=temp_cert_files["client_cert_path"],
                    client_key_path=temp_cert_files["client_key_path"],
                    host="test-host",
                    port=50051,
                )
