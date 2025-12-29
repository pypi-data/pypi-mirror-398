# KeiroLabs Python SDK

Official Python SDK for KeiroLabs - AI-powered search, research, and web crawling.

[![PyPI version](https://badge.fury.io/py/keirolabs.svg)](https://badge.fury.io/py/keirolabs)
[![Python Support](https://img.shields.io/pypi/pyversions/keirolabs.svg)](https://pypi.org/project/keirolabs/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Installation

```bash
pip install keirolabs
```

---

## Quick Start

```python
from keirolabs import Keiro
import os

# Initialize with your API key
client = Keiro(api_key=os.getenv("KEIRO_API_KEY"))

# Search
result = client.search("machine learning trends 2024")
print(result['data'])

# Get detailed answers
answer = client.answer("How does neural network training work?")
print(answer['data'])

# Research topics
research = client.research("quantum computing applications")
print(research['data'])
```

Get your API key: [https://www.keirolabs.cloud/](https://www.keirolabs.cloud/)

---

## API Methods

### search

Perform a neural search query.

**Parameters:**
- `query` (str, required): Search query
- `**kwargs`: Additional search parameters

**Returns:** Dictionary with search results and remaining credits

**Example:**
```python
result = client.search("Python best practices")
print(f"Found {len(result['data'])} results")
print(f"Credits remaining: {result['creditsRemaining']}")
```

**Credits:** 1 per search

---

### search_pro

Advanced search with enhanced capabilities.

**Parameters:**
- `query` (str, required): Search query
- `**kwargs`: Additional parameters

**Example:**
```python
result = client.search_pro("advanced AI architectures")
```

---

### answer

Generate detailed answers to questions using AI.

**Parameters:**
- `query` (str, required): Your question
- `**kwargs`: Additional parameters

**Returns:** Dictionary with answer and remaining credits

**Example:**
```python
answer = client.answer("What is reinforcement learning?")
print(answer['data'])
```

**Credits:** 5 per answer

---

### research

Conduct comprehensive research on any topic.

**Parameters:**
- `query` (str, required): Research topic
- `**kwargs`: Additional parameters

**Example:**
```python
research = client.research("climate change solutions")
print(research['data'])
```

---

### research_pro

Advanced research with deeper analysis.

**Parameters:**
- `query` (str, required): Research topic
- `**kwargs`: Additional parameters

**Example:**
```python
research = client.research_pro("blockchain consensus mechanisms")
```

---

### web_crawler

Extract structured data from any URL.

**Parameters:**
- `url` (str, required): Website URL to crawl
- `**kwargs`: Additional parameters

**Example:**
```python
data = client.web_crawler("https://example.com")
print(data['data'])
```

---

### search_engine

Access search engine functionality.

**Parameters:**
- `query` (str, required): Search query
- `**kwargs`: Additional parameters

**Example:**
```python
results = client.search_engine("latest AI papers")
```

---

### health_check

Check API server status.

**Example:**
```python
health = client.health_check()
print(f"Status: {health['status']}")
print(f"Environment: {health['environment']}")
```

---

## Error Handling

The SDK provides specific exception types for different error scenarios:

```python
from keirolabs import Keiro
from keirolabs.exceptions import (
    KeiroAuthError,
    KeiroRateLimitError,
    KeiroValidationError,
    KeiroConnectionError
)

client = Keiro(api_key="your-api-key")

try:
    result = client.search("query")
except KeiroAuthError:
    print("Invalid API key")
except KeiroRateLimitError:
    print("Out of credits")
except KeiroValidationError as e:
    print(f"Invalid parameter: {e}")
except KeiroConnectionError as e:
    print(f"Connection error: {e}")
```

### Exception Types

- **KeiroError** - Base exception class
- **KeiroAuthError** - Authentication failed (invalid API key)
- **KeiroRateLimitError** - Out of credits
- **KeiroValidationError** - Invalid request parameters
- **KeiroConnectionError** - Network connection issues
- **KeiroAPIError** - General API errors

---

## Custom Configuration

### Timeout

Set custom timeout for requests:

```python
client = Keiro(
    api_key="your-api-key",
    timeout=60  # seconds
)
```

### Local Development

For local development servers only:

```python
client = Keiro(
    api_key="your-api-key",
    base_url="http://localhost:8000/api"
)
```

### Environment Variables

Recommended for production:

```python
from dotenv import load_dotenv
import os
from keirolabs import Keiro

load_dotenv()
client = Keiro(api_key=os.getenv("KEIRO_API_KEY"))
```

Create `.env` file:
```
KEIRO_API_KEY=your-api-key-here
```

---

## Advanced Examples

### Example 1: Batch Search

```python
from keirolabs import Keiro

client = Keiro(api_key="your-api-key")

queries = ["AI trends", "machine learning", "deep learning"]
results = []

for query in queries:
    result = client.search(query)
    results.append(result)
    print(f"Query: {query}")
    print(f"Results: {len(result['data'])}")
    print(f"Credits: {result['creditsRemaining']}")
```

### Example 2: Research with Error Handling

```python
from keirolabs import Keiro
from keirolabs.exceptions import KeiroRateLimitError

client = Keiro(api_key="your-api-key")

try:
    research = client.research("quantum computing")
    answer = client.answer("How does quantum entanglement work?")
    print(research['data'])
    print(answer['data'])
except KeiroRateLimitError:
    print("Please add more credits to continue")
```

### Example 3: Web Scraping Pipeline

```python
from keirolabs import Keiro

client = Keiro(api_key="your-api-key")

urls = [
    "https://example.com/article1",
    "https://example.com/article2"
]

for url in urls:
    data = client.web_crawler(url)
    print(f"Extracted from {url}:")
    print(data['data'])
```

---

## Context Manager

Automatic session cleanup:

```python
with Keiro(api_key="your-api-key") as client:
    result = client.search("query")
    print(result)
# Session automatically closed
```

---

## Requirements

- Python >= 3.7
- requests >= 2.28.0

---

## Links

- **Homepage:** https://www.keirolabs.cloud/
- **API Dashboard:** https://www.keirolabs.cloud/
- **PyPI:** https://pypi.org/project/keirolabs
- **Support:** support@keiro.com

---

## License

MIT License - see LICENSE file for details.

---

**Version 0.1.3**

Made by KeiroLabs Team
