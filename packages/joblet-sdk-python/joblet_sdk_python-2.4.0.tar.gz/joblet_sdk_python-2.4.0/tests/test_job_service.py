"""
Unit tests for JobService
"""

from unittest.mock import Mock

import grpc
import pytest

from joblet.exceptions import JobNotFoundError
from joblet.services import JobService


class TestJobService:
    """Test cases for JobService class"""

    @pytest.fixture
    def job_service(self, mock_grpc_channel):
        """Create JobService instance with mocked channel"""
        return JobService(mock_grpc_channel)

    def test_run_job_minimal(self, job_service, sample_job_response):
        """Test running a job with minimal parameters"""
        # Mock the gRPC stub
        mock_stub = Mock()
        job_service.stub = mock_stub

        # Create mock response
        mock_grpc_response = Mock()
        mock_grpc_response.jobUuid = sample_job_response["job_uuid"]
        mock_grpc_response.status = sample_job_response["status"]
        mock_grpc_response.command = sample_job_response["command"]
        mock_grpc_response.args = sample_job_response["args"]
        mock_grpc_response.maxCpu = sample_job_response["max_cpu"]
        mock_grpc_response.cpuCores = sample_job_response["cpu_cores"]
        mock_grpc_response.maxMemory = sample_job_response["max_memory"]
        mock_grpc_response.maxIobps = sample_job_response["max_iobps"]
        mock_grpc_response.startTime = sample_job_response["start_time"]
        mock_grpc_response.endTime = sample_job_response["end_time"]
        mock_grpc_response.exitCode = sample_job_response["exit_code"]
        mock_grpc_response.scheduledTime = sample_job_response["scheduled_time"]

        mock_stub.RunJob.return_value = mock_grpc_response

        # Run the job
        result = job_service.run_job(command="echo", args=["hello", "world"])

        # Verify the result
        assert result["job_uuid"] == sample_job_response["job_uuid"]
        assert result["status"] == sample_job_response["status"]
        assert result["command"] == sample_job_response["command"]
        assert result["args"] == sample_job_response["args"]

        # Verify the stub was called correctly
        mock_stub.RunJob.assert_called_once()
        call_args = mock_stub.RunJob.call_args[0][0]
        assert call_args.command == "echo"
        assert list(call_args.args) == ["hello", "world"]

    def test_run_job_full_parameters(self, job_service, sample_job_response):
        """Test running a job with all parameters"""
        mock_stub = Mock()
        job_service.stub = mock_stub

        # Create mock response
        mock_grpc_response = Mock()
        mock_grpc_response.jobUuid = sample_job_response["job_uuid"]
        mock_grpc_response.status = sample_job_response["status"]
        mock_grpc_response.command = "python"
        mock_grpc_response.args = ["script.py"]
        mock_grpc_response.maxCpu = 80
        mock_grpc_response.cpuCores = "2"
        mock_grpc_response.maxMemory = 2048
        mock_grpc_response.maxIobps = 1000
        mock_grpc_response.startTime = sample_job_response["start_time"]
        mock_grpc_response.endTime = sample_job_response["end_time"]
        mock_grpc_response.exitCode = sample_job_response["exit_code"]
        mock_grpc_response.scheduledTime = sample_job_response["scheduled_time"]

        mock_stub.RunJob.return_value = mock_grpc_response

        # Run the job with full parameters
        result = job_service.run_job(
            command="python",
            args=["script.py"],
            name="test-job",
            max_cpu=80,
            cpu_cores="2",
            max_memory=2048,
            max_iobps=1000,
            schedule="2023-12-31T23:59:59Z",
            network="test-network",
            volumes=["vol1:/data", "vol2:/logs"],
            runtime="python:3.11",
            work_dir="/app",
            environment={"ENV": "test", "DEBUG": "true"},
            secret_environment={"API_KEY": "secret"},
            uploads=[
                {
                    "path": "script.py",
                    "content": b"print('hello')",
                    "mode": 0o755,
                    "is_directory": False,
                }
            ],
        )

        # Verify the result
        assert result["job_uuid"] == sample_job_response["job_uuid"]
        assert result["command"] == "python"
        assert result["args"] == ["script.py"]

        # Verify the stub was called correctly
        mock_stub.RunJob.assert_called_once()
        call_args = mock_stub.RunJob.call_args[0][0]
        assert call_args.command == "python"
        assert list(call_args.args) == ["script.py"]
        assert call_args.name == "test-job"
        assert call_args.maxCpu == 80
        assert call_args.cpuCores == "2"
        assert call_args.maxMemory == 2048
        assert call_args.maxIobps == 1000
        assert call_args.network == "test-network"
        assert list(call_args.volumes) == ["vol1:/data", "vol2:/logs"]
        assert call_args.runtime == "python:3.11"
        assert call_args.workDir == "/app"
        assert dict(call_args.environment) == {"ENV": "test", "DEBUG": "true"}
        assert dict(call_args.secret_environment) == {"API_KEY": "secret"}
        assert len(call_args.uploads) == 1
        assert call_args.uploads[0].path == "script.py"

    def test_run_job_grpc_error(self, job_service):
        """Test run_job handles gRPC errors"""
        mock_stub = Mock()
        job_service.stub = mock_stub

        # Mock gRPC error
        grpc_error = grpc.RpcError()
        grpc_error.details = lambda: "Job execution failed"
        mock_stub.RunJob.side_effect = grpc_error

        with pytest.raises(JobNotFoundError, match="Failed to run job"):
            job_service.run_job(command="echo", args=["hello"])

    def test_get_job_status_success(self, job_service):
        """Test getting job status successfully"""
        mock_stub = Mock()
        job_service.stub = mock_stub

        # Create mock response
        mock_grpc_response = Mock()
        mock_grpc_response.uuid = "test-job-123"
        mock_grpc_response.name = "test-job"
        mock_grpc_response.command = "echo"
        mock_grpc_response.args = ["hello"]
        mock_grpc_response.maxCPU = 50
        mock_grpc_response.cpuCores = ""
        mock_grpc_response.maxMemory = 1024
        mock_grpc_response.maxIOBPS = 0
        mock_grpc_response.status = "completed"
        mock_grpc_response.startTime = "2023-01-01T12:00:00Z"
        mock_grpc_response.endTime = "2023-01-01T12:00:05Z"
        mock_grpc_response.exitCode = 0
        mock_grpc_response.scheduledTime = ""
        mock_grpc_response.environment = {"ENV": "test"}
        mock_grpc_response.secret_environment = {}
        mock_grpc_response.network = ""
        mock_grpc_response.volumes = []
        mock_grpc_response.runtime = "python:3.11"
        mock_grpc_response.workDir = "/app"
        mock_grpc_response.uploads = []
        mock_grpc_response.gpu_indices = [0, 1]
        mock_grpc_response.gpu_count = 2
        mock_grpc_response.gpu_memory_mb = 8192

        mock_stub.GetJobStatus.return_value = mock_grpc_response

        result = job_service.get_job_status("test-job-123")

        assert result["uuid"] == "test-job-123"
        assert result["name"] == "test-job"
        assert result["command"] == "echo"
        assert result["args"] == ["hello"]
        assert result["status"] == "completed"
        assert result["exit_code"] == 0
        assert result["gpu_indices"] == [0, 1]
        assert result["gpu_count"] == 2
        assert result["gpu_memory_mb"] == 8192

        mock_stub.GetJobStatus.assert_called_once()

    def test_get_job_status_not_found(self, job_service):
        """Test getting status for non-existent job"""
        mock_stub = Mock()
        job_service.stub = mock_stub

        grpc_error = grpc.RpcError()
        grpc_error.details = lambda: "Job not found"
        mock_stub.GetJobStatus.side_effect = grpc_error

        with pytest.raises(JobNotFoundError, match="Job test-job-123 not found"):
            job_service.get_job_status("test-job-123")

    def test_stop_job_success(self, job_service):
        """Test stopping a job successfully"""
        mock_stub = Mock()
        job_service.stub = mock_stub

        mock_grpc_response = Mock()
        mock_grpc_response.uuid = "test-job-123"
        mock_grpc_response.status = "cancelled"
        mock_grpc_response.endTime = "2023-01-01T12:00:05Z"
        mock_grpc_response.exitCode = 130

        mock_stub.StopJob.return_value = mock_grpc_response

        result = job_service.stop_job("test-job-123")

        assert result["uuid"] == "test-job-123"
        assert result["status"] == "cancelled"
        assert result["exit_code"] == 130

        mock_stub.StopJob.assert_called_once()

    def test_cancel_job_success(self, job_service):
        """Test canceling a scheduled job successfully"""
        mock_stub = Mock()
        job_service.stub = mock_stub

        mock_grpc_response = Mock()
        mock_grpc_response.uuid = "test-scheduled-job-123"
        mock_grpc_response.status = "CANCELED"

        mock_stub.CancelJob.return_value = mock_grpc_response

        result = job_service.cancel_job("test-scheduled-job-123")

        assert result["uuid"] == "test-scheduled-job-123"
        assert result["status"] == "CANCELED"

        mock_stub.CancelJob.assert_called_once()

    def test_cancel_job_not_found(self, job_service):
        """Test canceling a job that doesn't exist"""
        mock_stub = Mock()
        job_service.stub = mock_stub

        # Simulate gRPC error for job not found
        grpc_error = grpc.RpcError()
        grpc_error.details = lambda: "Job not found"
        mock_stub.CancelJob.side_effect = grpc_error

        with pytest.raises(JobNotFoundError) as exc_info:
            job_service.cancel_job("non-existent-job")

        assert "Failed to cancel job" in str(exc_info.value)

    def test_delete_job_success(self, job_service):
        """Test deleting a job successfully"""
        mock_stub = Mock()
        job_service.stub = mock_stub

        mock_grpc_response = Mock()
        mock_grpc_response.uuid = "test-job-123"
        mock_grpc_response.success = True
        mock_grpc_response.message = "Job deleted successfully"

        mock_stub.DeleteJob.return_value = mock_grpc_response

        result = job_service.delete_job("test-job-123")

        assert result["uuid"] == "test-job-123"
        assert result["success"] is True
        assert result["message"] == "Job deleted successfully"

    def test_delete_all_jobs_success(self, job_service):
        """Test deleting all jobs successfully"""
        mock_stub = Mock()
        job_service.stub = mock_stub

        mock_grpc_response = Mock()
        mock_grpc_response.success = True
        mock_grpc_response.message = "All jobs deleted"
        mock_grpc_response.deleted_count = 5
        mock_grpc_response.skipped_count = 2

        mock_stub.DeleteAllJobs.return_value = mock_grpc_response

        result = job_service.delete_all_jobs()

        assert result["success"] is True
        assert result["message"] == "All jobs deleted"
        assert result["deleted_count"] == 5
        assert result["skipped_count"] == 2

    def test_get_job_logs(self, job_service):
        """Test getting job logs"""
        mock_stub = Mock()
        job_service.stub = mock_stub

        # Mock log chunks
        log_chunks = [
            Mock(payload=b"Log line 1\n"),
            Mock(payload=b"Log line 2\n"),
            Mock(payload=b"Log line 3\n"),
        ]

        mock_stub.GetJobLogs.return_value = iter(log_chunks)

        logs = list(job_service.get_job_logs("test-job-123"))

        assert len(logs) == 3
        assert logs[0] == b"Log line 1\n"
        assert logs[1] == b"Log line 2\n"
        assert logs[2] == b"Log line 3\n"

    def test_list_jobs_success(self, job_service):
        """Test listing jobs successfully"""
        mock_stub = Mock()
        job_service.stub = mock_stub

        # Create mock jobs
        mock_job1 = Mock()
        mock_job1.uuid = "job-1"
        mock_job1.name = "test-job-1"
        mock_job1.command = "echo"
        mock_job1.args = ["hello"]
        mock_job1.maxCPU = 50
        mock_job1.cpuCores = ""
        mock_job1.maxMemory = 1024
        mock_job1.maxIOBPS = 0
        mock_job1.status = "completed"
        mock_job1.startTime = "2023-01-01T12:00:00Z"
        mock_job1.endTime = "2023-01-01T12:00:05Z"
        mock_job1.exitCode = 0
        mock_job1.scheduledTime = ""
        mock_job1.runtime = "python:3.11"
        mock_job1.environment = {}
        mock_job1.secret_environment = {}
        mock_job1.gpu_indices = []
        mock_job1.gpu_count = 0
        mock_job1.gpu_memory_mb = 0
        mock_job1.nodeId = "node-1"

        mock_job2 = Mock()
        mock_job2.uuid = "job-2"
        mock_job2.name = "test-job-2"
        mock_job2.command = "python"
        mock_job2.args = ["script.py"]
        mock_job2.maxCPU = 80
        mock_job2.cpuCores = "2"
        mock_job2.maxMemory = 2048
        mock_job2.maxIOBPS = 1000
        mock_job2.status = "running"
        mock_job2.startTime = "2023-01-01T12:05:00Z"
        mock_job2.endTime = ""
        mock_job2.exitCode = 0
        mock_job2.scheduledTime = ""
        mock_job2.runtime = "python:3.11"
        mock_job2.environment = {"ENV": "test"}
        mock_job2.secret_environment = {}
        mock_job2.gpu_indices = []
        mock_job2.gpu_count = 0
        mock_job2.gpu_memory_mb = 0
        mock_job2.nodeId = "node-2"

        mock_grpc_response = Mock()
        mock_grpc_response.jobs = [mock_job1, mock_job2]
        mock_stub.ListJobs.return_value = mock_grpc_response

        result = job_service.list_jobs()

        assert len(result) == 2
        assert result[0]["uuid"] == "job-1"
        assert result[0]["name"] == "test-job-1"
        assert result[0]["status"] == "completed"
        assert result[1]["uuid"] == "job-2"
        assert result[1]["name"] == "test-job-2"
        assert result[1]["status"] == "running"

    def test_run_job_with_gpu(self, job_service, sample_job_response):
        """Test running a job with GPU parameters"""
        mock_stub = Mock()
        job_service.stub = mock_stub

        # Create mock response with GPU fields
        mock_grpc_response = Mock()
        mock_grpc_response.jobUuid = sample_job_response["job_uuid"]
        mock_grpc_response.status = sample_job_response["status"]
        mock_grpc_response.command = "python"
        mock_grpc_response.args = ["train.py"]
        mock_grpc_response.maxCpu = sample_job_response["max_cpu"]
        mock_grpc_response.cpuCores = sample_job_response["cpu_cores"]
        mock_grpc_response.maxMemory = sample_job_response["max_memory"]
        mock_grpc_response.maxIobps = sample_job_response["max_iobps"]
        mock_grpc_response.startTime = sample_job_response["start_time"]
        mock_grpc_response.endTime = sample_job_response["end_time"]
        mock_grpc_response.exitCode = sample_job_response["exit_code"]
        mock_grpc_response.scheduledTime = sample_job_response["scheduled_time"]
        mock_grpc_response.gpu_indices = [0, 1]
        mock_grpc_response.gpu_count = 2
        mock_grpc_response.gpu_memory_mb = 8192

        mock_stub.RunJob.return_value = mock_grpc_response

        result = job_service.run_job(
            command="python",
            args=["train.py"],
            name="gpu-job",
            gpu_count=2,
            gpu_memory_mb=8192,
            runtime="python-3.11-ml",
        )

        # Verify the result contains GPU info
        assert result["job_uuid"] == sample_job_response["job_uuid"]
        assert result["command"] == "python"
        assert result["args"] == ["train.py"]

        # Verify the request was made with GPU parameters
        call_args = mock_stub.RunJob.call_args[0][0]
        assert call_args.gpu_count == 2
        assert call_args.gpu_memory_mb == 8192
        assert call_args.command == "python"
        assert call_args.args == ["train.py"]
