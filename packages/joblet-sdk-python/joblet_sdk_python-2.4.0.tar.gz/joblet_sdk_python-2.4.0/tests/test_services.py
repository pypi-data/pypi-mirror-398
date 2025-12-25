"""
Unit tests for Network, Volume, Monitoring, and Runtime services
"""

from unittest.mock import Mock

import grpc
import pytest

from joblet.exceptions import NetworkError, RuntimeNotFoundError, VolumeError
from joblet.services import (
    MonitoringService,
    NetworkService,
    RuntimeService,
    VolumeService,
)


class TestNetworkService:
    """Test cases for NetworkService class"""

    @pytest.fixture
    def network_service(self, mock_grpc_channel):
        """Create NetworkService instance with mocked channel"""
        return NetworkService(mock_grpc_channel)

    def test_create_network_success(self, network_service):
        """Test creating a network successfully"""
        mock_stub = Mock()
        network_service.stub = mock_stub

        mock_grpc_response = Mock()
        mock_grpc_response.name = "test-network"
        mock_grpc_response.cidr = "10.0.1.0/24"
        mock_grpc_response.bridge = "br-test"

        mock_stub.CreateNetwork.return_value = mock_grpc_response

        result = network_service.create_network("test-network", "10.0.1.0/24")

        assert result["name"] == "test-network"
        assert result["cidr"] == "10.0.1.0/24"
        assert result["bridge"] == "br-test"

        mock_stub.CreateNetwork.assert_called_once()

    def test_create_network_grpc_error(self, network_service):
        """Test create_network handles gRPC errors"""
        mock_stub = Mock()
        network_service.stub = mock_stub

        grpc_error = grpc.RpcError()
        grpc_error.details = lambda: "Network creation failed"
        mock_stub.CreateNetwork.side_effect = grpc_error

        with pytest.raises(NetworkError, match="Failed to create network"):
            network_service.create_network("test-network", "10.0.1.0/24")

    def test_list_networks_success(self, network_service, sample_network_list):
        """Test listing networks successfully"""
        mock_stub = Mock()
        network_service.stub = mock_stub

        # Create mock networks
        mock_networks = []
        for net_data in sample_network_list:
            mock_network = Mock()
            mock_network.name = net_data["name"]
            mock_network.cidr = net_data["cidr"]
            mock_network.bridge = net_data["bridge"]
            mock_network.jobCount = net_data["job_count"]
            mock_networks.append(mock_network)

        mock_grpc_response = Mock()
        mock_grpc_response.networks = mock_networks

        mock_stub.ListNetworks.return_value = mock_grpc_response

        result = network_service.list_networks()

        assert len(result) == 2
        assert result[0]["name"] == "default"
        assert result[0]["cidr"] == "172.17.0.0/16"
        assert result[1]["name"] == "custom-network"
        assert result[1]["job_count"] == 2

    def test_remove_network_success(self, network_service):
        """Test removing a network successfully"""
        mock_stub = Mock()
        network_service.stub = mock_stub

        mock_grpc_response = Mock()
        mock_grpc_response.success = True
        mock_grpc_response.message = "Network removed successfully"

        mock_stub.RemoveNetwork.return_value = mock_grpc_response

        result = network_service.remove_network("test-network")

        assert result["success"] is True
        assert result["message"] == "Network removed successfully"


class TestVolumeService:
    """Test cases for VolumeService class"""

    @pytest.fixture
    def volume_service(self, mock_grpc_channel):
        """Create VolumeService instance with mocked channel"""
        return VolumeService(mock_grpc_channel)

    def test_create_volume_success(self, volume_service):
        """Test creating a volume successfully"""
        mock_stub = Mock()
        volume_service.stub = mock_stub

        mock_grpc_response = Mock()
        mock_grpc_response.name = "test-volume"
        mock_grpc_response.size = "5GB"
        mock_grpc_response.type = "filesystem"
        mock_grpc_response.path = "/var/joblet/volumes/test-volume"

        mock_stub.CreateVolume.return_value = mock_grpc_response

        result = volume_service.create_volume("test-volume", "5GB", "filesystem")

        assert result["name"] == "test-volume"
        assert result["size"] == "5GB"
        assert result["type"] == "filesystem"
        assert result["path"] == "/var/joblet/volumes/test-volume"

        mock_stub.CreateVolume.assert_called_once()

    def test_create_volume_default_type(self, volume_service):
        """Test creating a volume with default type"""
        mock_stub = Mock()
        volume_service.stub = mock_stub

        mock_grpc_response = Mock()
        mock_grpc_response.name = "test-volume"
        mock_grpc_response.size = "1GB"
        mock_grpc_response.type = "filesystem"
        mock_grpc_response.path = "/var/joblet/volumes/test-volume"

        mock_stub.CreateVolume.return_value = mock_grpc_response

        result = volume_service.create_volume("test-volume", "1GB")

        assert result["type"] == "filesystem"

        # Verify the request had default type
        call_args = mock_stub.CreateVolume.call_args[0][0]
        assert call_args.type == "filesystem"

    def test_create_volume_grpc_error(self, volume_service):
        """Test create_volume handles gRPC errors"""
        mock_stub = Mock()
        volume_service.stub = mock_stub

        grpc_error = grpc.RpcError()
        grpc_error.details = lambda: "Volume creation failed"
        mock_stub.CreateVolume.side_effect = grpc_error

        with pytest.raises(VolumeError, match="Failed to create volume"):
            volume_service.create_volume("test-volume", "1GB")

    def test_list_volumes_success(self, volume_service, sample_volume_list):
        """Test listing volumes successfully"""
        mock_stub = Mock()
        volume_service.stub = mock_stub

        # Create mock volumes
        mock_volumes = []
        for vol_data in sample_volume_list:
            mock_volume = Mock()
            mock_volume.name = vol_data["name"]
            mock_volume.size = vol_data["size"]
            mock_volume.type = vol_data["type"]
            mock_volume.path = vol_data["path"]
            mock_volume.createdTime = vol_data["created_time"]
            mock_volume.jobCount = vol_data["job_count"]
            mock_volumes.append(mock_volume)

        mock_grpc_response = Mock()
        mock_grpc_response.volumes = mock_volumes

        mock_stub.ListVolumes.return_value = mock_grpc_response

        result = volume_service.list_volumes()

        assert len(result) == 2
        assert result[0]["name"] == "data-volume"
        assert result[0]["size"] == "10GB"
        assert result[0]["type"] == "filesystem"
        assert result[1]["name"] == "temp-volume"
        assert result[1]["type"] == "memory"

    def test_remove_volume_success(self, volume_service):
        """Test removing a volume successfully"""
        mock_stub = Mock()
        volume_service.stub = mock_stub

        mock_grpc_response = Mock()
        mock_grpc_response.success = True
        mock_grpc_response.message = "Volume removed successfully"

        mock_stub.RemoveVolume.return_value = mock_grpc_response

        result = volume_service.remove_volume("test-volume")

        assert result["success"] is True
        assert result["message"] == "Volume removed successfully"


class TestMonitoringService:
    """Test cases for MonitoringService class"""

    @pytest.fixture
    def monitoring_service(self, mock_grpc_channel):
        """Create MonitoringService instance with mocked channel"""
        return MonitoringService(mock_grpc_channel)

    def test_get_system_status_success(self, monitoring_service, sample_system_status):
        """Test getting system status successfully"""
        mock_stub = Mock()
        monitoring_service.stub = mock_stub

        # Create mock gRPC response
        mock_grpc_response = Mock()
        mock_grpc_response.timestamp = sample_system_status["timestamp"]
        mock_grpc_response.available = sample_system_status["available"]

        # Mock host info
        mock_host = Mock()
        mock_host.hostname = sample_system_status["host"]["hostname"]
        mock_host.os = sample_system_status["host"]["os"]
        mock_host.platform = sample_system_status["host"]["platform"]
        mock_host.platformFamily = ""
        mock_host.platformVersion = sample_system_status["host"]["platform_version"]
        mock_host.kernelVersion = ""
        mock_host.kernelArch = ""
        mock_host.architecture = ""
        mock_host.cpuCount = sample_system_status["host"]["cpu_count"]
        mock_host.totalMemory = sample_system_status["host"]["total_memory"]
        mock_host.bootTime = ""
        mock_host.uptime = 0
        mock_host.nodeId = "test-node-123"
        mock_host.serverIPs = ["192.168.1.100", "10.0.0.1"]
        mock_host.macAddresses = ["00:1B:63:84:45:E6", "02:42:ac:11:00:02"]

        mock_grpc_response.HasField = lambda field: field in ["host", "cpu", "memory"]
        mock_grpc_response.host = mock_host

        # Mock CPU info
        mock_cpu = Mock()
        mock_cpu.cores = sample_system_status["cpu"]["cores"]
        mock_cpu.usagePercent = sample_system_status["cpu"]["usage_percent"]
        mock_cpu.userTime = 0
        mock_cpu.systemTime = 0
        mock_cpu.idleTime = 0
        mock_cpu.ioWaitTime = 0
        mock_cpu.stealTime = 0
        mock_cpu.loadAverage = sample_system_status["cpu"]["load_average"]
        mock_cpu.perCoreUsage = []

        mock_grpc_response.cpu = mock_cpu

        # Mock memory info
        mock_memory = Mock()
        mock_memory.totalBytes = sample_system_status["memory"]["total_bytes"]
        mock_memory.usedBytes = sample_system_status["memory"]["used_bytes"]
        mock_memory.freeBytes = 0
        mock_memory.availableBytes = 0
        mock_memory.usagePercent = sample_system_status["memory"]["usage_percent"]
        mock_memory.cachedBytes = 0
        mock_memory.bufferedBytes = 0
        mock_memory.swapTotal = 0
        mock_memory.swapUsed = 0
        mock_memory.swapFree = 0

        mock_grpc_response.memory = mock_memory
        mock_grpc_response.disks = []
        mock_grpc_response.networks = []

        mock_stub.GetSystemStatus.return_value = mock_grpc_response

        result = monitoring_service.get_system_status()

        assert result["timestamp"] == sample_system_status["timestamp"]
        assert result["available"] == sample_system_status["available"]
        assert result["host"]["hostname"] == sample_system_status["host"]["hostname"]
        assert result["cpu"]["cores"] == sample_system_status["cpu"]["cores"]
        assert (
            result["memory"]["total_bytes"]
            == sample_system_status["memory"]["total_bytes"]
        )

    def test_stream_system_metrics(self, monitoring_service):
        """Test streaming system metrics"""
        mock_stub = Mock()
        monitoring_service.stub = mock_stub

        # Create mock metric chunks
        metric_chunks = []
        for i in range(3):
            mock_metric = Mock()
            mock_metric.timestamp = f"2023-01-01T12:0{i}:00Z"
            mock_metric.HasField = lambda field: field == "cpu"

            mock_cpu = Mock()
            mock_cpu.cores = 4
            mock_cpu.usagePercent = 20.0 + i * 5
            mock_cpu.userTime = 0
            mock_cpu.systemTime = 0
            mock_cpu.idleTime = 0
            mock_cpu.ioWaitTime = 0
            mock_cpu.stealTime = 0
            mock_cpu.loadAverage = [1.0, 1.0, 1.0]
            mock_cpu.perCoreUsage = []

            mock_metric.cpu = mock_cpu
            mock_metric.disks = []
            mock_metric.networks = []
            metric_chunks.append(mock_metric)

        mock_stub.StreamSystemMetrics.return_value = iter(metric_chunks)

        metrics = list(monitoring_service.stream_system_metrics(interval_seconds=1))

        assert len(metrics) == 3
        assert metrics[0]["cpu"]["usage_percent"] == 20.0
        assert metrics[1]["cpu"]["usage_percent"] == 25.0
        assert metrics[2]["cpu"]["usage_percent"] == 30.0

        # Verify the request
        mock_stub.StreamSystemMetrics.assert_called_once()
        call_args = mock_stub.StreamSystemMetrics.call_args[0][0]
        assert call_args.intervalSeconds == 1


class TestRuntimeService:
    """Test cases for RuntimeService class"""

    @pytest.fixture
    def runtime_service(self, mock_grpc_channel):
        """Create RuntimeService instance with mocked channel"""
        return RuntimeService(mock_grpc_channel)

    def test_list_runtimes_success(self, runtime_service, sample_runtime_list):
        """Test listing runtimes successfully"""
        mock_stub = Mock()
        runtime_service.stub = mock_stub

        # Create mock runtimes
        mock_runtimes = []
        for runtime_data in sample_runtime_list:
            mock_runtime = Mock()
            mock_runtime.name = runtime_data["name"]
            mock_runtime.language = runtime_data["language"]
            mock_runtime.version = runtime_data["version"]
            mock_runtime.description = runtime_data["description"]
            mock_runtime.sizeBytes = runtime_data["size_bytes"]
            mock_runtime.packages = runtime_data["packages"]
            mock_runtime.available = runtime_data["available"]

            # Mock requirements
            mock_requirements = Mock()
            mock_requirements.architectures = runtime_data["requirements"][
                "architectures"
            ]
            mock_requirements.gpu = runtime_data["requirements"]["gpu"]

            mock_runtime.HasField = lambda field: field == "requirements"
            mock_runtime.requirements = mock_requirements

            mock_runtimes.append(mock_runtime)

        mock_grpc_response = Mock()
        mock_grpc_response.runtimes = mock_runtimes

        mock_stub.ListRuntimes.return_value = mock_grpc_response

        result = runtime_service.list_runtimes()

        assert len(result) == 2
        assert result[0]["name"] == "python:3.11"
        assert result[0]["language"] == "python"
        assert result[0]["available"] is True
        assert result[0]["requirements"]["architectures"] == ["amd64", "arm64"]
        assert result[1]["name"] == "node:18"
        assert result[1]["language"] == "javascript"

    def test_get_runtime_info_success(self, runtime_service):
        """Test getting runtime info successfully"""
        mock_stub = Mock()
        runtime_service.stub = mock_stub

        mock_runtime = Mock()
        mock_runtime.name = "python:3.11"
        mock_runtime.language = "python"
        mock_runtime.version = "3.11.0"
        mock_runtime.description = "Python 3.11 runtime"
        mock_runtime.sizeBytes = 1073741824
        mock_runtime.packages = ["pip", "setuptools"]
        mock_runtime.available = True

        mock_requirements = Mock()
        mock_requirements.architectures = ["amd64"]
        mock_requirements.gpu = False

        mock_runtime.HasField = lambda field: field == "requirements"
        mock_runtime.requirements = mock_requirements

        mock_grpc_response = Mock()
        mock_grpc_response.found = True
        mock_grpc_response.runtime = mock_runtime

        mock_stub.GetRuntimeInfo.return_value = mock_grpc_response

        result = runtime_service.get_runtime_info("python:3.11")

        assert result["name"] == "python:3.11"
        assert result["language"] == "python"
        assert result["available"] is True
        assert result["requirements"]["architectures"] == ["amd64"]

    def test_get_runtime_info_not_found(self, runtime_service):
        """Test getting runtime info for non-existent runtime"""
        mock_stub = Mock()
        runtime_service.stub = mock_stub

        mock_grpc_response = Mock()
        mock_grpc_response.found = False

        mock_stub.GetRuntimeInfo.return_value = mock_grpc_response

        with pytest.raises(RuntimeNotFoundError, match="Runtime nonexistent not found"):
            runtime_service.get_runtime_info("nonexistent")

    def test_test_runtime_success(self, runtime_service):
        """Test testing a runtime successfully"""
        mock_stub = Mock()
        runtime_service.stub = mock_stub

        mock_grpc_response = Mock()
        mock_grpc_response.success = True
        mock_grpc_response.output = "Python 3.11.0"
        mock_grpc_response.error = ""
        mock_grpc_response.exitCode = 0

        mock_stub.TestRuntime.return_value = mock_grpc_response

        result = runtime_service.test_runtime("python:3.11")

        assert result["success"] is True
        assert result["output"] == "Python 3.11.0"
        assert result["error"] == ""
        assert result["exit_code"] == 0

    def test_test_runtime_failure(self, runtime_service):
        """Test testing a runtime that fails"""
        mock_stub = Mock()
        runtime_service.stub = mock_stub

        mock_grpc_response = Mock()
        mock_grpc_response.success = False
        mock_grpc_response.output = ""
        mock_grpc_response.error = "Runtime not available"
        mock_grpc_response.exitCode = 1

        mock_stub.TestRuntime.return_value = mock_grpc_response

        result = runtime_service.test_runtime("invalid:runtime")

        assert result["success"] is False
        assert result["error"] == "Runtime not available"
        assert result["exit_code"] == 1

    def test_remove_runtime_success(self, runtime_service):
        """Test removing a runtime successfully"""
        mock_stub = Mock()
        runtime_service.stub = mock_stub

        mock_grpc_response = Mock()
        mock_grpc_response.success = True
        mock_grpc_response.message = "Runtime removed successfully"
        mock_grpc_response.freedSpaceBytes = 1073741824  # 1GB

        mock_stub.RemoveRuntime.return_value = mock_grpc_response

        result = runtime_service.remove_runtime("python:3.11")

        assert result["success"] is True
        assert result["message"] == "Runtime removed successfully"
        assert result["freed_space_bytes"] == 1073741824
