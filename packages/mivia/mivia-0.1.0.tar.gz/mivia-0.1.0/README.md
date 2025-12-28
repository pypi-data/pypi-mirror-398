# MiViA Python Client

Python API client for MiViA (Microstructure Analysis).

## Installation

```bash
pip install -e .
```

## Configuration

Set your API key as environment variable:

```bash
export MIVIA_API_KEY="your-api-key"
export MIVIA_BASE_URL="https://app.mivia.ai/api"  # optional, default
```

## Usage

### Async Client

```python
import asyncio
from mivia import MiviaClient

async def main():
    async with MiviaClient() as client:
        # List models
        models = await client.list_models()
        print(f"Models: {[m.display_name for m in models]}")

        # High-level: analyze images
        jobs = await client.analyze(
            file_paths=["image1.png", "image2.png"],
            model_id=models[0].id,
            wait=True,
        )

        for job in jobs:
            print(f"Job {job.id}: {job.status}")

        # Download report
        await client.download_pdf(
            job_ids=[j.id for j in jobs],
            output_path="report.pdf",
        )

asyncio.run(main())
```

### Sync Client

```python
from mivia import SyncMiviaClient

client = SyncMiviaClient()

# List models
models = client.list_models()

# Get customizations for a model
customizations = client.get_model_customizations(models[0].id)

# Upload and analyze with customization
jobs = client.analyze(
    file_paths=["image.png"],
    model_id=models[0].id,
    customization_id=customizations[0].id if customizations else None,
)

# Download report
client.download_csv(
    job_ids=[j.id for j in jobs],
    output_path="report.zip",
)
```

## CLI

```bash
# List models
mivia models

# List customizations for a model
mivia customizations MODEL_UUID

# Upload images
mivia upload image1.png image2.png

# Analyze (upload + run + wait)
mivia analyze image.png --model MODEL_UUID

# Analyze with customization (by name or UUID)
mivia analyze image.png --model MODEL_UUID --customization "Template Name"

# List available customizations for analyze
mivia analyze --model MODEL_UUID --list-customizations

# List jobs
mivia jobs list

# Get job details
mivia jobs get JOB_UUID

# Wait for jobs
mivia jobs wait JOB_UUID1 JOB_UUID2

# Download PDF report
mivia report pdf JOB_UUID -o report.pdf

# Download CSV report
mivia report csv JOB_UUID -o report.zip --no-images

# Show config
mivia config
```

## API Reference

### MiviaClient

| Method | Description |
|--------|-------------|
| `upload_image(path)` | Upload single image |
| `upload_images(paths)` | Upload multiple images |
| `list_images()` | List uploaded images |
| `delete_image(id)` | Delete image |
| `list_models()` | List available models |
| `get_model_customizations(id)` | Get model customizations |
| `create_jobs(image_ids, model_id)` | Create computation jobs |
| `get_job(id)` | Get job details with results |
| `list_jobs()` | List jobs with pagination |
| `wait_for_job(id)` | Poll until job completes |
| `wait_for_jobs(ids)` | Wait for multiple jobs |
| `download_pdf(job_ids, path)` | Download PDF report |
| `download_csv(job_ids, path)` | Download CSV report |
| `analyze(paths, model_id)` | High-level: upload + run + wait |
