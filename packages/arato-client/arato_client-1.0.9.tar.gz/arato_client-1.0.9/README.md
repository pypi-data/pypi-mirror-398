# Arato Python SDK

The official Python SDK for the [Arato API](https://arato.ai/).

Arato is a platform for testing, experimenting, and evaluating LLM-based applications. This library provides a convenient, developer-friendly interface for interacting with Arato resources programmatically.

## Installation

Install the SDK from PyPI using pip:

```bash
pip install arato-client
```

Or, to install from source, navigate to the root directory of this project (where `pyproject.toml` is located) and run:

```bash
pip install .
```

## Usage

First, ensure you have your Arato API key. You can pass it directly to the client or set it as an environment variable named `ARATO_API_KEY`.

### Synchronous Client

```python
import os
from arato_client import AratoClient, NotFoundError

# Initialize the client (automatically uses ARATO_API_KEY env var)
# If the environment variable is not set, pass the key directly:
# client = AratoClient(api_key="your-arato-api-key")
client = AratoClient()

# List all notebooks
try:
    notebooks_response = client.notebooks.list()
    notebooks = notebooks_response.get('notebooks', [])
    print(f"Found {len(notebooks)} notebooks.")

    if notebooks:
        notebook_id = notebooks['id']

        # List experiments for the first notebook
        experiments_response = client.notebooks.experiments.list(notebook_id=notebook_id)
        experiments = experiments_response.get('experiments', [])
        print(f"Found {len(experiments)} experiments in notebook {notebook_id}.")

except NotFoundError as e:
    print(f"Error: A resource was not found. {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
```

### Asynchronous Client

The SDK also provides an async client for use with `asyncio`.

```python
import asyncio
from arato_client import AsyncAratoClient

async def main():
    async with AsyncAratoClient() as client:
        # List all notebooks
        notebooks_response = await client.notebooks.list()
        notebooks = notebooks_response.get('notebooks', [])
        print(f"Found {len(notebooks)} notebooks.")

if __name__ == "__main__":
    # Ensure ARATO_API_KEY is set in your environment before running
    if os.getenv("ARATO_API_KEY"):
        asyncio.run(main())
    else:
        print("Please set the ARATO_API_KEY environment variable.")
```

See `example.py` for a more detailed demonstration of the SDK's capabilities.