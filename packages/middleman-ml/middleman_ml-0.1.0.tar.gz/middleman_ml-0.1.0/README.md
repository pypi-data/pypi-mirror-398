# Middleman Python SDK

Python SDK and CLI for the Middleman ML Training Platform.

## Installation

```bash
pip install middleman-ml
```

## Quick Start

### CLI Usage

Configure your API key:

```bash
middleman auth
# Enter your API key when prompted
```

Or set the environment variable:

```bash
export MIDDLEMAN_API_KEY=mdlm_your_api_key_here
```

Create a training job:

```bash
middleman jobs create /scripts/train.py /data/dataset \
  --name "My Training Run" \
  --gpu a100 \
  --gpu-count 2 \
  --framework pytorch \
  --max-hours 8
```

Monitor your job:

```bash
middleman jobs watch <job-id>
```

Check your balance:

```bash
middleman billing balance
```

### Python SDK Usage

```python
from middleman import MiddlemanClient

# Initialize client
client = MiddlemanClient(api_key="mdlm_...")

# Create a job
job = client.create_job(
    name="ResNet Training",
    script_path="/scripts/train.py",
    input_data_path="/data/imagenet",
    gpu_type="a100",
    gpu_count=4,
    framework="pytorch",
    max_runtime_hours=24,
)

print(f"Job {job.id} created, queue position: {job.queue_position}")

# Wait for completion
result = client.wait_for_job(job.id)
print(f"Job finished with status: {result.status}")

# Check balance
balance = client.get_balance()
print(f"Available credits: {balance.available}")
```

## CLI Commands

### Authentication

```bash
middleman auth [API_KEY]     # Configure API key
middleman whoami             # Show account info
```

### Jobs

```bash
middleman jobs list          # List jobs
middleman jobs create        # Create a job
middleman jobs status <id>   # Get job details
middleman jobs cancel <id>   # Cancel a job
middleman jobs pause <id>    # Pause a running job
middleman jobs resume <id>   # Resume a paused job
middleman jobs logs <id>     # View job logs
middleman jobs watch <id>    # Watch until completion
```

### Billing

```bash
middleman billing balance    # Show credit balance
middleman billing packages   # Show credit packages
middleman billing history    # Transaction history
```

### Data

```bash
middleman data upload <file>          # Upload a file
middleman data download-url <job-id>  # Get download URL
```

### API Keys

```bash
middleman keys list           # List API keys
middleman keys create <name>  # Create new key
middleman keys revoke <id>    # Revoke a key
```

## SDK Reference

### MiddlemanClient

```python
from middleman import MiddlemanClient

client = MiddlemanClient(
    api_key="mdlm_...",           # Or use MIDDLEMAN_API_KEY env var
    base_url="https://...",       # Optional, defaults to production
    timeout=30.0,                 # Request timeout in seconds
)
```

### Jobs API

```python
# List jobs
jobs, total = client.list_jobs(status="running", limit=20)

# Get job details
job = client.get_job("job-uuid")

# Create job
response = client.create_job(
    script_path="/scripts/train.py",
    input_data_path="/data/dataset",
    name="My Job",
    gpu_type="a100",      # t4, v100, a100
    gpu_count=1,          # 1-8
    framework="pytorch",  # pytorch, tensorflow, jax
    requirements_file="/scripts/requirements.txt",
    checkpoint_frequency=10,
    max_runtime_hours=4,
    environment_variables={"WANDB_API_KEY": "..."},
)

# Control jobs
client.cancel_job("job-uuid")
client.pause_job("job-uuid")
client.resume_job("job-uuid")

# Wait for completion
final_job = client.wait_for_job("job-uuid", timeout=3600)

# Stream status updates
for job in client.stream_job_status("job-uuid"):
    print(f"Epoch {job.current_epoch}, Loss: {job.current_loss}")
    if job.is_terminal:
        break

# Get logs
logs = client.get_job_logs("job-uuid")
```

### Billing API

```python
# Get balance
balance = client.get_balance()
print(f"Available: {balance.available} credits")

# List packages
packages = client.get_packages()

# Transaction history
transactions, total = client.get_transactions(limit=50)
```

### Data API

```python
# Upload a file
blob_path = client.upload_file("/local/path/data.zip", job_id="job-uuid")

# Get download URL
download = client.get_download_url("job-uuid", path="outputs/model.pt")
print(download.download_url)
```

### API Keys

```python
# List keys
keys = client.list_api_keys()

# Create key
key_info, full_key = client.create_api_key(
    name="CI/CD Pipeline",
    scopes=["read", "write"],
    expires_in_days=90,
)
print(f"Key: {full_key}")  # Only shown once!

# Revoke key
client.revoke_api_key("key-uuid")
```

## GPU Types and Pricing

| GPU Type | VRAM | Credits/Hour |
|----------|------|--------------|
| T4       | 16GB | 10           |
| V100     | 32GB | 25           |
| A100     | 80GB | 50           |

## Environment Variables

- `MIDDLEMAN_API_KEY` - Your API key
- `MIDDLEMAN_API_URL` - Custom API URL (optional)

## License

MIT
