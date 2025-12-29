"""Service classes for Joblet SDK"""

from datetime import datetime
from typing import Any, Dict, Iterator, List, Optional

import grpc

from .exceptions import (
    JobNotFoundError,
    NetworkError,
    RuntimeNotFoundError,
    ValidationError,
    VolumeError,
)
from .proto import joblet_pb2, joblet_pb2_grpc


class JobService:
    """Service for managing jobs"""

    def __init__(self, channel: grpc.Channel):
        self.stub = joblet_pb2_grpc.JobServiceStub(channel)

    def run_job(
        self,
        command: str,
        args: Optional[List[str]] = None,
        name: Optional[str] = None,
        max_cpu: Optional[int] = None,
        cpu_cores: Optional[str] = None,
        max_memory: Optional[int] = None,
        max_iobps: Optional[int] = None,
        schedule: Optional[str] = None,
        network: Optional[str] = None,
        volumes: Optional[List[str]] = None,
        runtime: Optional[str] = None,
        work_dir: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None,
        secret_environment: Optional[Dict[str, str]] = None,
        uploads: Optional[List[Dict[str, Any]]] = None,
        gpu_count: Optional[int] = None,
        gpu_memory_mb: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Run a new job

        Args:
            command: Command to execute
            args: Command arguments
            name: Job name
            max_cpu: Maximum CPU percentage
            cpu_cores: CPU cores specification
            max_memory: Maximum memory in MB
            max_iobps: Maximum IO operations per second
            schedule: Schedule time (RFC3339)
            network: Network configuration
            volumes: List of volumes to mount
            runtime: Runtime specification
            work_dir: Working directory
            environment: Environment variables
            secret_environment: Secret environment variables
            uploads: Files to upload
            gpu_count: Number of GPUs to allocate
            gpu_memory_mb: Minimum GPU memory required in MB

        Returns:
            Job response dictionary
        """
        request = joblet_pb2.RunJobRequest(
            command=command,
            args=args or [],
            name=name or "",
            maxCpu=max_cpu or 0,
            cpuCores=cpu_cores or "",
            maxMemory=max_memory or 0,
            maxIobps=max_iobps or 0,
            schedule=schedule or "",
            network=network or "",
            volumes=volumes or [],
            runtime=runtime or "",
            workDir=work_dir or "",
            environment=environment or {},
            secret_environment=secret_environment or {},
            gpu_count=gpu_count or 0,
            gpu_memory_mb=gpu_memory_mb or 0,
        )

        # Add file uploads if provided
        if uploads:
            for upload in uploads:
                file_upload = joblet_pb2.FileUpload(
                    path=upload.get("path", ""),
                    content=upload.get("content", b""),
                    mode=upload.get("mode", 0o644),
                    isDirectory=upload.get("is_directory", False),
                )
                request.uploads.append(file_upload)

        try:
            response = self.stub.RunJob(request)
            return {
                "job_uuid": response.jobUuid,
                "status": response.status,
                "command": response.command,
                "args": list(response.args),
                "max_cpu": response.maxCpu,
                "cpu_cores": response.cpuCores,
                "max_memory": response.maxMemory,
                "max_iobps": response.maxIobps,
                "start_time": response.startTime,
                "end_time": response.endTime,
                "exit_code": response.exitCode,
                "scheduled_time": response.scheduledTime,
            }
        except grpc.RpcError as e:
            raise JobNotFoundError(f"Failed to run job: {e.details()}")

    def get_job_status(self, job_uuid: str) -> Dict[str, Any]:
        """Get job status

        Args:
            job_uuid: Job UUID

        Returns:
            Job status dictionary
        """
        request = joblet_pb2.GetJobStatusReq(uuid=job_uuid)

        try:
            response = self.stub.GetJobStatus(request)
            return {
                "uuid": response.uuid,
                "name": response.name,
                "command": response.command,
                "args": list(response.args),
                "max_cpu": response.maxCPU,
                "cpu_cores": response.cpuCores,
                "max_memory": response.maxMemory,
                "max_iobps": response.maxIOBPS,
                "status": response.status,
                "start_time": response.startTime,
                "end_time": response.endTime,
                "exit_code": response.exitCode,
                "scheduled_time": response.scheduledTime,
                "environment": dict(response.environment),
                "secret_environment": dict(response.secret_environment),
                "network": response.network,
                "volumes": list(response.volumes),
                "runtime": response.runtime,
                "work_dir": response.workDir,
                "uploads": list(response.uploads),
                "gpu_indices": list(response.gpu_indices),
                "gpu_count": response.gpu_count,
                "gpu_memory_mb": response.gpu_memory_mb,
                "node_id": response.nodeId,
            }
        except grpc.RpcError as e:
            raise JobNotFoundError(f"Job {job_uuid} not found: {e.details()}")

    def stop_job(self, job_uuid: str) -> Dict[str, Any]:
        """Stop a running job

        Args:
            job_uuid: Job UUID

        Returns:
            Stop response dictionary
        """
        request = joblet_pb2.StopJobReq(uuid=job_uuid)

        try:
            response = self.stub.StopJob(request)
            return {
                "uuid": response.uuid,
                "status": response.status,
                "end_time": response.endTime,
                "exit_code": response.exitCode,
            }
        except grpc.RpcError as e:
            raise JobNotFoundError(f"Failed to stop job {job_uuid}: {e.details()}")

    def cancel_job(self, job_uuid: str) -> Dict[str, Any]:
        """Cancel a scheduled job

        This is specifically for jobs in SCHEDULED status. It will:
        - Cancel the job (preventing it from executing)
        - Change status to CANCELED (not STOPPED)
        - Preserve the job in history for audit

        Args:
            job_uuid: Job UUID

        Returns:
            Cancel response dictionary with uuid, status

        Raises:
            JobNotFoundError: If job not found or not scheduled
        """
        request = joblet_pb2.CancelJobReq(uuid=job_uuid)

        try:
            response = self.stub.CancelJob(request)
            return {
                "uuid": response.uuid,
                "status": response.status,
            }
        except grpc.RpcError as e:
            raise JobNotFoundError(f"Failed to cancel job {job_uuid}: {e.details()}")

    def delete_job(self, job_uuid: str) -> Dict[str, Any]:
        """Delete a job

        Args:
            job_uuid: Job UUID

        Returns:
            Delete response dictionary
        """
        request = joblet_pb2.DeleteJobReq(uuid=job_uuid)

        try:
            response = self.stub.DeleteJob(request)
            return {
                "uuid": response.uuid,
                "success": response.success,
                "message": response.message,
            }
        except grpc.RpcError as e:
            raise JobNotFoundError(f"Failed to delete job {job_uuid}: {e.details()}")

    def delete_all_jobs(self) -> Dict[str, Any]:
        """Delete all non-running jobs

        Returns:
            Delete response dictionary
        """
        request = joblet_pb2.DeleteAllJobsReq()

        try:
            response = self.stub.DeleteAllJobs(request)
            return {
                "success": response.success,
                "message": response.message,
                "deleted_count": response.deleted_count,
                "skipped_count": response.skipped_count,
            }
        except grpc.RpcError as e:
            raise JobNotFoundError(f"Failed to delete all jobs: {e.details()}")

    def get_job_logs(
        self, job_uuid: str, include_historical: bool = True
    ) -> Iterator[bytes]:
        """Stream job logs with automatic historical + live log handling

        The Joblet service automatically provides both historical and live logs in a
        single stream. Historical logs (if any) are sent first, followed by live logs
        from the running job. The server handles this internally via IPC to the persist
        subprocess.

        This provides seamless log access for both completed and running jobs,
        similar to how 'rnx job log' works.

        Args:
            job_uuid: Job UUID or short UUID prefix
            include_historical: Deprecated parameter, kept for backwards
                compatibility. Server always includes historical logs.

        Yields:
            bytes: Log chunks from both historical and live sources

        Raises:
            JobNotFoundError: If the job doesn't exist

        Example:
            >>> # Get all logs (historical + live) for any job
            >>> for chunk in client.jobs.get_job_logs(job_uuid):
            ...     print(chunk.decode('utf-8'), end='')
        """
        # Stream logs from joblet service (includes both historical and live)
        request = joblet_pb2.GetJobLogsReq(uuid=job_uuid)

        try:
            for chunk in self.stub.GetJobLogs(request):
                yield chunk.payload
        except grpc.RpcError as e:
            raise JobNotFoundError(
                f"Failed to get logs for job {job_uuid}: {e.details()}"
            )

    def stream_live_logs(self, job_uuid: str) -> Iterator[bytes]:
        """Stream live logs only (skip historical logs)

        This method only streams logs from the live job service, skipping
        any historical logs. Useful when you only want to see new output.

        Args:
            job_uuid: Job UUID or short UUID prefix

        Yields:
            bytes: Log chunks as they arrive from the job

        Raises:
            JobNotFoundError: If the job doesn't exist

        Example:
            >>> for chunk in client.jobs.stream_live_logs(job_uuid):
            ...     print(chunk.decode('utf-8'), end='')
        """
        return self.get_job_logs(job_uuid, include_historical=False)

    def stream_job_metrics(self, job_uuid: str) -> Iterator[Dict[str, Any]]:
        """Stream live metrics for a running job

        Streams real-time resource usage metrics including CPU, memory, disk I/O,
        network, and GPU usage (if applicable). The stream continues until the
        job completes or the connection is closed.

        Args:
            job_uuid: Job UUID or short UUID prefix

        Yields:
            Dict[str, Any]: Metric event dictionaries containing:
                - timestamp: Unix timestamp in nanoseconds
                - job_id: Job UUID
                - cpu_percent: CPU usage percentage
                - memory_bytes: Current memory usage in bytes
                - memory_limit: Memory limit in bytes
                - disk_read_bytes: Total disk bytes read
                - disk_write_bytes: Total disk bytes written
                - net_recv_bytes: Total network bytes received
                - net_sent_bytes: Total network bytes sent
                - gpu_percent: GPU utilization percentage (0 if no GPU)
                - gpu_memory_bytes: GPU memory usage in bytes (0 if no GPU)

        Raises:
            JobNotFoundError: If the job doesn't exist

        Example:
            >>> for metric in client.jobs.stream_job_metrics(job_uuid):
            ...     cpu = metric['cpu_percent']
            ...     memory_mb = metric['memory_bytes'] / (1024 * 1024)
            ...     print(f"CPU: {cpu:.2f}%, Memory: {memory_mb:.2f} MB")
        """
        request = joblet_pb2.StreamJobMetricsRequest(job_uuid=job_uuid)

        try:
            for event in self.stub.StreamJobMetrics(request):
                yield self._parse_metrics_event(event)
        except grpc.RpcError as e:
            raise JobNotFoundError(
                f"Failed to stream metrics for job {job_uuid}: {e.details()}"
            )

    def get_job_metrics(
        self,
        job_uuid: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> Iterator[Dict[str, Any]]:
        """Get historical metrics for a completed job

        Retrieves stored metrics from the persistence layer. Useful for
        post-mortem analysis of job resource usage.

        Args:
            job_uuid: Job UUID or short UUID prefix
            start_time: Start time in Unix nanoseconds (0 or None = beginning)
            end_time: End time in Unix nanoseconds (0 or None = end of job)
            limit: Maximum number of events to return (0 or None = no limit)

        Yields:
            Dict[str, Any]: Metric event dictionaries containing:
                - timestamp: Unix timestamp in nanoseconds
                - job_id: Job UUID
                - cpu_percent: CPU usage percentage
                - memory_bytes: Current memory usage in bytes
                - memory_limit: Memory limit in bytes
                - disk_read_bytes: Total disk bytes read
                - disk_write_bytes: Total disk bytes written
                - net_recv_bytes: Total network bytes received
                - net_sent_bytes: Total network bytes sent
                - gpu_percent: GPU utilization percentage (0 if no GPU)
                - gpu_memory_bytes: GPU memory usage in bytes (0 if no GPU)

        Raises:
            JobNotFoundError: If the job doesn't exist

        Example:
            >>> for metric in client.jobs.get_job_metrics(job_uuid):
            ...     cpu = metric['cpu_percent']
            ...     memory_mb = metric['memory_bytes'] / (1024 * 1024)
            ...     print(f"CPU: {cpu:.2f}%, Memory: {memory_mb:.2f} MB")
        """
        request = joblet_pb2.GetJobMetricsRequest(
            job_uuid=job_uuid,
            start_time=start_time or 0,
            end_time=end_time or 0,
            limit=limit or 0,
        )

        try:
            for event in self.stub.GetJobMetrics(request):
                yield self._parse_metrics_event(event)
        except grpc.RpcError as e:
            raise JobNotFoundError(
                f"Failed to get metrics for job {job_uuid}: {e.details()}"
            )

    def _parse_metrics_event(self, event) -> Dict[str, Any]:
        """Parse a JobMetricsEvent protobuf message to a dictionary"""
        return {
            "timestamp": event.timestamp,
            "job_id": event.job_id,
            "cpu_percent": event.cpu_percent,
            "memory_bytes": event.memory_bytes,
            "memory_limit": event.memory_limit,
            "disk_read_bytes": event.disk_read_bytes,
            "disk_write_bytes": event.disk_write_bytes,
            "net_recv_bytes": event.net_recv_bytes,
            "net_sent_bytes": event.net_sent_bytes,
            "gpu_percent": event.gpu_percent,
            "gpu_memory_bytes": event.gpu_memory_bytes,
        }

    def stream_job_telematics(
        self, job_uuid: str, event_types: Optional[List[str]] = None
    ) -> Iterator[Dict[str, Any]]:
        """Stream live telematics events for a running job

        Streams eBPF security events in real-time including process executions,
        network connections, file operations, and memory events. The stream
        continues until the job completes or the connection is closed.

        Args:
            job_uuid: Job UUID or short UUID prefix
            event_types: Optional list of event types to filter:
                - "exec": Process executions (eBPF execve tracing)
                - "connect": Outgoing network connections (eBPF connect tracing)
                - "accept": Incoming network connections (eBPF accept tracing)
                - "file": File operations (eBPF file tracing)
                - "mmap": Memory mapping events (eBPF mmap tracing)
                - "mprotect": Memory protection changes (eBPF mprotect tracing)
                - "socket_data": Socket data transfers (eBPF send/recv tracing)
                If None or empty, all event types are streamed.

        Yields:
            Dict[str, Any]: Telematics event dictionaries containing:
                - timestamp: Unix timestamp in nanoseconds
                - job_id: Job UUID
                - type: Event type
                - data: Event-specific data

        Raises:
            JobNotFoundError: If the job doesn't exist

        Example:
            >>> # Stream all telematics events
            >>> for event in client.jobs.stream_job_telematics(job_uuid):
            ...     if event['type'] == 'exec':
            ...         print(f"EXEC: {event['exec']['binary']}")
            ...     elif event['type'] == 'connect':
            ...         conn = event['connect']
            ...         print(f"CONNECT: {conn['dst_addr']}:{conn['dst_port']}")

            >>> # Stream only exec and connect events
            >>> for event in client.jobs.stream_job_telematics(
            ...     job_uuid, ["exec", "connect"]
            ... ):
            ...     print(event)
        """
        request = joblet_pb2.StreamJobTelematicsRequest(
            job_uuid=job_uuid,
            types=event_types or [],
        )

        try:
            for event in self.stub.StreamJobTelematics(request):
                yield self._parse_telematics_event(event)
        except grpc.RpcError as e:
            raise JobNotFoundError(
                f"Failed to stream telematics for job {job_uuid}: {e.details()}"
            )

    # Backward compatibility alias
    stream_job_telemetry = stream_job_telematics

    def get_job_telematics(
        self,
        job_uuid: str,
        event_types: Optional[List[str]] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> Iterator[Dict[str, Any]]:
        """Get historical telematics events for a completed job

        Retrieves stored eBPF security events from the persistence layer.
        Useful for post-mortem analysis of job execution behavior.

        Args:
            job_uuid: Job UUID or short UUID prefix
            event_types: Optional list of event types to filter:
                - "exec": Process executions (eBPF execve tracing)
                - "connect": Outgoing network connections (eBPF connect tracing)
                - "accept": Incoming network connections (eBPF accept tracing)
                - "file": File operations (eBPF file tracing)
                - "mmap": Memory mapping events (eBPF mmap tracing)
                - "mprotect": Memory protection changes (eBPF mprotect tracing)
                - "socket_data": Socket data transfers (eBPF send/recv tracing)
                If None or empty, all event types are returned.
            start_time: Start time in Unix nanoseconds (0 or None = beginning)
            end_time: End time in Unix nanoseconds (0 or None = end of job)
            limit: Maximum number of events to return (0 or None = no limit)

        Yields:
            Dict[str, Any]: Telematics event dictionaries containing:
                - timestamp: Unix timestamp in nanoseconds
                - job_id: Job UUID
                - type: Event type
                - data: Event-specific data

        Raises:
            JobNotFoundError: If the job doesn't exist or telematics unavailable

        Example:
            >>> # Get all historical telematics
            >>> events = list(client.jobs.get_job_telematics(job_uuid))

            >>> # Get only exec events
            >>> for event in client.jobs.get_job_telematics(job_uuid, ["exec"]):
            ...     exec_data = event['exec']
            ...     print(f"PID {exec_data['pid']}: {exec_data['binary']}")

            >>> # Get events with time range and limit
            >>> for event in client.jobs.get_job_telematics(
            ...     job_uuid,
            ...     start_time=start_ns,
            ...     end_time=end_ns,
            ...     limit=100
            ... ):
            ...     print(event)
        """
        request = joblet_pb2.GetJobTelematicsRequest(
            job_uuid=job_uuid,
            types=event_types or [],
            start_time=start_time or 0,
            end_time=end_time or 0,
            limit=limit or 0,
        )

        try:
            for event in self.stub.GetJobTelematics(request):
                yield self._parse_telematics_event(event)
        except grpc.RpcError as e:
            raise JobNotFoundError(
                f"Failed to get telematics for job {job_uuid}: {e.details()}"
            )

    # Backward compatibility alias
    get_job_telemetry = get_job_telematics

    def _parse_telematics_event(self, event) -> Dict[str, Any]:
        """Parse a TelematicsEvent protobuf message to a dictionary"""
        result = {
            "timestamp": event.timestamp,
            "job_id": event.job_id,
            "type": event.type,
        }

        # Parse the oneof data field based on event type
        if event.HasField("exec"):
            exec_data = event.exec
            result["exec"] = {
                "pid": exec_data.pid,
                "ppid": exec_data.ppid,
                "binary": exec_data.binary,
                "args": list(exec_data.args),
                "exit_code": exec_data.exit_code,
            }
        elif event.HasField("connect"):
            conn = event.connect
            result["connect"] = {
                "pid": conn.pid,
                "dst_addr": conn.dst_addr,
                "dst_port": conn.dst_port,
                "src_addr": conn.src_addr,
                "src_port": conn.src_port,
                "protocol": conn.protocol,
            }
        elif event.HasField("accept"):
            acc = event.accept
            result["accept"] = {
                "pid": acc.pid,
                "src_addr": acc.src_addr,
                "src_port": acc.src_port,
                "dst_addr": acc.dst_addr,
                "dst_port": acc.dst_port,
                "protocol": acc.protocol,
            }
        elif event.HasField("file"):
            file_data = event.file
            result["file"] = {
                "pid": file_data.pid,
                "path": file_data.path,
                "operation": file_data.operation,
                "bytes": file_data.bytes,
                "flags": file_data.flags,
            }
        elif event.HasField("mmap"):
            mmap_data = event.mmap
            result["mmap"] = {
                "pid": mmap_data.pid,
                "addr": mmap_data.addr,
                "length": mmap_data.length,
                "prot": mmap_data.prot,
                "flags": mmap_data.flags,
                "file_path": mmap_data.file_path,
            }
        elif event.HasField("mprotect"):
            mprot = event.mprotect
            result["mprotect"] = {
                "pid": mprot.pid,
                "addr": mprot.addr,
                "length": mprot.length,
                "prot": mprot.prot,
            }
        elif event.HasField("socket_data"):
            sock = event.socket_data
            result["socket_data"] = {
                "pid": sock.pid,
                "direction": sock.direction,
                "dst_addr": sock.dst_addr,
                "dst_port": sock.dst_port,
                "src_addr": sock.src_addr,
                "src_port": sock.src_port,
                "protocol": sock.protocol,
                "bytes": sock.bytes,
            }

        return result

    def list_jobs(self) -> List[Dict[str, Any]]:
        """List all jobs on the server

        Retrieves a list of all jobs including their status, resource usage,
        and metadata. Jobs are returned in creation order.

        Returns:
            List[Dict[str, Any]]: List of job dictionaries containing:
                - uuid: Job unique identifier
                - name: Job name
                - status: Current status (pending, running, completed, failed, etc.)
                - command: Executed command
                - start_time: When the job started
                - exit_code: Exit code (if completed)

        Raises:
            JobNotFoundError: If unable to retrieve job list

        Example:
            >>> jobs = client.jobs.list_jobs()
            >>> for job in jobs:
            ...     print(f"{job['name']}: {job['status']}")
        """
        request = joblet_pb2.EmptyRequest()

        try:
            response = self.stub.ListJobs(request)
            jobs = []
            for job in response.jobs:
                jobs.append(
                    {
                        "uuid": job.uuid,
                        "name": job.name,
                        "command": job.command,
                        "args": list(job.args),
                        "max_cpu": job.maxCPU,
                        "cpu_cores": job.cpuCores,
                        "max_memory": job.maxMemory,
                        "max_iobps": job.maxIOBPS,
                        "status": job.status,
                        "start_time": job.startTime,
                        "end_time": job.endTime,
                        "exit_code": job.exitCode,
                        "scheduled_time": job.scheduledTime,
                        "runtime": job.runtime,
                        "environment": dict(job.environment),
                        "secret_environment": dict(job.secret_environment),
                        "gpu_indices": list(job.gpu_indices),
                        "gpu_count": job.gpu_count,
                        "gpu_memory_mb": job.gpu_memory_mb,
                        "node_id": job.nodeId,
                    }
                )
            return jobs
        except grpc.RpcError as e:
            raise JobNotFoundError(f"Failed to list jobs: {e.details()}")

    @staticmethod
    def _timestamp_to_datetime(timestamp: Any) -> Optional[datetime]:
        """Convert protobuf timestamp to datetime"""
        if timestamp and timestamp.seconds:
            return datetime.fromtimestamp(timestamp.seconds + timestamp.nanos / 1e9)
        return None


class NetworkService:
    """Service for managing networks"""

    def __init__(self, channel: grpc.Channel):
        self.stub = joblet_pb2_grpc.NetworkServiceStub(channel)

    def create_network(self, name: str, cidr: str) -> Dict[str, Any]:
        """Create a new network

        Args:
            name: Network name
            cidr: CIDR block (e.g., "10.0.0.0/24")

        Returns:
            Network creation response
        """
        request = joblet_pb2.CreateNetworkReq(name=name, cidr=cidr)

        try:
            response = self.stub.CreateNetwork(request)
            return {
                "name": response.name,
                "cidr": response.cidr,
                "bridge": response.bridge,
            }
        except grpc.RpcError as e:
            raise NetworkError(f"Failed to create network: {e.details()}")

    def list_networks(self) -> List[Dict[str, Any]]:
        """List all networks

        Returns:
            List of network dictionaries
        """
        request = joblet_pb2.EmptyRequest()

        try:
            response = self.stub.ListNetworks(request)
            networks = []
            for network in response.networks:
                networks.append(
                    {
                        "name": network.name,
                        "cidr": network.cidr,
                        "bridge": network.bridge,
                        "job_count": network.jobCount,
                    }
                )
            return networks
        except grpc.RpcError as e:
            raise NetworkError(f"Failed to list networks: {e.details()}")

    def remove_network(self, name: str) -> Dict[str, Any]:
        """Remove a network

        Args:
            name: Network name

        Returns:
            Removal response
        """
        request = joblet_pb2.RemoveNetworkReq(name=name)

        try:
            response = self.stub.RemoveNetwork(request)
            return {"success": response.success, "message": response.message}
        except grpc.RpcError as e:
            raise NetworkError(f"Failed to remove network: {e.details()}")


class VolumeService:
    """Service for managing volumes"""

    def __init__(self, channel: grpc.Channel):
        self.stub = joblet_pb2_grpc.VolumeServiceStub(channel)

    def create_volume(
        self, name: str, size: str, volume_type: str = "filesystem"
    ) -> Dict[str, Any]:
        """Create a new volume

        Args:
            name: Volume name
            size: Volume size (e.g., "1GB", "500MB")
            volume_type: Type of volume ("filesystem" or "memory")

        Returns:
            Volume creation response
        """
        request = joblet_pb2.CreateVolumeReq(name=name, size=size, type=volume_type)

        try:
            response = self.stub.CreateVolume(request)
            return {
                "name": response.name,
                "size": response.size,
                "type": response.type,
                "path": response.path,
            }
        except grpc.RpcError as e:
            raise VolumeError(f"Failed to create volume: {e.details()}")

    def list_volumes(self) -> List[Dict[str, Any]]:
        """List all volumes

        Returns:
            List of volume dictionaries
        """
        request = joblet_pb2.EmptyRequest()

        try:
            response = self.stub.ListVolumes(request)
            volumes = []
            for volume in response.volumes:
                volumes.append(
                    {
                        "name": volume.name,
                        "size": volume.size,
                        "type": volume.type,
                        "path": volume.path,
                        "created_time": volume.createdTime,
                        "job_count": volume.jobCount,
                    }
                )
            return volumes
        except grpc.RpcError as e:
            raise VolumeError(f"Failed to list volumes: {e.details()}")

    def remove_volume(self, name: str) -> Dict[str, Any]:
        """Remove a volume

        Args:
            name: Volume name

        Returns:
            Removal response
        """
        request = joblet_pb2.RemoveVolumeReq(name=name)

        try:
            response = self.stub.RemoveVolume(request)
            return {"success": response.success, "message": response.message}
        except grpc.RpcError as e:
            raise VolumeError(f"Failed to remove volume: {e.details()}")


class MonitoringService:
    """Service for system monitoring"""

    def __init__(self, channel: grpc.Channel):
        self.stub = joblet_pb2_grpc.MonitoringServiceStub(channel)

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status and resource availability

        Retrieves current system health information including CPU, memory,
        disk, network, and GPU metrics. Useful for monitoring server
        capacity before submitting resource-intensive jobs.

        Returns:
            Dict[str, Any]: System status containing:
                - available: Boolean indicating server availability
                - cpu: CPU metrics (usage, cores, load average)
                - memory: Memory usage and availability
                - disks: Disk usage per mount point
                - networks: Network interface statistics
                - host: Server information (hostname, OS, uptime)
                - gpu: GPU information (if available)

        Raises:
            RuntimeError: If unable to retrieve system status

        Example:
            >>> status = client.monitoring.get_system_status()
            >>> print(f"Available: {status['available']}")
            >>> print(f"CPU: {status['cpu']['usage_percent']:.1f}%")
            >>> print(f"Memory: {status['memory']['usage_percent']:.1f}%")
        """
        request = joblet_pb2.EmptyRequest()

        try:
            response = self.stub.GetSystemStatus(request)
            return self._parse_system_status(response)
        except grpc.RpcError as e:
            raise RuntimeError(f"Failed to get system status: {e.details()}")

    def stream_system_metrics(
        self, interval_seconds: int = 5, metric_types: Optional[List[str]] = None
    ) -> Iterator[Dict[str, Any]]:
        """Stream real-time system metrics at regular intervals

        Continuously streams system performance metrics, useful for
        monitoring server health over time or building dashboards.

        Args:
            interval_seconds: Update interval in seconds (default: 5)
            metric_types: Optional list to filter specific metric types

        Yields:
            Dict[str, Any]: Metrics snapshot containing CPU, memory, disk,
                network, and process information at each interval

        Raises:
            RuntimeError: If unable to stream metrics

        Example:
            >>> metrics_stream = client.monitoring.stream_system_metrics(
            ...     interval_seconds=10
            ... )
            >>> for metrics in metrics_stream:
            ...     cpu = metrics['cpu']['usage_percent']
            ...     mem = metrics['memory']['usage_percent']
            ...     print(f"CPU: {cpu:.1f}%, Memory: {mem:.1f}%")
            ...     if cpu > 90:
            ...         break  # Stop monitoring if CPU too high
        """
        request = joblet_pb2.StreamMetricsReq(
            intervalSeconds=interval_seconds, metricTypes=metric_types or []
        )

        try:
            for metrics in self.stub.StreamSystemMetrics(request):
                yield self._parse_system_metrics(metrics)
        except grpc.RpcError as e:
            raise RuntimeError(f"Failed to stream metrics: {e.details()}")

    def _parse_system_status(self, response) -> Dict[str, Any]:
        """Parse system status response"""
        result = {"timestamp": response.timestamp, "available": response.available}

        if response.HasField("host"):
            result["host"] = self._parse_host_info(response.host)
        if response.HasField("cpu"):
            result["cpu"] = self._parse_cpu_metrics(response.cpu)
        if response.HasField("memory"):
            result["memory"] = self._parse_memory_metrics(response.memory)
        if response.disks:
            result["disks"] = [self._parse_disk_metrics(d) for d in response.disks]
        if response.networks:
            result["networks"] = [
                self._parse_network_metrics(n) for n in response.networks
            ]
        if response.HasField("io"):
            result["io"] = self._parse_io_metrics(response.io)
        if response.HasField("processes"):
            result["processes"] = self._parse_process_metrics(response.processes)
        if response.HasField("cloud"):
            result["cloud"] = self._parse_cloud_info(response.cloud)
        if response.HasField("server_version"):
            result["server_version"] = self._parse_server_version(
                response.server_version
            )

        return result

    def _parse_system_metrics(self, response) -> Dict[str, Any]:
        """Parse system metrics response"""
        result = {"timestamp": response.timestamp}

        if response.HasField("host"):
            result["host"] = self._parse_host_info(response.host)
        if response.HasField("cpu"):
            result["cpu"] = self._parse_cpu_metrics(response.cpu)
        if response.HasField("memory"):
            result["memory"] = self._parse_memory_metrics(response.memory)
        if response.disks:
            result["disks"] = [self._parse_disk_metrics(d) for d in response.disks]
        if response.networks:
            result["networks"] = [
                self._parse_network_metrics(n) for n in response.networks
            ]
        if response.HasField("io"):
            result["io"] = self._parse_io_metrics(response.io)
        if response.HasField("processes"):
            result["processes"] = self._parse_process_metrics(response.processes)
        if response.HasField("cloud"):
            result["cloud"] = self._parse_cloud_info(response.cloud)

        return result

    @staticmethod
    def _parse_host_info(host) -> Dict[str, Any]:
        """Parse host info"""
        return {
            "hostname": host.hostname,
            "os": host.os,
            "platform": host.platform,
            "platform_family": host.platformFamily,
            "platform_version": host.platformVersion,
            "kernel_version": host.kernelVersion,
            "kernel_arch": host.kernelArch,
            "architecture": host.architecture,
            "cpu_count": host.cpuCount,
            "total_memory": host.totalMemory,
            "boot_time": host.bootTime,
            "uptime": host.uptime,
            "node_id": host.nodeId,
            "server_ips": list(host.serverIPs),
            "mac_addresses": list(host.macAddresses),
        }

    @staticmethod
    def _parse_cpu_metrics(cpu) -> Dict[str, Any]:
        """Parse CPU metrics"""
        return {
            "cores": cpu.cores,
            "usage_percent": cpu.usagePercent,
            "user_time": cpu.userTime,
            "system_time": cpu.systemTime,
            "idle_time": cpu.idleTime,
            "io_wait_time": cpu.ioWaitTime,
            "steal_time": cpu.stealTime,
            "load_average": list(cpu.loadAverage),
            "per_core_usage": list(cpu.perCoreUsage),
        }

    @staticmethod
    def _parse_memory_metrics(memory) -> Dict[str, Any]:
        """Parse memory metrics"""
        return {
            "total_bytes": memory.totalBytes,
            "used_bytes": memory.usedBytes,
            "free_bytes": memory.freeBytes,
            "available_bytes": memory.availableBytes,
            "usage_percent": memory.usagePercent,
            "cached_bytes": memory.cachedBytes,
            "buffered_bytes": memory.bufferedBytes,
            "swap_total": memory.swapTotal,
            "swap_used": memory.swapUsed,
            "swap_free": memory.swapFree,
        }

    @staticmethod
    def _parse_disk_metrics(disk) -> Dict[str, Any]:
        """Parse disk metrics"""
        return {
            "device": disk.device,
            "mount_point": disk.mountPoint,
            "filesystem": disk.filesystem,
            "total_bytes": disk.totalBytes,
            "used_bytes": disk.usedBytes,
            "free_bytes": disk.freeBytes,
            "usage_percent": disk.usagePercent,
            "inodes_total": disk.inodesTotal,
            "inodes_used": disk.inodesUsed,
            "inodes_free": disk.inodesFree,
            "inodes_usage_percent": disk.inodesUsagePercent,
        }

    @staticmethod
    def _parse_network_metrics(network) -> Dict[str, Any]:
        """Parse network metrics"""
        return {
            "interface": network.interface,
            "bytes_received": network.bytesReceived,
            "bytes_sent": network.bytesSent,
            "packets_received": network.packetsReceived,
            "packets_sent": network.packetsSent,
            "errors_in": network.errorsIn,
            "errors_out": network.errorsOut,
            "drops_in": network.dropsIn,
            "drops_out": network.dropsOut,
            "receive_rate": network.receiveRate,
            "transmit_rate": network.transmitRate,
        }

    @staticmethod
    def _parse_io_metrics(io) -> Dict[str, Any]:
        """Parse IO metrics"""
        result = {
            "total_reads": io.totalReads,
            "total_writes": io.totalWrites,
            "read_bytes": io.readBytes,
            "write_bytes": io.writeBytes,
            "read_rate": io.readRate,
            "write_rate": io.writeRate,
        }

        if io.diskIO:
            result["disk_io"] = []
            for disk_io in io.diskIO:
                result["disk_io"].append(
                    {
                        "device": disk_io.device,
                        "reads_completed": disk_io.readsCompleted,
                        "writes_completed": disk_io.writesCompleted,
                        "read_bytes": disk_io.readBytes,
                        "write_bytes": disk_io.writeBytes,
                        "read_time": disk_io.readTime,
                        "write_time": disk_io.writeTime,
                        "io_time": disk_io.ioTime,
                        "utilization": disk_io.utilization,
                    }
                )

        return result

    @staticmethod
    def _parse_process_metrics(processes) -> Dict[str, Any]:
        """Parse process metrics"""
        result = {
            "total_processes": processes.totalProcesses,
            "running_processes": processes.runningProcesses,
            "sleeping_processes": processes.sleepingProcesses,
            "stopped_processes": processes.stoppedProcesses,
            "zombie_processes": processes.zombieProcesses,
            "total_threads": processes.totalThreads,
        }

        if processes.topByCPU:
            result["top_by_cpu"] = []
            for proc in processes.topByCPU:
                result["top_by_cpu"].append(
                    {
                        "pid": proc.pid,
                        "ppid": proc.ppid,
                        "name": proc.name,
                        "command": proc.command,
                        "cpu_percent": proc.cpuPercent,
                        "memory_percent": proc.memoryPercent,
                        "memory_bytes": proc.memoryBytes,
                        "status": proc.status,
                        "start_time": proc.startTime,
                        "user": proc.user,
                    }
                )

        if processes.topByMemory:
            result["top_by_memory"] = []
            for proc in processes.topByMemory:
                result["top_by_memory"].append(
                    {
                        "pid": proc.pid,
                        "ppid": proc.ppid,
                        "name": proc.name,
                        "command": proc.command,
                        "cpu_percent": proc.cpuPercent,
                        "memory_percent": proc.memoryPercent,
                        "memory_bytes": proc.memoryBytes,
                        "status": proc.status,
                        "start_time": proc.startTime,
                        "user": proc.user,
                    }
                )

        return result

    @staticmethod
    def _parse_cloud_info(cloud) -> Dict[str, Any]:
        """Parse cloud info"""
        return {
            "provider": cloud.provider,
            "region": cloud.region,
            "zone": cloud.zone,
            "instance_id": cloud.instanceID,
            "instance_type": cloud.instanceType,
            "hypervisor_type": cloud.hypervisorType,
            "metadata": dict(cloud.metadata),
        }

    @staticmethod
    def _parse_server_version(version) -> Dict[str, Any]:
        """Parse server version info"""
        return {
            "version": version.version,
            "git_commit": version.git_commit,
            "git_tag": version.git_tag,
            "build_date": version.build_date,
            "component": version.component,
            "go_version": version.go_version,
            "platform": version.platform,
            "proto_commit": version.proto_commit,
            "proto_tag": version.proto_tag,
        }


class RuntimeService:
    """Service for managing runtimes"""

    def __init__(self, channel: grpc.Channel):
        self.stub = joblet_pb2_grpc.RuntimeServiceStub(channel)

    def list_runtimes(self) -> List[Dict[str, Any]]:
        """List all available runtimes

        Returns:
            List of runtime dictionaries
        """
        request = joblet_pb2.EmptyRequest()

        try:
            response = self.stub.ListRuntimes(request)
            runtimes = []
            for runtime in response.runtimes:
                runtime_dict = {
                    "name": runtime.name,
                    "language": runtime.language,
                    "version": runtime.version,
                    "description": runtime.description,
                    "size_bytes": runtime.sizeBytes,
                    "packages": list(runtime.packages),
                    "available": runtime.available,
                }

                if runtime.HasField("requirements"):
                    runtime_dict["requirements"] = {
                        "architectures": list(runtime.requirements.architectures),
                        "gpu": runtime.requirements.gpu,
                    }

                runtimes.append(runtime_dict)

            return runtimes
        except grpc.RpcError as e:
            raise RuntimeNotFoundError(f"Failed to list runtimes: {e.details()}")

    def get_runtime_info(self, runtime: str) -> Dict[str, Any]:
        """Get runtime information

        Args:
            runtime: Runtime specification

        Returns:
            Runtime information dictionary
        """
        request = joblet_pb2.RuntimeInfoReq(runtime=runtime)

        try:
            response = self.stub.GetRuntimeInfo(request)
            if not response.found:
                raise RuntimeNotFoundError(f"Runtime {runtime} not found")

            runtime_info = {
                "name": response.runtime.name,
                "language": response.runtime.language,
                "version": response.runtime.version,
                "description": response.runtime.description,
                "size_bytes": response.runtime.sizeBytes,
                "packages": list(response.runtime.packages),
                "available": response.runtime.available,
            }

            if response.runtime.HasField("requirements"):
                runtime_info["requirements"] = {
                    "architectures": list(response.runtime.requirements.architectures),
                    "gpu": response.runtime.requirements.gpu,
                }

            return runtime_info
        except grpc.RpcError as e:
            raise RuntimeNotFoundError(f"Failed to get runtime info: {e.details()}")

    def test_runtime(self, runtime: str) -> Dict[str, Any]:
        """Test a runtime

        Args:
            runtime: Runtime specification

        Returns:
            Test result dictionary
        """
        request = joblet_pb2.RuntimeTestReq(runtime=runtime)

        try:
            response = self.stub.TestRuntime(request)
            return {
                "success": response.success,
                "output": response.output,
                "error": response.error,
                "exit_code": response.exitCode,
            }
        except grpc.RpcError as e:
            raise RuntimeNotFoundError(f"Failed to test runtime: {e.details()}")

    def remove_runtime(self, runtime: str) -> Dict[str, Any]:
        """Remove a runtime

        Args:
            runtime: Runtime to remove

        Returns:
            Removal response dictionary
        """
        request = joblet_pb2.RuntimeRemoveReq(runtime=runtime)

        try:
            response = self.stub.RemoveRuntime(request)
            return {
                "success": response.success,
                "message": response.message,
                "freed_space_bytes": response.freedSpaceBytes,
            }
        except grpc.RpcError as e:
            raise RuntimeNotFoundError(f"Failed to remove runtime: {e.details()}")

    def build_runtime(
        self,
        yaml_content: str,
        dry_run: bool = False,
        verbose: bool = False,
        force_rebuild: bool = False,
    ):
        """Build a runtime from YAML specification

        The build process uses OverlayFS-based isolation to ensure the host system
        is never modified. System packages are installed in an isolated chroot,
        and only the resulting binaries/libraries are copied to the runtime directory.

        Args:
            yaml_content: YAML specification content (runtime.yaml)
            dry_run: If True, validate only without building
            verbose: If True, include detailed logs
            force_rebuild: If True, rebuild even if runtime exists

        Yields:
            Build progress events:
            - phase: Current build phase (1-14)
            - log: Build log lines
            - result: Final build result

        Example:
            ```python
            yaml_content = '''
            name: python-3.11-ml
            version: "1.0.0"
            language: python
            base_packages:
              - python3.11
              - python3.11-venv
            pip_packages:
              - numpy
              - pandas
            '''

            for event in client.runtimes.build_runtime(yaml_content, verbose=True):
                if "phase" in event:
                    phase_num = event['phase_number']
                    total = event['total_phases']
                    name = event['phase_name']
                    print(f"Phase {phase_num}/{total}: {name}")
                elif "log" in event:
                    print(event['log']['message'])
                elif "result" in event:
                    if event['result']['success']:
                        print(f"Runtime built: {event['result']['runtime_path']}")
            ```
        """
        request = joblet_pb2.BuildRuntimeRequest(
            yaml_content=yaml_content,
            dry_run=dry_run,
            verbose=verbose,
            force_rebuild=force_rebuild,
        )

        try:
            for progress in self.stub.BuildRuntime(request):
                if progress.HasField("phase"):
                    yield {
                        "phase": {
                            "phase_number": progress.phase.phase_number,
                            "total_phases": progress.phase.total_phases,
                            "phase_name": progress.phase.phase_name,
                            "message": progress.phase.message,
                        }
                    }
                elif progress.HasField("log"):
                    yield {
                        "log": {
                            "level": progress.log.level,
                            "message": progress.log.message,
                            "timestamp": progress.log.timestamp,
                        }
                    }
                elif progress.HasField("result"):
                    yield {
                        "result": {
                            "success": progress.result.success,
                            "message": progress.result.message,
                            "runtime_name": progress.result.runtime_name,
                            "runtime_version": progress.result.runtime_version,
                            "runtime_path": progress.result.runtime_path,
                            "build_duration_seconds": (
                                progress.result.build_duration_seconds
                            ),
                        }
                    }
        except grpc.RpcError as e:
            raise RuntimeError(f"Failed to build runtime: {e.details()}")

    def validate_runtime_yaml(self, yaml_content: str) -> Dict[str, Any]:
        """Validate a runtime YAML specification without building

        Args:
            yaml_content: YAML specification content to validate

        Returns:
            Validation result dictionary with:
            - valid: Whether the YAML is valid
            - message: Validation message
            - parsed_spec: Parsed specification details (if valid)
            - errors: List of validation errors (if invalid)
        """
        request = joblet_pb2.ValidateRuntimeYAMLRequest(yaml_content=yaml_content)

        try:
            response = self.stub.ValidateRuntimeYAML(request)
            result = {
                "valid": response.valid,
                "message": response.message,
            }

            if response.valid and response.HasField("parsed_spec"):
                result["parsed_spec"] = {
                    "name": response.parsed_spec.name,
                    "version": response.parsed_spec.version,
                    "language": response.parsed_spec.language,
                    "description": response.parsed_spec.description,
                }

            if not response.valid:
                result["errors"] = list(response.errors)

            return result
        except grpc.RpcError as e:
            raise ValidationError(f"Failed to validate runtime YAML: {e.details()}")


__all__ = [
    "JobService",
    "NetworkService",
    "VolumeService",
    "MonitoringService",
    "RuntimeService",
]
