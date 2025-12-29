# Middleman ML SDK

Python SDK for the Middleman GPU compute platform.

## Installation

```bash
pip install middleman-ml
```

## Quick Start

```python
from middleman import MiddlemanClient

client = MiddlemanClient(api_key="mdlm_...")

# Create a training job
job = client.create_job(
    name="bert-training",
    gpu_type="a100",
    script="train.py",
    requirements=["torch", "transformers"]
)

# Monitor progress
client.wait_for_job(job.id)

# Check your balance
balance = client.get_balance()
print(f"Remaining credits: {balance.credits}")
```

## Features

- **Job Management**: Create, list, cancel, pause, resume jobs
- **Real-time Logs**: Stream training logs as they happen
- **File Uploads**: Upload datasets and scripts
- **Billing**: Check balance, view transactions
- **Webhooks**: Get notified on job status changes

## GPU Options

| GPU | Credits/hr | Best For |
|-----|------------|----------|
| T4 | 50 | Inference, small models |
| A100 | 350 | Large models, fast training |
| H100 | 600 | Maximum performance |

## Documentation

Full docs at [docs.middleman.run](https://docs.middleman.run)

## Support

- Email: support@middleman.run
- GitHub: [github.com/mkshepherd1/Middleman](https://github.com/mkshepherd1/Middleman)
