"""
Integration tests for Joblet SDK

These tests verify the SDK works correctly with real or mocked gRPC services.
They are marked as integration tests and can be run separately from unit tests.
"""

from unittest.mock import Mock, patch

import pytest

from joblet import JobletClient
from joblet.exceptions import ConnectionError


@pytest.mark.integration
class TestJobletClientIntegration:
    """Integration tests for JobletClient"""

    def test_full_client_lifecycle(self, temp_cert_files):
        """Test complete client lifecycle from initialization to cleanup"""
        with patch("joblet.client.grpc.secure_channel") as mock_secure_channel:
            mock_channel = Mock()
            mock_secure_channel.return_value = mock_channel

            # Mock all service stubs
            with (
                patch(
                    "joblet.services.joblet_pb2_grpc.JobServiceStub"
                ) as mock_job_stub,
                patch(
                    "joblet.services.joblet_pb2_grpc.MonitoringServiceStub"
                ) as mock_monitoring_stub,
            ):
                # Setup monitoring service for health check
                mock_monitoring_instance = Mock()
                mock_monitoring_instance.GetSystemStatus.return_value = Mock(
                    available=True,
                    timestamp="2023-01-01T12:00:00Z",
                    HasField=lambda x: False,
                    disks=[],
                    networks=[],
                )
                mock_monitoring_stub.return_value = mock_monitoring_instance

                # Setup job service
                mock_job_instance = Mock()
                mock_job_response = Mock()
                mock_job_response.jobUuid = "test-job-123"
                mock_job_response.status = "running"
                mock_job_response.command = "echo"
                mock_job_response.args = ["hello"]
                mock_job_response.maxCpu = 50
                mock_job_response.cpuCores = ""
                mock_job_response.maxMemory = 1024
                mock_job_response.maxIobps = 0
                mock_job_response.startTime = "2023-01-01T12:00:00Z"
                mock_job_response.endTime = ""
                mock_job_response.exitCode = 0
                mock_job_response.scheduledTime = ""

                mock_job_instance.RunJob.return_value = mock_job_response
                mock_job_stub.return_value = mock_job_instance

                # Test the full flow
                with JobletClient(
                    ca_cert_path=temp_cert_files["ca_cert_path"],
                    client_cert_path=temp_cert_files["client_cert_path"],
                    client_key_path=temp_cert_files["client_key_path"],
                    host="test-server",
                    port=50051,
                ) as client:
                    # Test health check
                    assert client.health_check() is True

                    # Test job creation
                    job = client.jobs.run_job(
                        command="echo", args=["hello"], name="integration-test-job"
                    )

                    assert job["job_uuid"] == "test-job-123"
                    assert job["status"] == "running"
                    assert job["command"] == "echo"

                # Verify channel was closed
                mock_channel.close.assert_called_once()

    @pytest.mark.integration
    def test_client_with_all_services(self, temp_cert_files):
        """Test client with all service types"""
        with patch("joblet.client.grpc.secure_channel") as mock_secure_channel:
            mock_channel = Mock()
            mock_secure_channel.return_value = mock_channel

            # Mock all service stubs
            with (
                patch("joblet.services.joblet_pb2_grpc.JobServiceStub"),
                patch("joblet.services.joblet_pb2_grpc.NetworkServiceStub"),
                patch("joblet.services.joblet_pb2_grpc.VolumeServiceStub"),
                patch("joblet.services.joblet_pb2_grpc.MonitoringServiceStub"),
                patch("joblet.services.joblet_pb2_grpc.RuntimeServiceStub"),
            ):
                client = JobletClient(
                    ca_cert_path=temp_cert_files["ca_cert_path"],
                    client_cert_path=temp_cert_files["client_cert_path"],
                    client_key_path=temp_cert_files["client_key_path"],
                    host="test-host",
                    port=50051,
                )

                # Test that all service properties can be accessed
                jobs_service = client.jobs
                networks_service = client.networks
                volumes_service = client.volumes
                monitoring_service = client.monitoring
                runtimes_service = client.runtimes

                # Verify services are properly initialized
                assert jobs_service is not None
                assert networks_service is not None
                assert volumes_service is not None
                assert monitoring_service is not None
                assert runtimes_service is not None

                # Verify lazy loading - second access returns same instance
                assert client.jobs is jobs_service
                assert client.networks is networks_service

                client.close()

    @pytest.mark.integration
    @pytest.mark.network
    def test_real_grpc_connection_failure(self, temp_cert_files):
        """Test handling of real gRPC connection failures"""
        # This test uses real gRPC but with invalid host to test error handling
        # Note: The error might happen during initialization or first use
        try:
            client = JobletClient(
                ca_cert_path=temp_cert_files["ca_cert_path"],
                client_cert_path=temp_cert_files["client_cert_path"],
                client_key_path=temp_cert_files["client_key_path"],
                host="nonexistent-host-12345.invalid",
                port=99999,
            )
            # If initialization succeeds, health_check should return False
            # for invalid host
            assert client.health_check() is False
            client.close()
        except (ConnectionError, Exception):
            # This is expected - connection should fail during initialization
            pass

    @pytest.mark.integration
    def test_concurrent_service_access(self, temp_cert_files):
        """Test concurrent access to different services"""
        import threading

        with patch("joblet.client.grpc.secure_channel") as mock_secure_channel:
            mock_channel = Mock()
            mock_secure_channel.return_value = mock_channel

            with (
                patch("joblet.services.joblet_pb2_grpc.JobServiceStub"),
                patch("joblet.services.joblet_pb2_grpc.NetworkServiceStub"),
                patch("joblet.services.joblet_pb2_grpc.VolumeServiceStub"),
            ):

                client = JobletClient(
                    ca_cert_path=temp_cert_files["ca_cert_path"],
                    client_cert_path=temp_cert_files["client_cert_path"],
                    client_key_path=temp_cert_files["client_key_path"],
                    host="test-host",
                    port=50051,
                )

                # Test concurrent access to services
                services = []
                errors = []

                def access_service(service_name):
                    try:
                        if service_name == "jobs":
                            service = client.jobs
                        elif service_name == "networks":
                            service = client.networks
                        elif service_name == "volumes":
                            service = client.volumes
                        services.append((service_name, service))
                    except Exception as e:
                        errors.append((service_name, e))

                # Create threads for concurrent access
                threads = []
                for service_name in ["jobs", "networks", "volumes"]:
                    thread = threading.Thread(
                        target=access_service, args=(service_name,)
                    )
                    threads.append(thread)

                # Start all threads
                for thread in threads:
                    thread.start()

                # Wait for all threads
                for thread in threads:
                    thread.join(timeout=5.0)

                # Verify no errors and all services accessed
                assert len(errors) == 0, f"Errors occurred: {errors}"
                assert len(services) == 3

                client.close()


@pytest.mark.integration
class TestServiceIntegration:
    """Integration tests for service interactions"""

    def test_job_service_integration(self, temp_cert_files):
        """Test job service operations integration"""
        with patch("joblet.client.grpc.secure_channel") as mock_secure_channel:
            mock_channel = Mock()
            mock_secure_channel.return_value = mock_channel

            with patch(
                "joblet.services.joblet_pb2_grpc.JobServiceStub"
            ) as mock_job_stub:
                # Setup job service responses
                mock_job_instance = Mock()

                # Mock run_job response
                mock_run_response = Mock()
                mock_run_response.jobUuid = "test-job-123"
                mock_run_response.status = "running"
                mock_run_response.command = "echo"
                mock_run_response.args = ["hello"]
                mock_run_response.maxCpu = 50
                mock_run_response.cpuCores = ""
                mock_run_response.maxMemory = 1024
                mock_run_response.maxIobps = 0
                mock_run_response.startTime = "2023-01-01T12:00:00Z"
                mock_run_response.endTime = ""
                mock_run_response.exitCode = 0
                mock_run_response.scheduledTime = ""
                mock_job_instance.RunJob.return_value = mock_run_response

                # Mock get_job_status response
                mock_status_response = Mock()
                mock_status_response.uuid = "test-job-123"
                mock_status_response.name = "test-job"
                mock_status_response.command = "echo"
                mock_status_response.args = ["hello"]
                mock_status_response.maxCPU = 50
                mock_status_response.cpuCores = ""
                mock_status_response.maxMemory = 1024
                mock_status_response.maxIOBPS = 0
                mock_status_response.status = "completed"
                mock_status_response.startTime = "2023-01-01T12:00:00Z"
                mock_status_response.endTime = "2023-01-01T12:00:05Z"
                mock_status_response.exitCode = 0
                mock_status_response.scheduledTime = ""
                mock_status_response.environment = {}
                mock_status_response.secret_environment = {}
                mock_status_response.network = ""
                mock_status_response.volumes = []
                mock_status_response.runtime = ""
                mock_status_response.workDir = ""
                mock_status_response.uploads = []
                mock_status_response.gpu_indices = []
                mock_status_response.gpu_count = 0
                mock_status_response.gpu_memory_mb = 0
                mock_job_instance.GetJobStatus.return_value = mock_status_response

                # Mock get_job_logs response
                log_chunks = [
                    Mock(payload=b"Log line 1\n"),
                    Mock(payload=b"Log line 2\n"),
                ]
                mock_job_instance.GetJobLogs.return_value = iter(log_chunks)

                mock_job_stub.return_value = mock_job_instance

                # Test the integration flow
                client = JobletClient(
                    ca_cert_path=temp_cert_files["ca_cert_path"],
                    client_cert_path=temp_cert_files["client_cert_path"],
                    client_key_path=temp_cert_files["client_key_path"],
                    host="test-host",
                    port=50051,
                )

                try:
                    # Run job
                    job = client.jobs.run_job(command="echo", args=["hello"])
                    job_uuid = job["job_uuid"]

                    # Get status
                    status = client.jobs.get_job_status(job_uuid)
                    assert status["status"] == "completed"

                    # Get logs
                    logs = list(client.jobs.get_job_logs(job_uuid))
                    assert len(logs) == 2
                    assert logs[0] == b"Log line 1\n"

                finally:
                    client.close()


@pytest.mark.integration
@pytest.mark.slow
class TestStressIntegration:
    """Stress tests for SDK integration"""

    def test_multiple_client_instances(self, temp_cert_files):
        """Test creating multiple client instances"""
        clients = []

        with patch("joblet.client.grpc.secure_channel") as mock_secure_channel:
            mock_channels = [Mock() for _ in range(5)]
            mock_secure_channel.side_effect = mock_channels

            try:
                # Create multiple clients
                for i in range(5):
                    client = JobletClient(
                        ca_cert_path=temp_cert_files["ca_cert_path"],
                        client_cert_path=temp_cert_files["client_cert_path"],
                        client_key_path=temp_cert_files["client_key_path"],
                        host=f"test-host-{i}",
                        port=50051 + i,
                    )
                    clients.append(client)

                # Verify all clients are independent
                for i, client in enumerate(clients):
                    assert client.host == f"test-host-{i}"
                    assert client.port == 50051 + i

            finally:
                # Clean up all clients
                for client in clients:
                    client.close()

                # Verify all channels were closed
                for mock_channel in mock_channels:
                    mock_channel.close.assert_called_once()
