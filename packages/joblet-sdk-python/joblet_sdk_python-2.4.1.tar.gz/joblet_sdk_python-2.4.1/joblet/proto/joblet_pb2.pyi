from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Jobs(_message.Message):
    __slots__ = ("jobs",)
    JOBS_FIELD_NUMBER: _ClassVar[int]
    jobs: _containers.RepeatedCompositeFieldContainer[Job]
    def __init__(self, jobs: _Optional[_Iterable[_Union[Job, _Mapping]]] = ...) -> None: ...

class Job(_message.Message):
    __slots__ = ("uuid", "name", "command", "args", "maxCPU", "cpuCores", "maxMemory", "maxIOBPS", "status", "startTime", "endTime", "exitCode", "scheduledTime", "runtime", "environment", "secret_environment", "gpu_indices", "gpu_count", "gpu_memory_mb", "nodeId")
    class EnvironmentEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    class SecretEnvironmentEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    UUID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    COMMAND_FIELD_NUMBER: _ClassVar[int]
    ARGS_FIELD_NUMBER: _ClassVar[int]
    MAXCPU_FIELD_NUMBER: _ClassVar[int]
    CPUCORES_FIELD_NUMBER: _ClassVar[int]
    MAXMEMORY_FIELD_NUMBER: _ClassVar[int]
    MAXIOBPS_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    STARTTIME_FIELD_NUMBER: _ClassVar[int]
    ENDTIME_FIELD_NUMBER: _ClassVar[int]
    EXITCODE_FIELD_NUMBER: _ClassVar[int]
    SCHEDULEDTIME_FIELD_NUMBER: _ClassVar[int]
    RUNTIME_FIELD_NUMBER: _ClassVar[int]
    ENVIRONMENT_FIELD_NUMBER: _ClassVar[int]
    SECRET_ENVIRONMENT_FIELD_NUMBER: _ClassVar[int]
    GPU_INDICES_FIELD_NUMBER: _ClassVar[int]
    GPU_COUNT_FIELD_NUMBER: _ClassVar[int]
    GPU_MEMORY_MB_FIELD_NUMBER: _ClassVar[int]
    NODEID_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    name: str
    command: str
    args: _containers.RepeatedScalarFieldContainer[str]
    maxCPU: int
    cpuCores: str
    maxMemory: int
    maxIOBPS: int
    status: str
    startTime: str
    endTime: str
    exitCode: int
    scheduledTime: str
    runtime: str
    environment: _containers.ScalarMap[str, str]
    secret_environment: _containers.ScalarMap[str, str]
    gpu_indices: _containers.RepeatedScalarFieldContainer[int]
    gpu_count: int
    gpu_memory_mb: int
    nodeId: str
    def __init__(self, uuid: _Optional[str] = ..., name: _Optional[str] = ..., command: _Optional[str] = ..., args: _Optional[_Iterable[str]] = ..., maxCPU: _Optional[int] = ..., cpuCores: _Optional[str] = ..., maxMemory: _Optional[int] = ..., maxIOBPS: _Optional[int] = ..., status: _Optional[str] = ..., startTime: _Optional[str] = ..., endTime: _Optional[str] = ..., exitCode: _Optional[int] = ..., scheduledTime: _Optional[str] = ..., runtime: _Optional[str] = ..., environment: _Optional[_Mapping[str, str]] = ..., secret_environment: _Optional[_Mapping[str, str]] = ..., gpu_indices: _Optional[_Iterable[int]] = ..., gpu_count: _Optional[int] = ..., gpu_memory_mb: _Optional[int] = ..., nodeId: _Optional[str] = ...) -> None: ...

class EmptyRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class FileUpload(_message.Message):
    __slots__ = ("path", "content", "mode", "isDirectory")
    PATH_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    MODE_FIELD_NUMBER: _ClassVar[int]
    ISDIRECTORY_FIELD_NUMBER: _ClassVar[int]
    path: str
    content: bytes
    mode: int
    isDirectory: bool
    def __init__(self, path: _Optional[str] = ..., content: _Optional[bytes] = ..., mode: _Optional[int] = ..., isDirectory: bool = ...) -> None: ...

class GetJobStatusReq(_message.Message):
    __slots__ = ("uuid",)
    UUID_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    def __init__(self, uuid: _Optional[str] = ...) -> None: ...

class GetJobStatusRes(_message.Message):
    __slots__ = ("uuid", "name", "command", "args", "maxCPU", "cpuCores", "maxMemory", "maxIOBPS", "status", "startTime", "endTime", "exitCode", "scheduledTime", "environment", "secret_environment", "network", "volumes", "runtime", "workDir", "uploads", "gpu_indices", "gpu_count", "gpu_memory_mb", "nodeId")
    class EnvironmentEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    class SecretEnvironmentEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    UUID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    COMMAND_FIELD_NUMBER: _ClassVar[int]
    ARGS_FIELD_NUMBER: _ClassVar[int]
    MAXCPU_FIELD_NUMBER: _ClassVar[int]
    CPUCORES_FIELD_NUMBER: _ClassVar[int]
    MAXMEMORY_FIELD_NUMBER: _ClassVar[int]
    MAXIOBPS_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    STARTTIME_FIELD_NUMBER: _ClassVar[int]
    ENDTIME_FIELD_NUMBER: _ClassVar[int]
    EXITCODE_FIELD_NUMBER: _ClassVar[int]
    SCHEDULEDTIME_FIELD_NUMBER: _ClassVar[int]
    ENVIRONMENT_FIELD_NUMBER: _ClassVar[int]
    SECRET_ENVIRONMENT_FIELD_NUMBER: _ClassVar[int]
    NETWORK_FIELD_NUMBER: _ClassVar[int]
    VOLUMES_FIELD_NUMBER: _ClassVar[int]
    RUNTIME_FIELD_NUMBER: _ClassVar[int]
    WORKDIR_FIELD_NUMBER: _ClassVar[int]
    UPLOADS_FIELD_NUMBER: _ClassVar[int]
    GPU_INDICES_FIELD_NUMBER: _ClassVar[int]
    GPU_COUNT_FIELD_NUMBER: _ClassVar[int]
    GPU_MEMORY_MB_FIELD_NUMBER: _ClassVar[int]
    NODEID_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    name: str
    command: str
    args: _containers.RepeatedScalarFieldContainer[str]
    maxCPU: int
    cpuCores: str
    maxMemory: int
    maxIOBPS: int
    status: str
    startTime: str
    endTime: str
    exitCode: int
    scheduledTime: str
    environment: _containers.ScalarMap[str, str]
    secret_environment: _containers.ScalarMap[str, str]
    network: str
    volumes: _containers.RepeatedScalarFieldContainer[str]
    runtime: str
    workDir: str
    uploads: _containers.RepeatedScalarFieldContainer[str]
    gpu_indices: _containers.RepeatedScalarFieldContainer[int]
    gpu_count: int
    gpu_memory_mb: int
    nodeId: str
    def __init__(self, uuid: _Optional[str] = ..., name: _Optional[str] = ..., command: _Optional[str] = ..., args: _Optional[_Iterable[str]] = ..., maxCPU: _Optional[int] = ..., cpuCores: _Optional[str] = ..., maxMemory: _Optional[int] = ..., maxIOBPS: _Optional[int] = ..., status: _Optional[str] = ..., startTime: _Optional[str] = ..., endTime: _Optional[str] = ..., exitCode: _Optional[int] = ..., scheduledTime: _Optional[str] = ..., environment: _Optional[_Mapping[str, str]] = ..., secret_environment: _Optional[_Mapping[str, str]] = ..., network: _Optional[str] = ..., volumes: _Optional[_Iterable[str]] = ..., runtime: _Optional[str] = ..., workDir: _Optional[str] = ..., uploads: _Optional[_Iterable[str]] = ..., gpu_indices: _Optional[_Iterable[int]] = ..., gpu_count: _Optional[int] = ..., gpu_memory_mb: _Optional[int] = ..., nodeId: _Optional[str] = ...) -> None: ...

class StopJobReq(_message.Message):
    __slots__ = ("uuid",)
    UUID_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    def __init__(self, uuid: _Optional[str] = ...) -> None: ...

class StopJobRes(_message.Message):
    __slots__ = ("uuid", "status", "endTime", "exitCode")
    UUID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    ENDTIME_FIELD_NUMBER: _ClassVar[int]
    EXITCODE_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    status: str
    endTime: str
    exitCode: int
    def __init__(self, uuid: _Optional[str] = ..., status: _Optional[str] = ..., endTime: _Optional[str] = ..., exitCode: _Optional[int] = ...) -> None: ...

class CancelJobReq(_message.Message):
    __slots__ = ("uuid",)
    UUID_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    def __init__(self, uuid: _Optional[str] = ...) -> None: ...

class CancelJobRes(_message.Message):
    __slots__ = ("uuid", "status")
    UUID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    status: str
    def __init__(self, uuid: _Optional[str] = ..., status: _Optional[str] = ...) -> None: ...

class DeleteJobReq(_message.Message):
    __slots__ = ("uuid",)
    UUID_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    def __init__(self, uuid: _Optional[str] = ...) -> None: ...

class DeleteJobRes(_message.Message):
    __slots__ = ("uuid", "success", "message")
    UUID_FIELD_NUMBER: _ClassVar[int]
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    success: bool
    message: str
    def __init__(self, uuid: _Optional[str] = ..., success: bool = ..., message: _Optional[str] = ...) -> None: ...

class DeleteAllJobsReq(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class DeleteAllJobsRes(_message.Message):
    __slots__ = ("success", "message", "deleted_count", "skipped_count")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    DELETED_COUNT_FIELD_NUMBER: _ClassVar[int]
    SKIPPED_COUNT_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    deleted_count: int
    skipped_count: int
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., deleted_count: _Optional[int] = ..., skipped_count: _Optional[int] = ...) -> None: ...

class GetJobLogsReq(_message.Message):
    __slots__ = ("uuid",)
    UUID_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    def __init__(self, uuid: _Optional[str] = ...) -> None: ...

class DataChunk(_message.Message):
    __slots__ = ("payload",)
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    payload: bytes
    def __init__(self, payload: _Optional[bytes] = ...) -> None: ...

class BuildRuntimeRequest(_message.Message):
    __slots__ = ("yaml_content", "dry_run", "verbose", "force_rebuild")
    YAML_CONTENT_FIELD_NUMBER: _ClassVar[int]
    DRY_RUN_FIELD_NUMBER: _ClassVar[int]
    VERBOSE_FIELD_NUMBER: _ClassVar[int]
    FORCE_REBUILD_FIELD_NUMBER: _ClassVar[int]
    yaml_content: str
    dry_run: bool
    verbose: bool
    force_rebuild: bool
    def __init__(self, yaml_content: _Optional[str] = ..., dry_run: bool = ..., verbose: bool = ..., force_rebuild: bool = ...) -> None: ...

class BuildRuntimeProgress(_message.Message):
    __slots__ = ("phase", "log", "result")
    PHASE_FIELD_NUMBER: _ClassVar[int]
    LOG_FIELD_NUMBER: _ClassVar[int]
    RESULT_FIELD_NUMBER: _ClassVar[int]
    phase: BuildPhaseProgress
    log: BuildLogLine
    result: BuildResult
    def __init__(self, phase: _Optional[_Union[BuildPhaseProgress, _Mapping]] = ..., log: _Optional[_Union[BuildLogLine, _Mapping]] = ..., result: _Optional[_Union[BuildResult, _Mapping]] = ...) -> None: ...

class BuildPhaseProgress(_message.Message):
    __slots__ = ("phase_number", "total_phases", "phase_name", "message")
    PHASE_NUMBER_FIELD_NUMBER: _ClassVar[int]
    TOTAL_PHASES_FIELD_NUMBER: _ClassVar[int]
    PHASE_NAME_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    phase_number: int
    total_phases: int
    phase_name: str
    message: str
    def __init__(self, phase_number: _Optional[int] = ..., total_phases: _Optional[int] = ..., phase_name: _Optional[str] = ..., message: _Optional[str] = ...) -> None: ...

class BuildLogLine(_message.Message):
    __slots__ = ("level", "message", "timestamp")
    LEVEL_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    level: str
    message: str
    timestamp: int
    def __init__(self, level: _Optional[str] = ..., message: _Optional[str] = ..., timestamp: _Optional[int] = ...) -> None: ...

class BuildResult(_message.Message):
    __slots__ = ("success", "message", "runtime_name", "runtime_version", "install_path", "size_bytes", "build_duration_ms")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    RUNTIME_NAME_FIELD_NUMBER: _ClassVar[int]
    RUNTIME_VERSION_FIELD_NUMBER: _ClassVar[int]
    INSTALL_PATH_FIELD_NUMBER: _ClassVar[int]
    SIZE_BYTES_FIELD_NUMBER: _ClassVar[int]
    BUILD_DURATION_MS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    runtime_name: str
    runtime_version: str
    install_path: str
    size_bytes: int
    build_duration_ms: int
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., runtime_name: _Optional[str] = ..., runtime_version: _Optional[str] = ..., install_path: _Optional[str] = ..., size_bytes: _Optional[int] = ..., build_duration_ms: _Optional[int] = ...) -> None: ...

class ValidateRuntimeYAMLRequest(_message.Message):
    __slots__ = ("yaml_content",)
    YAML_CONTENT_FIELD_NUMBER: _ClassVar[int]
    yaml_content: str
    def __init__(self, yaml_content: _Optional[str] = ...) -> None: ...

class ValidateRuntimeYAMLResponse(_message.Message):
    __slots__ = ("valid", "message", "errors", "warnings", "spec_info")
    VALID_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    ERRORS_FIELD_NUMBER: _ClassVar[int]
    WARNINGS_FIELD_NUMBER: _ClassVar[int]
    SPEC_INFO_FIELD_NUMBER: _ClassVar[int]
    valid: bool
    message: str
    errors: _containers.RepeatedScalarFieldContainer[str]
    warnings: _containers.RepeatedScalarFieldContainer[str]
    spec_info: RuntimeYAMLInfo
    def __init__(self, valid: bool = ..., message: _Optional[str] = ..., errors: _Optional[_Iterable[str]] = ..., warnings: _Optional[_Iterable[str]] = ..., spec_info: _Optional[_Union[RuntimeYAMLInfo, _Mapping]] = ...) -> None: ...

class RuntimeYAMLInfo(_message.Message):
    __slots__ = ("name", "version", "language", "language_version", "description", "pip_packages", "npm_packages", "has_hooks", "requires_gpu")
    NAME_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    LANGUAGE_FIELD_NUMBER: _ClassVar[int]
    LANGUAGE_VERSION_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    PIP_PACKAGES_FIELD_NUMBER: _ClassVar[int]
    NPM_PACKAGES_FIELD_NUMBER: _ClassVar[int]
    HAS_HOOKS_FIELD_NUMBER: _ClassVar[int]
    REQUIRES_GPU_FIELD_NUMBER: _ClassVar[int]
    name: str
    version: str
    language: str
    language_version: str
    description: str
    pip_packages: _containers.RepeatedScalarFieldContainer[str]
    npm_packages: _containers.RepeatedScalarFieldContainer[str]
    has_hooks: bool
    requires_gpu: bool
    def __init__(self, name: _Optional[str] = ..., version: _Optional[str] = ..., language: _Optional[str] = ..., language_version: _Optional[str] = ..., description: _Optional[str] = ..., pip_packages: _Optional[_Iterable[str]] = ..., npm_packages: _Optional[_Iterable[str]] = ..., has_hooks: bool = ..., requires_gpu: bool = ...) -> None: ...

class CreateNetworkReq(_message.Message):
    __slots__ = ("name", "cidr")
    NAME_FIELD_NUMBER: _ClassVar[int]
    CIDR_FIELD_NUMBER: _ClassVar[int]
    name: str
    cidr: str
    def __init__(self, name: _Optional[str] = ..., cidr: _Optional[str] = ...) -> None: ...

class CreateNetworkRes(_message.Message):
    __slots__ = ("name", "cidr", "bridge")
    NAME_FIELD_NUMBER: _ClassVar[int]
    CIDR_FIELD_NUMBER: _ClassVar[int]
    BRIDGE_FIELD_NUMBER: _ClassVar[int]
    name: str
    cidr: str
    bridge: str
    def __init__(self, name: _Optional[str] = ..., cidr: _Optional[str] = ..., bridge: _Optional[str] = ...) -> None: ...

class RemoveNetworkReq(_message.Message):
    __slots__ = ("name",)
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...

class RemoveNetworkRes(_message.Message):
    __slots__ = ("success", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    def __init__(self, success: bool = ..., message: _Optional[str] = ...) -> None: ...

class Network(_message.Message):
    __slots__ = ("name", "cidr", "bridge", "jobCount")
    NAME_FIELD_NUMBER: _ClassVar[int]
    CIDR_FIELD_NUMBER: _ClassVar[int]
    BRIDGE_FIELD_NUMBER: _ClassVar[int]
    JOBCOUNT_FIELD_NUMBER: _ClassVar[int]
    name: str
    cidr: str
    bridge: str
    jobCount: int
    def __init__(self, name: _Optional[str] = ..., cidr: _Optional[str] = ..., bridge: _Optional[str] = ..., jobCount: _Optional[int] = ...) -> None: ...

class Networks(_message.Message):
    __slots__ = ("networks",)
    NETWORKS_FIELD_NUMBER: _ClassVar[int]
    networks: _containers.RepeatedCompositeFieldContainer[Network]
    def __init__(self, networks: _Optional[_Iterable[_Union[Network, _Mapping]]] = ...) -> None: ...

class CreateVolumeReq(_message.Message):
    __slots__ = ("name", "size", "type")
    NAME_FIELD_NUMBER: _ClassVar[int]
    SIZE_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    name: str
    size: str
    type: str
    def __init__(self, name: _Optional[str] = ..., size: _Optional[str] = ..., type: _Optional[str] = ...) -> None: ...

class CreateVolumeRes(_message.Message):
    __slots__ = ("name", "size", "type", "path")
    NAME_FIELD_NUMBER: _ClassVar[int]
    SIZE_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    name: str
    size: str
    type: str
    path: str
    def __init__(self, name: _Optional[str] = ..., size: _Optional[str] = ..., type: _Optional[str] = ..., path: _Optional[str] = ...) -> None: ...

class RemoveVolumeReq(_message.Message):
    __slots__ = ("name",)
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...

class RemoveVolumeRes(_message.Message):
    __slots__ = ("success", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    def __init__(self, success: bool = ..., message: _Optional[str] = ...) -> None: ...

class Volume(_message.Message):
    __slots__ = ("name", "size", "type", "path", "createdTime", "jobCount")
    NAME_FIELD_NUMBER: _ClassVar[int]
    SIZE_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    CREATEDTIME_FIELD_NUMBER: _ClassVar[int]
    JOBCOUNT_FIELD_NUMBER: _ClassVar[int]
    name: str
    size: str
    type: str
    path: str
    createdTime: str
    jobCount: int
    def __init__(self, name: _Optional[str] = ..., size: _Optional[str] = ..., type: _Optional[str] = ..., path: _Optional[str] = ..., createdTime: _Optional[str] = ..., jobCount: _Optional[int] = ...) -> None: ...

class Volumes(_message.Message):
    __slots__ = ("volumes",)
    VOLUMES_FIELD_NUMBER: _ClassVar[int]
    volumes: _containers.RepeatedCompositeFieldContainer[Volume]
    def __init__(self, volumes: _Optional[_Iterable[_Union[Volume, _Mapping]]] = ...) -> None: ...

class SystemStatusRes(_message.Message):
    __slots__ = ("timestamp", "available", "host", "cpu", "memory", "disks", "networks", "io", "processes", "cloud", "server_version")
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    AVAILABLE_FIELD_NUMBER: _ClassVar[int]
    HOST_FIELD_NUMBER: _ClassVar[int]
    CPU_FIELD_NUMBER: _ClassVar[int]
    MEMORY_FIELD_NUMBER: _ClassVar[int]
    DISKS_FIELD_NUMBER: _ClassVar[int]
    NETWORKS_FIELD_NUMBER: _ClassVar[int]
    IO_FIELD_NUMBER: _ClassVar[int]
    PROCESSES_FIELD_NUMBER: _ClassVar[int]
    CLOUD_FIELD_NUMBER: _ClassVar[int]
    SERVER_VERSION_FIELD_NUMBER: _ClassVar[int]
    timestamp: str
    available: bool
    host: HostInfo
    cpu: CPUMetrics
    memory: MemoryMetrics
    disks: _containers.RepeatedCompositeFieldContainer[DiskMetrics]
    networks: _containers.RepeatedCompositeFieldContainer[NetworkMetrics]
    io: IOMetrics
    processes: ProcessMetrics
    cloud: CloudInfo
    server_version: ServerVersionInfo
    def __init__(self, timestamp: _Optional[str] = ..., available: bool = ..., host: _Optional[_Union[HostInfo, _Mapping]] = ..., cpu: _Optional[_Union[CPUMetrics, _Mapping]] = ..., memory: _Optional[_Union[MemoryMetrics, _Mapping]] = ..., disks: _Optional[_Iterable[_Union[DiskMetrics, _Mapping]]] = ..., networks: _Optional[_Iterable[_Union[NetworkMetrics, _Mapping]]] = ..., io: _Optional[_Union[IOMetrics, _Mapping]] = ..., processes: _Optional[_Union[ProcessMetrics, _Mapping]] = ..., cloud: _Optional[_Union[CloudInfo, _Mapping]] = ..., server_version: _Optional[_Union[ServerVersionInfo, _Mapping]] = ...) -> None: ...

class SystemMetricsRes(_message.Message):
    __slots__ = ("timestamp", "host", "cpu", "memory", "disks", "networks", "io", "processes", "cloud")
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    HOST_FIELD_NUMBER: _ClassVar[int]
    CPU_FIELD_NUMBER: _ClassVar[int]
    MEMORY_FIELD_NUMBER: _ClassVar[int]
    DISKS_FIELD_NUMBER: _ClassVar[int]
    NETWORKS_FIELD_NUMBER: _ClassVar[int]
    IO_FIELD_NUMBER: _ClassVar[int]
    PROCESSES_FIELD_NUMBER: _ClassVar[int]
    CLOUD_FIELD_NUMBER: _ClassVar[int]
    timestamp: str
    host: HostInfo
    cpu: CPUMetrics
    memory: MemoryMetrics
    disks: _containers.RepeatedCompositeFieldContainer[DiskMetrics]
    networks: _containers.RepeatedCompositeFieldContainer[NetworkMetrics]
    io: IOMetrics
    processes: ProcessMetrics
    cloud: CloudInfo
    def __init__(self, timestamp: _Optional[str] = ..., host: _Optional[_Union[HostInfo, _Mapping]] = ..., cpu: _Optional[_Union[CPUMetrics, _Mapping]] = ..., memory: _Optional[_Union[MemoryMetrics, _Mapping]] = ..., disks: _Optional[_Iterable[_Union[DiskMetrics, _Mapping]]] = ..., networks: _Optional[_Iterable[_Union[NetworkMetrics, _Mapping]]] = ..., io: _Optional[_Union[IOMetrics, _Mapping]] = ..., processes: _Optional[_Union[ProcessMetrics, _Mapping]] = ..., cloud: _Optional[_Union[CloudInfo, _Mapping]] = ...) -> None: ...

class StreamMetricsReq(_message.Message):
    __slots__ = ("intervalSeconds", "metricTypes")
    INTERVALSECONDS_FIELD_NUMBER: _ClassVar[int]
    METRICTYPES_FIELD_NUMBER: _ClassVar[int]
    intervalSeconds: int
    metricTypes: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, intervalSeconds: _Optional[int] = ..., metricTypes: _Optional[_Iterable[str]] = ...) -> None: ...

class HostInfo(_message.Message):
    __slots__ = ("hostname", "os", "platform", "platformFamily", "platformVersion", "kernelVersion", "kernelArch", "architecture", "cpuCount", "totalMemory", "bootTime", "uptime", "nodeId", "serverIPs", "macAddresses")
    HOSTNAME_FIELD_NUMBER: _ClassVar[int]
    OS_FIELD_NUMBER: _ClassVar[int]
    PLATFORM_FIELD_NUMBER: _ClassVar[int]
    PLATFORMFAMILY_FIELD_NUMBER: _ClassVar[int]
    PLATFORMVERSION_FIELD_NUMBER: _ClassVar[int]
    KERNELVERSION_FIELD_NUMBER: _ClassVar[int]
    KERNELARCH_FIELD_NUMBER: _ClassVar[int]
    ARCHITECTURE_FIELD_NUMBER: _ClassVar[int]
    CPUCOUNT_FIELD_NUMBER: _ClassVar[int]
    TOTALMEMORY_FIELD_NUMBER: _ClassVar[int]
    BOOTTIME_FIELD_NUMBER: _ClassVar[int]
    UPTIME_FIELD_NUMBER: _ClassVar[int]
    NODEID_FIELD_NUMBER: _ClassVar[int]
    SERVERIPS_FIELD_NUMBER: _ClassVar[int]
    MACADDRESSES_FIELD_NUMBER: _ClassVar[int]
    hostname: str
    os: str
    platform: str
    platformFamily: str
    platformVersion: str
    kernelVersion: str
    kernelArch: str
    architecture: str
    cpuCount: int
    totalMemory: int
    bootTime: str
    uptime: int
    nodeId: str
    serverIPs: _containers.RepeatedScalarFieldContainer[str]
    macAddresses: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, hostname: _Optional[str] = ..., os: _Optional[str] = ..., platform: _Optional[str] = ..., platformFamily: _Optional[str] = ..., platformVersion: _Optional[str] = ..., kernelVersion: _Optional[str] = ..., kernelArch: _Optional[str] = ..., architecture: _Optional[str] = ..., cpuCount: _Optional[int] = ..., totalMemory: _Optional[int] = ..., bootTime: _Optional[str] = ..., uptime: _Optional[int] = ..., nodeId: _Optional[str] = ..., serverIPs: _Optional[_Iterable[str]] = ..., macAddresses: _Optional[_Iterable[str]] = ...) -> None: ...

class CPUMetrics(_message.Message):
    __slots__ = ("cores", "usagePercent", "userTime", "systemTime", "idleTime", "ioWaitTime", "stealTime", "loadAverage", "perCoreUsage")
    CORES_FIELD_NUMBER: _ClassVar[int]
    USAGEPERCENT_FIELD_NUMBER: _ClassVar[int]
    USERTIME_FIELD_NUMBER: _ClassVar[int]
    SYSTEMTIME_FIELD_NUMBER: _ClassVar[int]
    IDLETIME_FIELD_NUMBER: _ClassVar[int]
    IOWAITTIME_FIELD_NUMBER: _ClassVar[int]
    STEALTIME_FIELD_NUMBER: _ClassVar[int]
    LOADAVERAGE_FIELD_NUMBER: _ClassVar[int]
    PERCOREUSAGE_FIELD_NUMBER: _ClassVar[int]
    cores: int
    usagePercent: float
    userTime: float
    systemTime: float
    idleTime: float
    ioWaitTime: float
    stealTime: float
    loadAverage: _containers.RepeatedScalarFieldContainer[float]
    perCoreUsage: _containers.RepeatedScalarFieldContainer[float]
    def __init__(self, cores: _Optional[int] = ..., usagePercent: _Optional[float] = ..., userTime: _Optional[float] = ..., systemTime: _Optional[float] = ..., idleTime: _Optional[float] = ..., ioWaitTime: _Optional[float] = ..., stealTime: _Optional[float] = ..., loadAverage: _Optional[_Iterable[float]] = ..., perCoreUsage: _Optional[_Iterable[float]] = ...) -> None: ...

class MemoryMetrics(_message.Message):
    __slots__ = ("totalBytes", "usedBytes", "freeBytes", "availableBytes", "usagePercent", "cachedBytes", "bufferedBytes", "swapTotal", "swapUsed", "swapFree")
    TOTALBYTES_FIELD_NUMBER: _ClassVar[int]
    USEDBYTES_FIELD_NUMBER: _ClassVar[int]
    FREEBYTES_FIELD_NUMBER: _ClassVar[int]
    AVAILABLEBYTES_FIELD_NUMBER: _ClassVar[int]
    USAGEPERCENT_FIELD_NUMBER: _ClassVar[int]
    CACHEDBYTES_FIELD_NUMBER: _ClassVar[int]
    BUFFEREDBYTES_FIELD_NUMBER: _ClassVar[int]
    SWAPTOTAL_FIELD_NUMBER: _ClassVar[int]
    SWAPUSED_FIELD_NUMBER: _ClassVar[int]
    SWAPFREE_FIELD_NUMBER: _ClassVar[int]
    totalBytes: int
    usedBytes: int
    freeBytes: int
    availableBytes: int
    usagePercent: float
    cachedBytes: int
    bufferedBytes: int
    swapTotal: int
    swapUsed: int
    swapFree: int
    def __init__(self, totalBytes: _Optional[int] = ..., usedBytes: _Optional[int] = ..., freeBytes: _Optional[int] = ..., availableBytes: _Optional[int] = ..., usagePercent: _Optional[float] = ..., cachedBytes: _Optional[int] = ..., bufferedBytes: _Optional[int] = ..., swapTotal: _Optional[int] = ..., swapUsed: _Optional[int] = ..., swapFree: _Optional[int] = ...) -> None: ...

class DiskMetrics(_message.Message):
    __slots__ = ("device", "mountPoint", "filesystem", "totalBytes", "usedBytes", "freeBytes", "usagePercent", "inodesTotal", "inodesUsed", "inodesFree", "inodesUsagePercent")
    DEVICE_FIELD_NUMBER: _ClassVar[int]
    MOUNTPOINT_FIELD_NUMBER: _ClassVar[int]
    FILESYSTEM_FIELD_NUMBER: _ClassVar[int]
    TOTALBYTES_FIELD_NUMBER: _ClassVar[int]
    USEDBYTES_FIELD_NUMBER: _ClassVar[int]
    FREEBYTES_FIELD_NUMBER: _ClassVar[int]
    USAGEPERCENT_FIELD_NUMBER: _ClassVar[int]
    INODESTOTAL_FIELD_NUMBER: _ClassVar[int]
    INODESUSED_FIELD_NUMBER: _ClassVar[int]
    INODESFREE_FIELD_NUMBER: _ClassVar[int]
    INODESUSAGEPERCENT_FIELD_NUMBER: _ClassVar[int]
    device: str
    mountPoint: str
    filesystem: str
    totalBytes: int
    usedBytes: int
    freeBytes: int
    usagePercent: float
    inodesTotal: int
    inodesUsed: int
    inodesFree: int
    inodesUsagePercent: float
    def __init__(self, device: _Optional[str] = ..., mountPoint: _Optional[str] = ..., filesystem: _Optional[str] = ..., totalBytes: _Optional[int] = ..., usedBytes: _Optional[int] = ..., freeBytes: _Optional[int] = ..., usagePercent: _Optional[float] = ..., inodesTotal: _Optional[int] = ..., inodesUsed: _Optional[int] = ..., inodesFree: _Optional[int] = ..., inodesUsagePercent: _Optional[float] = ...) -> None: ...

class NetworkMetrics(_message.Message):
    __slots__ = ("interface", "bytesReceived", "bytesSent", "packetsReceived", "packetsSent", "errorsIn", "errorsOut", "dropsIn", "dropsOut", "receiveRate", "transmitRate", "ipAddresses", "macAddress")
    INTERFACE_FIELD_NUMBER: _ClassVar[int]
    BYTESRECEIVED_FIELD_NUMBER: _ClassVar[int]
    BYTESSENT_FIELD_NUMBER: _ClassVar[int]
    PACKETSRECEIVED_FIELD_NUMBER: _ClassVar[int]
    PACKETSSENT_FIELD_NUMBER: _ClassVar[int]
    ERRORSIN_FIELD_NUMBER: _ClassVar[int]
    ERRORSOUT_FIELD_NUMBER: _ClassVar[int]
    DROPSIN_FIELD_NUMBER: _ClassVar[int]
    DROPSOUT_FIELD_NUMBER: _ClassVar[int]
    RECEIVERATE_FIELD_NUMBER: _ClassVar[int]
    TRANSMITRATE_FIELD_NUMBER: _ClassVar[int]
    IPADDRESSES_FIELD_NUMBER: _ClassVar[int]
    MACADDRESS_FIELD_NUMBER: _ClassVar[int]
    interface: str
    bytesReceived: int
    bytesSent: int
    packetsReceived: int
    packetsSent: int
    errorsIn: int
    errorsOut: int
    dropsIn: int
    dropsOut: int
    receiveRate: float
    transmitRate: float
    ipAddresses: _containers.RepeatedScalarFieldContainer[str]
    macAddress: str
    def __init__(self, interface: _Optional[str] = ..., bytesReceived: _Optional[int] = ..., bytesSent: _Optional[int] = ..., packetsReceived: _Optional[int] = ..., packetsSent: _Optional[int] = ..., errorsIn: _Optional[int] = ..., errorsOut: _Optional[int] = ..., dropsIn: _Optional[int] = ..., dropsOut: _Optional[int] = ..., receiveRate: _Optional[float] = ..., transmitRate: _Optional[float] = ..., ipAddresses: _Optional[_Iterable[str]] = ..., macAddress: _Optional[str] = ...) -> None: ...

class IOMetrics(_message.Message):
    __slots__ = ("totalReads", "totalWrites", "readBytes", "writeBytes", "readRate", "writeRate", "diskIO")
    TOTALREADS_FIELD_NUMBER: _ClassVar[int]
    TOTALWRITES_FIELD_NUMBER: _ClassVar[int]
    READBYTES_FIELD_NUMBER: _ClassVar[int]
    WRITEBYTES_FIELD_NUMBER: _ClassVar[int]
    READRATE_FIELD_NUMBER: _ClassVar[int]
    WRITERATE_FIELD_NUMBER: _ClassVar[int]
    DISKIO_FIELD_NUMBER: _ClassVar[int]
    totalReads: int
    totalWrites: int
    readBytes: int
    writeBytes: int
    readRate: float
    writeRate: float
    diskIO: _containers.RepeatedCompositeFieldContainer[DiskIOMetrics]
    def __init__(self, totalReads: _Optional[int] = ..., totalWrites: _Optional[int] = ..., readBytes: _Optional[int] = ..., writeBytes: _Optional[int] = ..., readRate: _Optional[float] = ..., writeRate: _Optional[float] = ..., diskIO: _Optional[_Iterable[_Union[DiskIOMetrics, _Mapping]]] = ...) -> None: ...

class DiskIOMetrics(_message.Message):
    __slots__ = ("device", "readsCompleted", "writesCompleted", "readBytes", "writeBytes", "readTime", "writeTime", "ioTime", "utilization")
    DEVICE_FIELD_NUMBER: _ClassVar[int]
    READSCOMPLETED_FIELD_NUMBER: _ClassVar[int]
    WRITESCOMPLETED_FIELD_NUMBER: _ClassVar[int]
    READBYTES_FIELD_NUMBER: _ClassVar[int]
    WRITEBYTES_FIELD_NUMBER: _ClassVar[int]
    READTIME_FIELD_NUMBER: _ClassVar[int]
    WRITETIME_FIELD_NUMBER: _ClassVar[int]
    IOTIME_FIELD_NUMBER: _ClassVar[int]
    UTILIZATION_FIELD_NUMBER: _ClassVar[int]
    device: str
    readsCompleted: int
    writesCompleted: int
    readBytes: int
    writeBytes: int
    readTime: int
    writeTime: int
    ioTime: int
    utilization: float
    def __init__(self, device: _Optional[str] = ..., readsCompleted: _Optional[int] = ..., writesCompleted: _Optional[int] = ..., readBytes: _Optional[int] = ..., writeBytes: _Optional[int] = ..., readTime: _Optional[int] = ..., writeTime: _Optional[int] = ..., ioTime: _Optional[int] = ..., utilization: _Optional[float] = ...) -> None: ...

class ProcessMetrics(_message.Message):
    __slots__ = ("totalProcesses", "runningProcesses", "sleepingProcesses", "stoppedProcesses", "zombieProcesses", "totalThreads", "topByCPU", "topByMemory")
    TOTALPROCESSES_FIELD_NUMBER: _ClassVar[int]
    RUNNINGPROCESSES_FIELD_NUMBER: _ClassVar[int]
    SLEEPINGPROCESSES_FIELD_NUMBER: _ClassVar[int]
    STOPPEDPROCESSES_FIELD_NUMBER: _ClassVar[int]
    ZOMBIEPROCESSES_FIELD_NUMBER: _ClassVar[int]
    TOTALTHREADS_FIELD_NUMBER: _ClassVar[int]
    TOPBYCPU_FIELD_NUMBER: _ClassVar[int]
    TOPBYMEMORY_FIELD_NUMBER: _ClassVar[int]
    totalProcesses: int
    runningProcesses: int
    sleepingProcesses: int
    stoppedProcesses: int
    zombieProcesses: int
    totalThreads: int
    topByCPU: _containers.RepeatedCompositeFieldContainer[ProcessInfo]
    topByMemory: _containers.RepeatedCompositeFieldContainer[ProcessInfo]
    def __init__(self, totalProcesses: _Optional[int] = ..., runningProcesses: _Optional[int] = ..., sleepingProcesses: _Optional[int] = ..., stoppedProcesses: _Optional[int] = ..., zombieProcesses: _Optional[int] = ..., totalThreads: _Optional[int] = ..., topByCPU: _Optional[_Iterable[_Union[ProcessInfo, _Mapping]]] = ..., topByMemory: _Optional[_Iterable[_Union[ProcessInfo, _Mapping]]] = ...) -> None: ...

class ProcessInfo(_message.Message):
    __slots__ = ("pid", "ppid", "name", "command", "cpuPercent", "memoryPercent", "memoryBytes", "status", "startTime", "user")
    PID_FIELD_NUMBER: _ClassVar[int]
    PPID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    COMMAND_FIELD_NUMBER: _ClassVar[int]
    CPUPERCENT_FIELD_NUMBER: _ClassVar[int]
    MEMORYPERCENT_FIELD_NUMBER: _ClassVar[int]
    MEMORYBYTES_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    STARTTIME_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    pid: int
    ppid: int
    name: str
    command: str
    cpuPercent: float
    memoryPercent: float
    memoryBytes: int
    status: str
    startTime: str
    user: str
    def __init__(self, pid: _Optional[int] = ..., ppid: _Optional[int] = ..., name: _Optional[str] = ..., command: _Optional[str] = ..., cpuPercent: _Optional[float] = ..., memoryPercent: _Optional[float] = ..., memoryBytes: _Optional[int] = ..., status: _Optional[str] = ..., startTime: _Optional[str] = ..., user: _Optional[str] = ...) -> None: ...

class CloudInfo(_message.Message):
    __slots__ = ("provider", "region", "zone", "instanceID", "instanceType", "hypervisorType", "metadata")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    PROVIDER_FIELD_NUMBER: _ClassVar[int]
    REGION_FIELD_NUMBER: _ClassVar[int]
    ZONE_FIELD_NUMBER: _ClassVar[int]
    INSTANCEID_FIELD_NUMBER: _ClassVar[int]
    INSTANCETYPE_FIELD_NUMBER: _ClassVar[int]
    HYPERVISORTYPE_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    provider: str
    region: str
    zone: str
    instanceID: str
    instanceType: str
    hypervisorType: str
    metadata: _containers.ScalarMap[str, str]
    def __init__(self, provider: _Optional[str] = ..., region: _Optional[str] = ..., zone: _Optional[str] = ..., instanceID: _Optional[str] = ..., instanceType: _Optional[str] = ..., hypervisorType: _Optional[str] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...

class ServerVersionInfo(_message.Message):
    __slots__ = ("version", "git_commit", "git_tag", "build_date", "component", "go_version", "platform", "proto_commit", "proto_tag")
    VERSION_FIELD_NUMBER: _ClassVar[int]
    GIT_COMMIT_FIELD_NUMBER: _ClassVar[int]
    GIT_TAG_FIELD_NUMBER: _ClassVar[int]
    BUILD_DATE_FIELD_NUMBER: _ClassVar[int]
    COMPONENT_FIELD_NUMBER: _ClassVar[int]
    GO_VERSION_FIELD_NUMBER: _ClassVar[int]
    PLATFORM_FIELD_NUMBER: _ClassVar[int]
    PROTO_COMMIT_FIELD_NUMBER: _ClassVar[int]
    PROTO_TAG_FIELD_NUMBER: _ClassVar[int]
    version: str
    git_commit: str
    git_tag: str
    build_date: str
    component: str
    go_version: str
    platform: str
    proto_commit: str
    proto_tag: str
    def __init__(self, version: _Optional[str] = ..., git_commit: _Optional[str] = ..., git_tag: _Optional[str] = ..., build_date: _Optional[str] = ..., component: _Optional[str] = ..., go_version: _Optional[str] = ..., platform: _Optional[str] = ..., proto_commit: _Optional[str] = ..., proto_tag: _Optional[str] = ...) -> None: ...

class RuntimesRes(_message.Message):
    __slots__ = ("runtimes",)
    RUNTIMES_FIELD_NUMBER: _ClassVar[int]
    runtimes: _containers.RepeatedCompositeFieldContainer[RuntimeInfo]
    def __init__(self, runtimes: _Optional[_Iterable[_Union[RuntimeInfo, _Mapping]]] = ...) -> None: ...

class RuntimeInfo(_message.Message):
    __slots__ = ("name", "language", "version", "description", "sizeBytes", "packages", "available", "requirements")
    NAME_FIELD_NUMBER: _ClassVar[int]
    LANGUAGE_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    SIZEBYTES_FIELD_NUMBER: _ClassVar[int]
    PACKAGES_FIELD_NUMBER: _ClassVar[int]
    AVAILABLE_FIELD_NUMBER: _ClassVar[int]
    REQUIREMENTS_FIELD_NUMBER: _ClassVar[int]
    name: str
    language: str
    version: str
    description: str
    sizeBytes: int
    packages: _containers.RepeatedScalarFieldContainer[str]
    available: bool
    requirements: RuntimeRequirements
    def __init__(self, name: _Optional[str] = ..., language: _Optional[str] = ..., version: _Optional[str] = ..., description: _Optional[str] = ..., sizeBytes: _Optional[int] = ..., packages: _Optional[_Iterable[str]] = ..., available: bool = ..., requirements: _Optional[_Union[RuntimeRequirements, _Mapping]] = ...) -> None: ...

class RuntimeRequirements(_message.Message):
    __slots__ = ("architectures", "gpu")
    ARCHITECTURES_FIELD_NUMBER: _ClassVar[int]
    GPU_FIELD_NUMBER: _ClassVar[int]
    architectures: _containers.RepeatedScalarFieldContainer[str]
    gpu: bool
    def __init__(self, architectures: _Optional[_Iterable[str]] = ..., gpu: bool = ...) -> None: ...

class RuntimeInfoReq(_message.Message):
    __slots__ = ("runtime",)
    RUNTIME_FIELD_NUMBER: _ClassVar[int]
    runtime: str
    def __init__(self, runtime: _Optional[str] = ...) -> None: ...

class RuntimeInfoRes(_message.Message):
    __slots__ = ("runtime", "found")
    RUNTIME_FIELD_NUMBER: _ClassVar[int]
    FOUND_FIELD_NUMBER: _ClassVar[int]
    runtime: RuntimeInfo
    found: bool
    def __init__(self, runtime: _Optional[_Union[RuntimeInfo, _Mapping]] = ..., found: bool = ...) -> None: ...

class RuntimeTestReq(_message.Message):
    __slots__ = ("runtime",)
    RUNTIME_FIELD_NUMBER: _ClassVar[int]
    runtime: str
    def __init__(self, runtime: _Optional[str] = ...) -> None: ...

class RuntimeTestRes(_message.Message):
    __slots__ = ("success", "output", "error", "exitCode")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    EXITCODE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    output: str
    error: str
    exitCode: int
    def __init__(self, success: bool = ..., output: _Optional[str] = ..., error: _Optional[str] = ..., exitCode: _Optional[int] = ...) -> None: ...

class RunJobRequest(_message.Message):
    __slots__ = ("name", "command", "args", "maxCpu", "cpuCores", "maxMemory", "maxIobps", "uploads", "schedule", "network", "volumes", "runtime", "workDir", "environment", "secret_environment", "gpu_count", "gpu_memory_mb")
    class EnvironmentEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    class SecretEnvironmentEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    NAME_FIELD_NUMBER: _ClassVar[int]
    COMMAND_FIELD_NUMBER: _ClassVar[int]
    ARGS_FIELD_NUMBER: _ClassVar[int]
    MAXCPU_FIELD_NUMBER: _ClassVar[int]
    CPUCORES_FIELD_NUMBER: _ClassVar[int]
    MAXMEMORY_FIELD_NUMBER: _ClassVar[int]
    MAXIOBPS_FIELD_NUMBER: _ClassVar[int]
    UPLOADS_FIELD_NUMBER: _ClassVar[int]
    SCHEDULE_FIELD_NUMBER: _ClassVar[int]
    NETWORK_FIELD_NUMBER: _ClassVar[int]
    VOLUMES_FIELD_NUMBER: _ClassVar[int]
    RUNTIME_FIELD_NUMBER: _ClassVar[int]
    WORKDIR_FIELD_NUMBER: _ClassVar[int]
    ENVIRONMENT_FIELD_NUMBER: _ClassVar[int]
    SECRET_ENVIRONMENT_FIELD_NUMBER: _ClassVar[int]
    GPU_COUNT_FIELD_NUMBER: _ClassVar[int]
    GPU_MEMORY_MB_FIELD_NUMBER: _ClassVar[int]
    name: str
    command: str
    args: _containers.RepeatedScalarFieldContainer[str]
    maxCpu: int
    cpuCores: str
    maxMemory: int
    maxIobps: int
    uploads: _containers.RepeatedCompositeFieldContainer[FileUpload]
    schedule: str
    network: str
    volumes: _containers.RepeatedScalarFieldContainer[str]
    runtime: str
    workDir: str
    environment: _containers.ScalarMap[str, str]
    secret_environment: _containers.ScalarMap[str, str]
    gpu_count: int
    gpu_memory_mb: int
    def __init__(self, name: _Optional[str] = ..., command: _Optional[str] = ..., args: _Optional[_Iterable[str]] = ..., maxCpu: _Optional[int] = ..., cpuCores: _Optional[str] = ..., maxMemory: _Optional[int] = ..., maxIobps: _Optional[int] = ..., uploads: _Optional[_Iterable[_Union[FileUpload, _Mapping]]] = ..., schedule: _Optional[str] = ..., network: _Optional[str] = ..., volumes: _Optional[_Iterable[str]] = ..., runtime: _Optional[str] = ..., workDir: _Optional[str] = ..., environment: _Optional[_Mapping[str, str]] = ..., secret_environment: _Optional[_Mapping[str, str]] = ..., gpu_count: _Optional[int] = ..., gpu_memory_mb: _Optional[int] = ...) -> None: ...

class RunJobResponse(_message.Message):
    __slots__ = ("jobUuid", "status", "command", "args", "maxCpu", "cpuCores", "maxMemory", "maxIobps", "startTime", "endTime", "exitCode", "scheduledTime")
    JOBUUID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    COMMAND_FIELD_NUMBER: _ClassVar[int]
    ARGS_FIELD_NUMBER: _ClassVar[int]
    MAXCPU_FIELD_NUMBER: _ClassVar[int]
    CPUCORES_FIELD_NUMBER: _ClassVar[int]
    MAXMEMORY_FIELD_NUMBER: _ClassVar[int]
    MAXIOBPS_FIELD_NUMBER: _ClassVar[int]
    STARTTIME_FIELD_NUMBER: _ClassVar[int]
    ENDTIME_FIELD_NUMBER: _ClassVar[int]
    EXITCODE_FIELD_NUMBER: _ClassVar[int]
    SCHEDULEDTIME_FIELD_NUMBER: _ClassVar[int]
    jobUuid: str
    status: str
    command: str
    args: _containers.RepeatedScalarFieldContainer[str]
    maxCpu: int
    cpuCores: str
    maxMemory: int
    maxIobps: int
    startTime: str
    endTime: str
    exitCode: int
    scheduledTime: str
    def __init__(self, jobUuid: _Optional[str] = ..., status: _Optional[str] = ..., command: _Optional[str] = ..., args: _Optional[_Iterable[str]] = ..., maxCpu: _Optional[int] = ..., cpuCores: _Optional[str] = ..., maxMemory: _Optional[int] = ..., maxIobps: _Optional[int] = ..., startTime: _Optional[str] = ..., endTime: _Optional[str] = ..., exitCode: _Optional[int] = ..., scheduledTime: _Optional[str] = ...) -> None: ...

class Timestamp(_message.Message):
    __slots__ = ("seconds", "nanos")
    SECONDS_FIELD_NUMBER: _ClassVar[int]
    NANOS_FIELD_NUMBER: _ClassVar[int]
    seconds: int
    nanos: int
    def __init__(self, seconds: _Optional[int] = ..., nanos: _Optional[int] = ...) -> None: ...

class RuntimeRemoveReq(_message.Message):
    __slots__ = ("runtime",)
    RUNTIME_FIELD_NUMBER: _ClassVar[int]
    runtime: str
    def __init__(self, runtime: _Optional[str] = ...) -> None: ...

class RuntimeRemoveRes(_message.Message):
    __slots__ = ("success", "message", "freedSpaceBytes")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    FREEDSPACEBYTES_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    freedSpaceBytes: int
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., freedSpaceBytes: _Optional[int] = ...) -> None: ...

class StreamJobMetricsRequest(_message.Message):
    __slots__ = ("job_uuid",)
    JOB_UUID_FIELD_NUMBER: _ClassVar[int]
    job_uuid: str
    def __init__(self, job_uuid: _Optional[str] = ...) -> None: ...

class GetJobMetricsRequest(_message.Message):
    __slots__ = ("job_uuid", "start_time", "end_time", "limit")
    JOB_UUID_FIELD_NUMBER: _ClassVar[int]
    START_TIME_FIELD_NUMBER: _ClassVar[int]
    END_TIME_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    job_uuid: str
    start_time: int
    end_time: int
    limit: int
    def __init__(self, job_uuid: _Optional[str] = ..., start_time: _Optional[int] = ..., end_time: _Optional[int] = ..., limit: _Optional[int] = ...) -> None: ...

class JobMetricsEvent(_message.Message):
    __slots__ = ("timestamp", "job_id", "cpu_percent", "memory_bytes", "memory_limit", "disk_read_bytes", "disk_write_bytes", "net_recv_bytes", "net_sent_bytes", "gpu_percent", "gpu_memory_bytes")
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    CPU_PERCENT_FIELD_NUMBER: _ClassVar[int]
    MEMORY_BYTES_FIELD_NUMBER: _ClassVar[int]
    MEMORY_LIMIT_FIELD_NUMBER: _ClassVar[int]
    DISK_READ_BYTES_FIELD_NUMBER: _ClassVar[int]
    DISK_WRITE_BYTES_FIELD_NUMBER: _ClassVar[int]
    NET_RECV_BYTES_FIELD_NUMBER: _ClassVar[int]
    NET_SENT_BYTES_FIELD_NUMBER: _ClassVar[int]
    GPU_PERCENT_FIELD_NUMBER: _ClassVar[int]
    GPU_MEMORY_BYTES_FIELD_NUMBER: _ClassVar[int]
    timestamp: int
    job_id: str
    cpu_percent: float
    memory_bytes: int
    memory_limit: int
    disk_read_bytes: int
    disk_write_bytes: int
    net_recv_bytes: int
    net_sent_bytes: int
    gpu_percent: float
    gpu_memory_bytes: int
    def __init__(self, timestamp: _Optional[int] = ..., job_id: _Optional[str] = ..., cpu_percent: _Optional[float] = ..., memory_bytes: _Optional[int] = ..., memory_limit: _Optional[int] = ..., disk_read_bytes: _Optional[int] = ..., disk_write_bytes: _Optional[int] = ..., net_recv_bytes: _Optional[int] = ..., net_sent_bytes: _Optional[int] = ..., gpu_percent: _Optional[float] = ..., gpu_memory_bytes: _Optional[int] = ...) -> None: ...

class StreamJobTelematicsRequest(_message.Message):
    __slots__ = ("job_uuid", "types")
    JOB_UUID_FIELD_NUMBER: _ClassVar[int]
    TYPES_FIELD_NUMBER: _ClassVar[int]
    job_uuid: str
    types: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, job_uuid: _Optional[str] = ..., types: _Optional[_Iterable[str]] = ...) -> None: ...

class GetJobTelematicsRequest(_message.Message):
    __slots__ = ("job_uuid", "types", "start_time", "end_time", "limit")
    JOB_UUID_FIELD_NUMBER: _ClassVar[int]
    TYPES_FIELD_NUMBER: _ClassVar[int]
    START_TIME_FIELD_NUMBER: _ClassVar[int]
    END_TIME_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    job_uuid: str
    types: _containers.RepeatedScalarFieldContainer[str]
    start_time: int
    end_time: int
    limit: int
    def __init__(self, job_uuid: _Optional[str] = ..., types: _Optional[_Iterable[str]] = ..., start_time: _Optional[int] = ..., end_time: _Optional[int] = ..., limit: _Optional[int] = ...) -> None: ...

class TelematicsEvent(_message.Message):
    __slots__ = ("timestamp", "job_id", "type", "exec", "connect", "accept", "file", "mmap", "mprotect", "socket_data")
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    EXEC_FIELD_NUMBER: _ClassVar[int]
    CONNECT_FIELD_NUMBER: _ClassVar[int]
    ACCEPT_FIELD_NUMBER: _ClassVar[int]
    FILE_FIELD_NUMBER: _ClassVar[int]
    MMAP_FIELD_NUMBER: _ClassVar[int]
    MPROTECT_FIELD_NUMBER: _ClassVar[int]
    SOCKET_DATA_FIELD_NUMBER: _ClassVar[int]
    timestamp: int
    job_id: str
    type: str
    exec: TelematicsExecData
    connect: TelematicsConnectData
    accept: TelematicsAcceptData
    file: TelematicsFileData
    mmap: TelematicsMmapData
    mprotect: TelematicsMprotectData
    socket_data: TelematicsSocketDataData
    def __init__(self, timestamp: _Optional[int] = ..., job_id: _Optional[str] = ..., type: _Optional[str] = ..., exec: _Optional[_Union[TelematicsExecData, _Mapping]] = ..., connect: _Optional[_Union[TelematicsConnectData, _Mapping]] = ..., accept: _Optional[_Union[TelematicsAcceptData, _Mapping]] = ..., file: _Optional[_Union[TelematicsFileData, _Mapping]] = ..., mmap: _Optional[_Union[TelematicsMmapData, _Mapping]] = ..., mprotect: _Optional[_Union[TelematicsMprotectData, _Mapping]] = ..., socket_data: _Optional[_Union[TelematicsSocketDataData, _Mapping]] = ...) -> None: ...

class TelematicsExecData(_message.Message):
    __slots__ = ("pid", "ppid", "binary", "args", "exit_code")
    PID_FIELD_NUMBER: _ClassVar[int]
    PPID_FIELD_NUMBER: _ClassVar[int]
    BINARY_FIELD_NUMBER: _ClassVar[int]
    ARGS_FIELD_NUMBER: _ClassVar[int]
    EXIT_CODE_FIELD_NUMBER: _ClassVar[int]
    pid: int
    ppid: int
    binary: str
    args: _containers.RepeatedScalarFieldContainer[str]
    exit_code: int
    def __init__(self, pid: _Optional[int] = ..., ppid: _Optional[int] = ..., binary: _Optional[str] = ..., args: _Optional[_Iterable[str]] = ..., exit_code: _Optional[int] = ...) -> None: ...

class TelematicsConnectData(_message.Message):
    __slots__ = ("pid", "dst_addr", "dst_port", "protocol", "src_addr", "src_port")
    PID_FIELD_NUMBER: _ClassVar[int]
    DST_ADDR_FIELD_NUMBER: _ClassVar[int]
    DST_PORT_FIELD_NUMBER: _ClassVar[int]
    PROTOCOL_FIELD_NUMBER: _ClassVar[int]
    SRC_ADDR_FIELD_NUMBER: _ClassVar[int]
    SRC_PORT_FIELD_NUMBER: _ClassVar[int]
    pid: int
    dst_addr: str
    dst_port: int
    protocol: str
    src_addr: str
    src_port: int
    def __init__(self, pid: _Optional[int] = ..., dst_addr: _Optional[str] = ..., dst_port: _Optional[int] = ..., protocol: _Optional[str] = ..., src_addr: _Optional[str] = ..., src_port: _Optional[int] = ...) -> None: ...

class TelematicsAcceptData(_message.Message):
    __slots__ = ("pid", "src_addr", "src_port", "dst_addr", "dst_port", "protocol")
    PID_FIELD_NUMBER: _ClassVar[int]
    SRC_ADDR_FIELD_NUMBER: _ClassVar[int]
    SRC_PORT_FIELD_NUMBER: _ClassVar[int]
    DST_ADDR_FIELD_NUMBER: _ClassVar[int]
    DST_PORT_FIELD_NUMBER: _ClassVar[int]
    PROTOCOL_FIELD_NUMBER: _ClassVar[int]
    pid: int
    src_addr: str
    src_port: int
    dst_addr: str
    dst_port: int
    protocol: str
    def __init__(self, pid: _Optional[int] = ..., src_addr: _Optional[str] = ..., src_port: _Optional[int] = ..., dst_addr: _Optional[str] = ..., dst_port: _Optional[int] = ..., protocol: _Optional[str] = ...) -> None: ...

class TelematicsFileData(_message.Message):
    __slots__ = ("pid", "path", "operation", "bytes", "flags")
    PID_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    BYTES_FIELD_NUMBER: _ClassVar[int]
    FLAGS_FIELD_NUMBER: _ClassVar[int]
    pid: int
    path: str
    operation: str
    bytes: int
    flags: int
    def __init__(self, pid: _Optional[int] = ..., path: _Optional[str] = ..., operation: _Optional[str] = ..., bytes: _Optional[int] = ..., flags: _Optional[int] = ...) -> None: ...

class TelematicsMmapData(_message.Message):
    __slots__ = ("pid", "addr", "length", "prot", "flags", "file_path")
    PID_FIELD_NUMBER: _ClassVar[int]
    ADDR_FIELD_NUMBER: _ClassVar[int]
    LENGTH_FIELD_NUMBER: _ClassVar[int]
    PROT_FIELD_NUMBER: _ClassVar[int]
    FLAGS_FIELD_NUMBER: _ClassVar[int]
    FILE_PATH_FIELD_NUMBER: _ClassVar[int]
    pid: int
    addr: int
    length: int
    prot: int
    flags: int
    file_path: str
    def __init__(self, pid: _Optional[int] = ..., addr: _Optional[int] = ..., length: _Optional[int] = ..., prot: _Optional[int] = ..., flags: _Optional[int] = ..., file_path: _Optional[str] = ...) -> None: ...

class TelematicsMprotectData(_message.Message):
    __slots__ = ("pid", "addr", "length", "prot")
    PID_FIELD_NUMBER: _ClassVar[int]
    ADDR_FIELD_NUMBER: _ClassVar[int]
    LENGTH_FIELD_NUMBER: _ClassVar[int]
    PROT_FIELD_NUMBER: _ClassVar[int]
    pid: int
    addr: int
    length: int
    prot: int
    def __init__(self, pid: _Optional[int] = ..., addr: _Optional[int] = ..., length: _Optional[int] = ..., prot: _Optional[int] = ...) -> None: ...

class TelematicsSocketDataData(_message.Message):
    __slots__ = ("pid", "direction", "dst_addr", "dst_port", "src_addr", "src_port", "protocol", "bytes")
    PID_FIELD_NUMBER: _ClassVar[int]
    DIRECTION_FIELD_NUMBER: _ClassVar[int]
    DST_ADDR_FIELD_NUMBER: _ClassVar[int]
    DST_PORT_FIELD_NUMBER: _ClassVar[int]
    SRC_ADDR_FIELD_NUMBER: _ClassVar[int]
    SRC_PORT_FIELD_NUMBER: _ClassVar[int]
    PROTOCOL_FIELD_NUMBER: _ClassVar[int]
    BYTES_FIELD_NUMBER: _ClassVar[int]
    pid: int
    direction: str
    dst_addr: str
    dst_port: int
    src_addr: str
    src_port: int
    protocol: str
    bytes: int
    def __init__(self, pid: _Optional[int] = ..., direction: _Optional[str] = ..., dst_addr: _Optional[str] = ..., dst_port: _Optional[int] = ..., src_addr: _Optional[str] = ..., src_port: _Optional[int] = ..., protocol: _Optional[str] = ..., bytes: _Optional[int] = ...) -> None: ...
