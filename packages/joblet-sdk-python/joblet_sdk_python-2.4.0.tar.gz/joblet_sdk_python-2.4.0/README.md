# Joblet Python SDK

The official Python SDK for [Joblet](https://github.com/ehsaniara/joblet) - a distributed job orchestration system with GPU support.

## Installation

```bash
pip install joblet-sdk-python
```

## Quick Start

```python
from joblet import JobletClient

# Connect to your Joblet server
with JobletClient(
    host="your-joblet-server.com",
    port=50051,
    ca_cert_path="ca.pem",
    client_cert_path="client.pem",
    client_key_path="client.key"
) as client:
    # Run a simple job
    job = client.jobs.run_job(
        command="echo",
        args=["Hello, Joblet!"],
        name="my-first-job"
    )
    print(f"Job started: {job['job_uuid']}")
```

## Configuration

Create `~/.rnx/rnx-config.yml`:

```yaml
version: "3.0"
nodes:
  default:
    address: "your-joblet-server:50051"  # Required: Joblet service endpoint
    nodeId: "node-001"  # Optional: unique identifier for this node
    cert: |
      -----BEGIN CERTIFICATE-----
      # Your client certificate
      -----END CERTIFICATE-----
    key: |
      -----BEGIN PRIVATE KEY-----
      # Your client private key
      -----END PRIVATE KEY-----
    ca: |
      -----BEGIN CERTIFICATE-----
      # Your CA certificate
      -----END CERTIFICATE-----
```

**Configuration Fields:**
- `address` - **Required**: Joblet service endpoint (port 50051)
  - Handles all operations: job execution, logs, metrics, and resource management
  - Historical data is handled internally via IPC
- `nodeId` - Optional: Unique identifier for the node
- `cert` - **Required**: Client certificate for mTLS authentication
- `key` - **Required**: Client private key for mTLS authentication
- `ca` - **Required**: CA certificate for server verification

**Note**: Joblet runs as a unified Linux systemd service on port 50051. The server handles historical data internally via IPC to the persist subprocess. See the [Joblet Installation Guide](https://github.com/ehsaniara/joblet/blob/main/docs/INSTALLATION.md) for server setup.

## GPU Support

```python
# Run GPU-accelerated job
job = client.jobs.run_job(
    command="nvidia-smi",
    name="gpu-job",
    gpu_count=1,
    gpu_memory_mb=4096,
    runtime="python-3.11-ml"
)
```

## What You Can Do

### Run Jobs Anywhere

```python
# Run compute-intensive tasks on remote servers
job = client.jobs.run_job(
    command="python",
    args=["train_model.py"],
    max_cpu=800,  # 8 cores
    max_memory=16384,  # 16GB
    gpu_count=2
)
```

### Stream Logs in Real-Time

```python
# Get complete logs from any job (running or completed)
for chunk in client.jobs.get_job_logs(job['job_uuid']):
    print(chunk.decode('utf-8'), end='', flush=True)
```

### Get Job Metrics

```python
# Stream live metrics for a running job
for metric in client.jobs.stream_job_metrics(job_uuid):
    print(f"CPU: {metric['cpu_percent']:.2f}%")
    print(f"Memory: {metric['memory_bytes'] / 1e9:.2f} GB")

# Get historical metrics for a completed job
for metric in client.jobs.get_job_metrics(job_uuid):
    print(f"CPU: {metric['cpu_percent']:.2f}%")
```

### Get eBPF Telematics

```python
# Stream live security events for a running job
for event in client.jobs.stream_job_telematics(job_uuid, ["exec", "connect"]):
    if event['type'] == 'exec':
        print(f"EXEC: {event['exec']['binary']} {event['exec']['args']}")
    elif event['type'] == 'connect':
        conn = event['connect']
        print(f"CONNECT: {conn['dst_addr']}:{conn['dst_port']}")

# Get historical telematics events for a completed job
for event in client.jobs.get_job_telematics(job_uuid):
    print(f"Event: {event['type']} at {event['timestamp']}")
```

### Manage Resources

```python
# Create isolated networks and persistent storage
network = client.networks.create_network("ml-net", "10.0.1.0/24")
volume = client.volumes.create_volume("data", "100GB")

# Use in jobs
job = client.jobs.run_job(
    command="python",
    args=["process_data.py"],
    network="ml-net",
    volumes=["data:/data"]
)
```

### Monitor System Health

```python
# Get real-time system metrics
for metrics in client.monitoring.stream_system_metrics(interval_seconds=5):
    cpu = metrics['cpu']['usage_percent']
    memory = metrics['memory']['usage_percent']
    print(f"System: CPU {cpu:.1f}%, Memory {memory:.1f}%")
```

## API Reference

### Jobs
- `client.jobs.run_job()` - Execute a job
- `client.jobs.cancel_job()` - Cancel a scheduled job
- `client.jobs.stop_job()` - Stop a running job
- `client.jobs.get_job_status()` - Get job status
- `client.jobs.get_job_logs()` - **Smart log streaming** (historical + live)
- `client.jobs.stream_live_logs()` - Live-only log streaming

### Metrics & Telematics
- `client.jobs.stream_job_metrics()` - Stream live metrics for running job
- `client.jobs.get_job_metrics()` - Get historical metrics for completed job
- `client.jobs.stream_job_telematics()` - Stream live eBPF events (exec, connect, accept, file, mmap, mprotect)
- `client.jobs.get_job_telematics()` - Get historical eBPF events

### Resources
- `client.networks` - Network management
- `client.volumes` - Storage management
- `client.monitoring` - System monitoring
- `client.runtimes` - Runtime environments

### Runtimes
- `client.runtimes.list_runtimes()` - List available runtimes
- `client.runtimes.get_runtime_info()` - Get runtime details
- `client.runtimes.build_runtime()` - Build runtime from YAML (with OverlayFS isolation)
- `client.runtimes.validate_runtime_yaml()` - Validate runtime YAML without building
- `client.runtimes.remove_runtime()` - Remove a runtime

For complete API documentation, see [docs/API_REFERENCE.md](docs/API_REFERENCE.md)

## Building Runtimes

Build custom runtimes with isolated package installation:

```python
# Define a runtime specification
yaml_content = '''
name: python-3.11-ml
version: "1.0.0"
language: python
description: Python 3.11 with ML packages
base_packages:
  - python3.11
  - python3.11-venv
pip_packages:
  - numpy
  - pandas
  - scikit-learn
'''

# Build with streaming progress
for event in client.runtimes.build_runtime(yaml_content, verbose=True):
    if "phase" in event:
        phase = event["phase"]
        print(f"[{phase['phase_number']}/{phase['total_phases']}] {phase['phase_name']}")
    elif "log" in event:
        print(event["log"]["message"])
    elif "result" in event:
        result = event["result"]
        if result["success"]:
            print(f"Runtime built: {result['runtime_path']}")
        else:
            print(f"Build failed: {result['message']}")
```

**Note:** Runtime builds use OverlayFS-based chroot isolation, ensuring the host system is never modified during package installation. See [Joblet Runtime Documentation](https://github.com/ehsaniara/joblet/blob/main/docs/RUNTIME_DESIGN.md) for details.

## Development

### Setup

```bash
# Clone and setup
git clone https://github.com/ehsaniara/joblet-sdk-python.git
cd joblet-sdk-python

# Install development dependencies (editable mode)
make dev

# Or manually:
pip install -e .[dev]
pre-commit install
```

### Testing

```bash
# Run tests with coverage
make test

# Run linting (exactly what CI runs)
make lint

# IMPORTANT: Test package installation before release (CI-like)
make test-package
```

### Why `make test-package` is Important

**Problem**: Editable installs (`pip install -e .`) can mask packaging issues. Your local tests may pass but CI/production installs may fail.

**Solution**: Before committing or releasing, run:
```bash
make test-package
```

This command:
1. Uninstalls the editable version
2. Builds a clean package
3. Installs it like CI and end-users will
4. Runs all tests against the installed package
5. Catches issues like missing `__init__.py`, incorrect package structure, etc.

After testing, restore editable install:
```bash
pip install -e .[dev]
```

### Other Commands

```bash
# Build distribution packages
make build

# Regenerate protobuf files
make proto

# Clean build artifacts
make clean
```

## Examples

See the `examples/` directory for hands-on examples:

| Example | Description |
|---------|-------------|
| [01_basic_usage](examples/01_basic_usage/) | Running jobs, checking status, getting logs |
| [02_advanced_features](examples/02_advanced_features/) | Resource limits, GPUs, networks, volumes |
| [03_streaming_logs](examples/03_streaming_logs/) | Real-time log streaming |
| [04_historical_logs_metrics](examples/04_historical_logs_metrics/) | Logs and metrics from completed jobs |
| [05_smart_log_streaming](examples/05_smart_log_streaming/) | Automatic historical + live log handling |
| [06_long_running_job](examples/06_long_running_job/) | Managing long-duration jobs |
| [07_file_uploads_and_dependencies](examples/07_file_uploads_and_dependencies/) | File uploads and Python dependencies |

Each example has its own README with detailed explanations.

## Related Projects

- **[Joblet](https://github.com/ehsaniara/joblet)** - Main orchestration system (server-side)
- **[joblet-proto](https://github.com/ehsaniara/joblet-proto)** - Protocol Buffer definitions
- **rnx** - Official CLI tool (included in Joblet repo)

## License

MIT License - see LICENSE file for details.
