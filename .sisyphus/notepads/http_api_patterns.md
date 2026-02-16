# SearXNG HTTP API Integration Patterns

## Executive Summary

SearXNG uses **httpx** as its primary HTTP client library for all external API calls. The codebase provides a custom network abstraction layer (`searx.network`) that wraps httpx with synchronous interfaces while handling async operations internally. This document summarizes the patterns for implementing OpenAI-compatible API calls.

---

## 1. HTTP Client Library

### Primary Library: httpx
- **Import pattern**: `import httpx` or `from httpx import HTTPError`
- **Found in**: 15+ files across the codebase
- **Key locations**:
  - `/opt/searxng/searx/network/__init__.py` - Main network interface
  - `/opt/searxng/searx/network/client.py` - HTTP client configuration
  - `/opt/searxng/searx/network/network.py` - Network management

### Secondary Libraries
- **urllib**: Used ONLY for URL parsing (urlencode, urlparse, urljoin)
  - `from urllib.parse import urlencode, urlparse, urljoin`
- **requests**: Used only in utility/update scripts (not in engines)
- **aiohttp**: NOT used in SearXNG

---

## 2. Network Module Import Patterns

### Standard Import (for GET requests)
```python
# For simple GET requests within engines
from searx.network import get
from searx.network import get as http_get  # Alias pattern
```

### Standard Import (for POST requests)
```python
# For POST requests
from searx.network import post as http_post
```

### Multiple Methods
```python
from searx.network import get, raise_for_httperror
from searx.network import post, get
```

### Authentication Support
```python
from httpx import DigestAuth  # For HTTP Digest authentication
```

---

## 3. Engine Implementation Patterns

### 3.1 GET Request Pattern (Most Common)

**Example: GitHub API** (`searx/engines/github.py`)
```python
from urllib.parse import urlencode

about = {
    "website": 'https://github.com/',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

categories = ['it', 'repos']
search_url = 'https://api.github.com/search/repositories?sort=stars&order=desc&{query}'
accept_header = 'application/vnd.github.preview.text-match+json'

def request(query, params):
    params['url'] = search_url.format(query=urlencode({'q': query}))
    params['headers']['Accept'] = accept_header
    return params

def response(resp):
    results = []
    for item in resp.json().get('items', []):
        results.append({
            'url': item.get('html_url'),
            'title': item.get('full_name'),
            'content': item.get('description', ''),
        })
    return results
```

### 3.2 POST with Form Data Pattern

**Example: DeepL API** (`searx/engines/deepl.py`)
```python
def request(_query, params):
    params['url'] = url
    params['method'] = 'POST'
    params['data'] = {
        'auth_key': api_key,
        'text': params['query'],
        'target_lang': params['to_lang'][1]
    }
    return params
```

### 3.3 POST with JSON Body Pattern

**Example: Azure API** (`searx/engines/azure.py`)
```python
from searx.network import post as http_post

def request(query: str, params: "OnlineParams") -> None:
    token = get_auth_token(azure_tenant_id, azure_client_id, azure_client_secret)
    
    params["url"] = azure_batch_endpoint
    params["method"] = "POST"
    params["headers"]["Authorization"] = f"Bearer {token}"
    params["headers"]["Content-Type"] = "application/json"
    params["json"] = {
        "requests": [
            {
                "url": "/providers/Microsoft.ResourceGraph/resources?api-version=2024-04-01",
                "httpMethod": "POST",
                "content": {"query": f"Resources | where name contains '{query}' | take 30"}
            }
        ]
    }
```

**Example: Semantic Scholar** (`searx/engines/semantic_scholar.py`)
```python
params["url"] = search_url
params["method"] = "POST"
params["headers"].update({
    "Content-Type": "application/json",
    "X-S2-UI-Version": get_ui_version(),
})
params["json"] = {
    "queryString": query,
    "page": params["pageno"],
    "pageSize": 10,
    "sort": "relevance",
}
```

### 3.4 POST with Raw JSON String Pattern

**Example: Cloudflare AI** (`searx/engines/cloudflareai.py`)
```python
from json import loads, dumps

def request(query, params):
    params['url'] = f'https://gateway.ai.cloudflare.com/v1/{cf_account_id}/{cf_ai_gateway}/workers-ai/{cf_ai_model}'
    params['method'] = 'POST'
    params['headers']['Authorization'] = f'Bearer {cf_ai_api}'
    params['headers']['Content-Type'] = 'application/json'
    params['data'] = dumps({
        'messages': [
            {'role': 'assistant', 'content': cf_ai_model_assistant},
            {'role': 'system', 'content': cf_ai_model_system},
            {'role': 'user', 'content': params['query']},
        ]
    }).encode('utf-8')
```

### 3.5 Direct HTTP Calls in Engine Functions

**Example: Spotify** (`searx/engines/spotify.py`)
```python
from json import loads
from searx.network import post as http_post

def request(query, params):
    offset = (params['pageno'] - 1) * 20
    params['url'] = search_url.format(query=urlencode({'q': query}), offset=offset)
    
    # Direct HTTP POST for authentication token
    r = http_post(
        'https://accounts.spotify.com/api/token',
        data={'grant_type': 'client_credentials'},
        headers={
            'Authorization': 'Basic ' + base64.b64encode(f"{api_client_id}:{api_client_secret}".encode()).decode()
        },
    )
    j = loads(r.text)
    params['headers'] = {'Authorization': f'Bearer {j.get("access_token")}'}
    return params
```

---

## 4. Async vs Sync Patterns

### Sync Interface Only for Engines
- **Engines use synchronous interfaces exclusively**
- The `searx.network` module handles async operations internally
- Engines call `get()`, `post()`, etc. which are synchronous wrappers
- Async operations run on a dedicated event loop in a background thread

### Network Layer Async Pattern
```python
# In searx/network/__init__.py
def request(method: str, url: str, **kwargs) -> SXNG_Response:
    with _record_http_time() as start_time:
        network = get_context_network()
        timeout = _get_timeout(start_time, kwargs)
        future = asyncio.run_coroutine_threadsafe(
            network.request(method, url, **kwargs),
            get_loop(),
        )
        try:
            return future.result(timeout)
        except concurrent.futures.TimeoutError as e:
            raise httpx.TimeoutException('Timeout', request=None) from e
```

### Key Insight for OpenAI Implementation
- Use the synchronous `post()` function from `searx.network`
- Pass JSON payload via `params['json'] = {...}` or `params['data'] = json.dumps({...}).encode()`
- The network layer handles all async/await internally

---

## 5. Timeout Configuration

### Engine-Level Timeout Setting
```python
# In engine module
timeout = 2.0  # seconds (default varies by engine)
```

### Common Timeout Values
- `timeout = 2.0` - Demo engines, fast APIs
- `timeout = 3.0` - Semantic Scholar, Arch Linux wiki
- `timeout = 5.0` - Azure authentication
- `timeout = 10.0` - Open Library
- `timeout = 60.0` - Odysee, PeerTube (video platforms)

### Per-Request Timeout Override
```python
# Direct network call with timeout
from searx.network import get
resp = get(base_url, timeout=3)
```

### Global Default
- From `searx/network/__init__.py`: 2 minutes default for requests without timeout
- Thread-local timeout management via `set_timeout_for_thread()`

### Recommendation for OpenAI API
- Use `timeout = 30.0` or `timeout = 60.0` for AI API calls
- AI summarization may take longer than typical search queries

---

## 6. Error Handling Conventions

### 6.1 HTTP Error Exceptions (httpx)
```python
import httpx

# Caught in online.py processor:
- httpx.TimeoutException
- asyncio.TimeoutError
- httpx.HTTPError
- httpx.StreamError
- ssl.SSLError
```

### 6.2 SearXNG Custom Exceptions
From `searx/exceptions.py`:
```python
from searx.exceptions import (
    SearxEngineAPIException,           # API returned application error
    SearxEngineAccessDeniedException,   # HTTP 402, 403
    SearxEngineTooManyRequestsException, # HTTP 429
    SearxEngineCaptchaException,        # CAPTCHA detected
)
```

### 6.3 Error Handling Pattern
**Example: Cloudflare AI** (`searx/engines/cloudflareai.py`)
```python
from json import loads
from searx.exceptions import SearxEngineAPIException

def response(resp):
    results = []
    json = loads(resp.text)
    
    if 'error' in json:
        raise SearxEngineAPIException('Cloudflare AI error: ' + json['error'])
    
    if 'result' in json:
        results.append({
            'content': json['result']['response'],
            'infobox': cf_ai_model_display_name,
        })
    
    return results
```

### 6.4 Response Status Checking
**Example: Azure** (`searx/engines/azure.py`)
```python
from searx.network import post as http_post

def authenticate(t_id: str, c_id: str, c_secret: str) -> str:
    resp = http_post(url, body, timeout=5)
    if resp.status_code != 200:
        raise RuntimeError(f"Azure authentication failed (status {resp.status_code}): {resp.text}")
    return resp.json()["access_token"]
```

### 6.5 Response.ok Property
```python
resp = get(base_url, timeout=3)
if not resp.ok:  # resp.ok = not resp.is_error (for requests compatibility)
    raise RuntimeError("Request failed")
```

---

## 7. JSON Parsing Patterns

### 7.1 Preferred Pattern: resp.json()
```python
def response(resp):
    json_data = resp.json()  # Returns Python dict/list
    for item in json_data['results']:
        # Process results
```

**Used by**: 96+ engines including:
- github.py: `resp.json().get('items', [])`
- open_meteo.py: `json_data = resp.json()`
- spotify.py: `search_res = loads(resp.text)` (alternative)

### 7.2 Alternative: json.loads(resp.text)
```python
from json import loads

def response(resp):
    json_data = loads(resp.text)
    # Process results
```

### 7.3 Common JSON Access Patterns
```python
# Safe dictionary access
for item in resp.json().get('items', []):
    title = item.get('title', '')
    
# Nested access with defaults
content = result.get('venue', {}).get('text') or result.get('journal', {}).get('name')

# Array iteration
for result in json_data["results"]:
    url = result.get("primaryPaperLink", {}).get("url")
```

---

## 8. Authentication Patterns

### 8.1 Bearer Token in Headers
```python
params['headers']['Authorization'] = f'Bearer {api_key}'
```

### 8.2 API Key in POST Data
```python
params['data'] = {
    'auth_key': api_key,
    'text': params['query'],
    'target_lang': params['to_lang'][1]
}
```

### 8.3 HTTP Digest Authentication
```python
from httpx import DigestAuth

if http_digest_auth_user and http_digest_auth_pass:
    params['auth'] = DigestAuth(http_digest_auth_user, http_digest_auth_pass)
```

---

## 9. Complete Example: OpenAI-Compatible API Implementation

Based on patterns from cloudflareai.py, azure.py, and semantic_scholar.py:

```python
# SPDX-License-Identifier: AGPL-3.0-or-later
"""OpenAI-compatible API summarization engine for SearXNG"""

from urllib.parse import urlencode
from searx.result_types import EngineResults
from searx.exceptions import SearxEngineAPIException

about = {
    "website": "https://openai.com",
    "wikidata_id": None,
    "official_api_documentation": "https://platform.openai.com/docs",
    "use_official_api": True,
    "require_api_key": True,
    "results": "JSON",
}

engine_type = "online"
categories = ["general"]
disabled = True

# Configuration options (set in settings.yml)
openai_api_base = "https://api.openai.com/v1"
openai_api_key = None
openai_model = "gpt-3.5-turbo"
openai_max_tokens = 150
timeout = 30.0  # AI APIs may take longer


def request(query, params):
    """Build request for OpenAI chat completions API"""
    
    if not openai_api_key:
        return None  # Skip if no API key configured
    
    params['url'] = f"{openai_api_base}/chat/completions"
    params['method'] = 'POST'
    params['headers']['Authorization'] = f'Bearer {openai_api_key}'
    params['headers']['Content-Type'] = 'application/json'
    params['json'] = {
        'model': openai_model,
        'messages': [
            {
                'role': 'system',
                'content': 'You are a helpful assistant that summarizes search results concisely.'
            },
            {
                'role': 'user',
                'content': f"Summarize: {query}"
            }
        ],
        'max_tokens': openai_max_tokens,
        'temperature': 0.7,
    }
    
    return params


def response(resp) -> EngineResults:
    """Parse OpenAI API response"""
    res = EngineResults()
    
    json_data = resp.json()
    
    # Handle API errors
    if 'error' in json_data:
        error_msg = json_data['error'].get('message', 'Unknown error')
        raise SearxEngineAPIException(f'OpenAI API error: {error_msg}')
    
    # Extract summary from response
    choices = json_data.get('choices', [])
    if choices and len(choices) > 0:
        summary = choices[0].get('message', {}).get('content', '').strip()
        if summary:
            res.add(
                res.types.Answer(
                    answer=summary,
                    url="https://openai.com",
                )
            )
    
    return res
```

---

## 10. Key Takeaways for OpenAI API Implementation

1. **Use `httpx` via `searx.network`**: Import `from searx.network import post`
2. **Synchronous interface**: Engines don't use async/await directly
3. **JSON POST data**: Use `params['json'] = {...}` for dict payload
4. **Set appropriate timeout**: `timeout = 30.0` for AI API calls
5. **Error handling**: Use `SearxEngineAPIException` for API errors
6. **Response parsing**: Use `resp.json()` to parse JSON responses
7. **Authentication**: Set `params['headers']['Authorization'] = f'Bearer {api_key}'`
8. **Configuration**: Define settings as module-level variables (e.g., `openai_api_key = None`)

---

## 11. Files Referenced

### Network Layer
- `/opt/searxng/searx/network/__init__.py` - Main network interface
- `/opt/searxng/searx/network/client.py` - HTTP client configuration
- `/opt/searxng/searx/network/network.py` - Network management
- `/opt/searxng/searx/network/raise_for_httperror.py` - Error handling

### Processor Layer
- `/opt/searxng/searx/search/processors/online.py` - Online engine processor

### Example Engines
- `/opt/searxng/searx/engines/cloudflareai.py` - AI API pattern (JSON POST)
- `/opt/searxng/searx/engines/azure.py` - Token auth + JSON POST
- `/opt/searxng/searx/engines/semantic_scholar.py` - JSON POST with headers
- `/opt/searxng/searx/engines/spotify.py` - Direct network calls in request()
- `/opt/searxng/searx/engines/deepl.py` - Form POST pattern
- `/opt/searxng/searx/engines/github.py` - Simple GET pattern
- `/opt/searxng/searx/engines/demo_online.py` - Basic engine structure

### Type Definitions
- `/opt/searxng/searx/extended_types.py` - SXNG_Response, SXNG_Request
- `/opt/searxng/searx/exceptions.py` - SearxEngineAPIException, etc.

---

*Generated from analysis of SearXNG codebase*
