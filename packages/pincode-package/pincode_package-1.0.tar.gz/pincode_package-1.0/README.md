<!-- # indianpincode

A Python package to fetch live Indian pincode details using PostalPincode.in API.

## Installation
```bash
pip install pincode_package -->


# pincode_package

A Python package to fetch Indian Pincode and Post Office details using the official India Post API, with offline cache fallback, retry logic, async support, and a CLI tool.

🔍 Search by Pincode

🏤 Search by Post Office Name

💾 Offline cache fallback (OS-safe cache)

⏱ Cache expiry (TTL) to avoid stale data

🔁 Retry with exponential backoff for network resilience

⚡ Async & Sync APIs

🖥 Command Line Interface (CLI)

🌐 FastAPI integration ready

🧪 Fully unit-tested

📦 PyPI-ready structure

## Install from PyPI
```python
pip install pincode_package
```

## Install from source (development)
```python
git clone https://github.com/your-username/pincode_package.git
cd pincode_package
pip install -e .
```
This project uses pyproject.toml (PEP 621) — no requirements.txt needed.

## Sync Usage
```python

from pincode_package import fetch_by_pincode, fetch_by_postoffice_name

postoffice = fetch_by_pincode("682001")
pin = fetch_by_postoffice_name("Ernakulam")
print(postoffice)
print(pin)
```

## Async Usage
```python
import asyncio
from pincode_package.api import fetch_by_pincode_async

async def main():
    data = await fetch_by_pincode_async("682001")
    print(data)

asyncio.run(main())
```
## Command-Line Interface (CLI)
```python
pincode 682001
pincode Ernakulam

```
## Exmaple Output
```
Ernakulam | N/A | Ernakulam | Kerala | Ernakulam | 682001

```
Missing fields are safely displayed as N/A.

## Cache Behaviour

Cache location :
```
~/.cache/pincode_package/cache.json
```
Cache key: Pincode

Cache value: Post Office list

Cache expiry (TTL): 7 days

Cache used automatically when API is unavailable

## Retry & Backoff

Automatic retries on network failure

Exponential backoff:

✔ Retry 1 → 1s

✔ Retry 2 → 2s

✔ Retry 3 → 4s

Improves reliability for unstable networks.

## Error Handling
The package uses custom exceptions:
```python
from pincode_package.exceptions import (
    APIUnavailableError,
    PincodeNotFoundError,
    PostOfficeNotFoundError
)

```

## Logging
The package uses Python’s standard logging module.
Enable logs in your application:
```
import logging
logging.basicConfig(level=logging.INFO)

```

## FastAPI Integration Example
```
from fastapi import FastAPI
from pincode_package.api import fetch_by_pincode_async

app = FastAPI()

@app.get("/pincode/{pincode}")
async def pincode_lookup(pincode: str):
    return await fetch_by_pincode_async(pincode)
```
Run:
```
uvicorn api_server:app --reload
```
## Testing
Run tests with:
```
pytest -v
```
✔ API calls mocked
✔ Cache mocked
✔ Error paths tested

## 🛠 Requirements

Python 3.8+

requests

httpx




