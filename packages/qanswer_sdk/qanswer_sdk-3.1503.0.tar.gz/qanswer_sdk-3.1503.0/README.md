# QAnswer Python SDK

[![PyPI version](https://badge.fury.io/py/qanswer-sdk.svg)](https://pypi.org/project/qanswer-sdk/)
[![Python Versions](https://img.shields.io/pypi/pyversions/qanswer-sdk.svg)](https://pypi.org/project/qanswer-sdk/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Official **Python SDK** for the [QAnswer API](https://qanswer.eu), automatically generated from the OpenAPI specification.

This SDK allows Python applications to interact with QAnswer's services programmatically without needing to craft raw HTTP requests.

---

## 🚀 Features

- Full coverage of QAnswer API endpoints  
- Type-safe models via [Pydantic](https://docs.pydantic.dev)  
- Easy configuration of authentication and base URL  
- Auto-generated and versioned with each API release  

---

## 📦 Installation

You can install from [PyPI](https://pypi.org/project/qanswer-sdk/):

```bash
pip install qanswer-sdk
```


Or add it to your `requirements.txt`

```txt
qanswer-sdk==3.1184.0
```

---

## 🔑 Authentication

Most endpoints require authentication. You can configure authentication in several ways:

### API Key Authentication

```python
from qanswer_sdk import Configuration, ApiClient
from qanswer_sdk.api.chatbot_api import ChatbotApi

# Configure API key authorization
config = Configuration(
    host="https://app.qanswer.ai/backend",
    api_key={"QAnswer-Api-Key": "your-api-key-here"}
)

# Initialize client
with ApiClient(config) as client:
    api = ChatbotApi(client)
    # Use the API...
```

### Bearer Token Authentication

```python
from qanswer_sdk import Configuration, ApiClient
from qanswer_sdk.api.chatbot_api import ChatbotApi

# Configure Bearer token authorization
config = Configuration(
    host="https://app.qanswer.ai/backend",
    access_token="your-jwt-token-here"
)

# Initialize client
with ApiClient(config) as client:
    api = ChatbotApi(client)
    # Use the API...
```

---

## 📖 Usage Examples

### Chatbot API

```python
from qanswer_sdk import Configuration, ApiClient
from qanswer_sdk.api.chatbot_api import ChatbotApi
from qanswer_sdk.models.chatbot_chat_payload import ChatbotChatPayload

config = Configuration(
    host="https://app.qanswer.ai/backend",
    api_key={"QAnswer-Api-Key": "your-api-key"}
)

with ApiClient(config) as client:
    api = ChatbotApi(client)
    
    # Create chat payload
    payload = ChatbotChatPayload(
        question="What is artificial intelligence?",
        username="admin",
        conversation_id="df150332-97c2-4b6a-9d83-cd35e14cf89c",
        llm_choice="openai-large"
        # Add other required fields based on your model
    )
    
    # Send chat message
    response = api.free_text_chatbot_chat(payload)
    print(response.ai_response)  # Access response data
```

### Chat Completion API

```python
from qanswer_sdk.api.chat_completion_api import ChatCompletionApi

with ApiClient(config) as client:
    api = ChatCompletionApi(client)
    # Use chat completion endpoints...
```

### Handle Different Response Types

```python
# Get just the data
response_data = api.free_text_chatbot_chat(payload)

# Get full HTTP response info
full_response = api.free_text_chatbot_chat_with_http_info(payload)
print(full_response.status_code)
print(full_response.headers)
print(full_response.data)

# Get raw HTTP response for streaming
raw_response = api.free_text_chatbot_chat_without_preload_content(payload)
```

---

## ⚙️ Configuration Options

```python
from qanswer_sdk import Configuration

config = Configuration(
    host="https://app.qanswer.ai/backend",  # API base URL
    api_key={"QAnswer-Api-Key": "your-key"},  # API key auth
    access_token="jwt-token",  # Bearer token auth
    username="user",  # Basic auth username
    password="pass",  # Basic auth password
    verify_ssl=True,  # SSL verification
    ssl_ca_cert="/path/to/ca.pem",  # Custom CA certificate
    connection_pool_maxsize=10,  # Connection pool size
    retries=3,  # Number of retries
    debug=False,  # Enable debug logging
    proxy="http://proxy:8080"  # Proxy URL
)
```
---

## 🛠 Error Handling

```python
from qanswer_sdk.exceptions import (
    ApiException, 
    BadRequestException,
    UnauthorizedException,
    NotFoundException
)

try:
    response = api.free_text_chatbot_chat(payload)
except UnauthorizedException:
    print("Invalid authentication credentials")
except BadRequestException as e:
    print(f"Bad request: {e}")
except ApiException as e:
    print(f"API error: {e.status} - {e.reason}")
```
---

## 📝 Models and Type Safety

All request and response objects are Pydantic models with full type safety:

```python
from qanswer_sdk.models.chatbot_chat_payload import ChatbotChatPayload
from qanswer_sdk.models.chatbot_response import ChatbotResponse

# Create typed request payload
payload = ChatbotChatPayload(
    message="Hello",
    # IDE will provide autocomplete for available fields
)

# Response is fully typed
response: ChatbotResponse = api.free_text_chatbot_chat(payload)
# Access typed response fields with autocomplete
print(response.answer)
```

---

## 📌 Versioning

This SDK follows the version of the QAnswer API.
The current version is: `3.1503.0 (branch: main)`

---

## 🤝 Support

For issues related to:

- **SDK usage:** Open an issue in this repository
- **API functionality:** Contact QAnswer support
- **Authentication:** Check your API key and permissions

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## Made with ❤️ by The QA Company