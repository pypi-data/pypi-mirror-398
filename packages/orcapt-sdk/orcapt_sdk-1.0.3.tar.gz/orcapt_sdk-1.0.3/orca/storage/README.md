# Orca Storage SDK

Simple storage client for Orca platform.

## Quick Start

```python
from orca import OrcaStorage

# Initialize
storage = OrcaStorage(
    workspace='my-workspace',
    token='my-token',
    base_url='https://api.example.com/api/v1/storage'
)

# Create bucket
bucket = storage.create_bucket('my-bucket')

# Upload file
file_info = storage.upload_file('my-bucket', 'report.pdf', folder='reports/2025/')

# Download file
storage.download_file('my-bucket', 'reports/2025/report.pdf', 'local.pdf')

# List files
files = storage.list_files('my-bucket', folder='reports/')
```

## Documentation

See [Orca Storage SDK Developer Guide](../../../Orca_storage%20_SDK_Developer_Guide.md) for complete documentation.
