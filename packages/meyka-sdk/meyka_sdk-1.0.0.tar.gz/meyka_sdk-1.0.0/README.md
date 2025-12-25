# Meyka AI Python SDK

Python SDK for the [Meyka AI Stock Market Chatbot API](https://api.meyka.com). Access GPT, Claude, and DeepSeek models with streaming support.

## Installation

```bash
pip install meyka-sdk
```

For async support:
```bash
pip install meyka-sdk[async]
```

## Quick Start

```python
from meyka_sdk import MeykaClient

client = MeykaClient("your_api_key")

# Quick one-liner
response = client.quick_chat("What is the capital of France?")
print(response)

# Or with a chat session
chat = client.create_chat(model="gpt-4o-mini")
response = client.send_message(chat.id, "Analyze Tesla stock")
print(response.ai_message)
```

## Features

- Multiple AI models (GPT, Claude, DeepSeek)
- Streaming responses
- Custom system prompts
- Extended thinking mode
- Usage and billing tracking
- Sync and async clients

## Available Models

### OpenAI
- `gpt-4o-mini` (default) - Cost-effective for everyday tasks
- `gpt-4o` - Multimodal GPT-4
- `gpt-4-turbo` - Extended context
- `gpt-4` - Advanced reasoning
- `gpt-3.5-turbo` - Fast and efficient
- `gpt-5` - Latest with thinking capabilities

### Anthropic (Claude)
- `claude-sonnet-4-5-20250929` - 1M token context
- `claude-opus-4-1-20250805` - Most capable
- `claude-3-5-sonnet-20241022` - Balanced
- `claude-3-5-haiku-20241022` - Fast
- `claude-haiku-4-5-20251001` - Latest Haiku

### DeepSeek
- `deepseek-chat` - General chat with tools
- `deepseek-reasoner` - Chain-of-thought reasoning

## Usage Examples

### Basic Chat

```python
from meyka_sdk import MeykaClient

client = MeykaClient("your_api_key")

# Create a chat session
chat = client.create_chat(model="claude-3-5-sonnet-20241022")

# Send a message
response = client.send_message(chat.id, "Explain quantum computing")
print(response.ai_message)

# Check token usage
print(f"Tokens used: {response.metadata.tokens.ai_message}")
print(f"Cost: ${response.metadata.billing.total_cost}")
```

### Streaming Responses

```python
from meyka_sdk import MeykaClient

client = MeykaClient("your_api_key")
chat = client.create_chat()

for chunk in client.send_message_stream(chat.id, "Write a poem about AI"):
    if chunk.content:
        print(chunk.content, end="", flush=True)
    if chunk.event_type == "hint":
        print(f"\n[Tool: {chunk.content}]")
    if chunk.event_type == "reasoning":
        print(f"\n[Thinking: {chunk.content}]")
```

### Custom System Prompt

```python
response = client.send_message(
    chat_id=chat.id,
    content="Analyze AAPL",
    system_prompt="You are a professional financial advisor specializing in tech stocks.",
    company_name="My Company"
)
```

### Extended Thinking Mode

For models that support it (Claude Sonnet 4.5, DeepSeek Reasoner):

```python
chat = client.create_chat(model="deepseek-reasoner")
response = client.send_message(
    chat.id,
    "Solve this complex math problem...",
    enable_thinking=True
)
```

### Async Client

```python
import asyncio
from meyka_sdk import AsyncMeykaClient

async def main():
    async with AsyncMeykaClient("your_api_key") as client:
        chat = await client.create_chat()
        response = await client.send_message(chat.id, "Hello!")
        print(response.ai_message)

        # Streaming
        async for chunk in client.send_message_stream(chat.id, "Tell me a story"):
            if chunk.content:
                print(chunk.content, end="")

asyncio.run(main())
```

### Chat Management

```python
# List all chats
chats = client.list_chats()
for chat in chats:
    print(f"{chat.id}: {chat.title}")

# Get chat details
chat = client.get_chat("chat_id")

# Update chat
chat = client.update_chat("chat_id", title="New Title")

# Get messages
messages = client.get_messages("chat_id")
for msg in messages:
    print(f"{msg.role}: {msg.content[:50]}...")

# Delete chat
client.delete_chat("chat_id")
```

### Error Handling

```python
from meyka_sdk import (
    MeykaClient,
    AuthenticationError,
    PaymentRequiredError,
    NotFoundError,
    BadRequestError,
)

client = MeykaClient("your_api_key")

try:
    response = client.send_message("chat_id", "Hello")
except AuthenticationError:
    print("Invalid API key")
except PaymentRequiredError as e:
    print(f"Insufficient balance: {e}")
except NotFoundError:
    print("Chat not found")
except BadRequestError as e:
    print(f"Invalid request: {e}")
```

### Context Manager

```python
with MeykaClient("your_api_key") as client:
    response = client.quick_chat("Hello!")
    print(response)
# Session automatically closed
```

## Response Objects

### ChatResponse

```python
response = client.send_message(chat.id, "Hello")

response.ai_message        # The AI's response text
response.metadata.tokens   # Token usage info
response.metadata.billing  # Cost information
response.metadata.model    # Model used
response.metadata.chat_id  # Chat ID
```

### StreamChunk

```python
for chunk in client.send_message_stream(chat.id, "Hello"):
    chunk.content       # Text content (may be None)
    chunk.event_type    # "hint", "reasoning", or None
    chunk.done          # True for final chunk
    chunk.metadata      # Only in final chunk
```

## API Reference

### MeykaClient

| Method | Description |
|--------|-------------|
| `list_chats()` | List all chat sessions |
| `create_chat(model, title)` | Create new chat |
| `get_chat(chat_id)` | Get chat details |
| `update_chat(chat_id, title, model)` | Update chat |
| `delete_chat(chat_id)` | Delete chat |
| `get_messages(chat_id)` | Get all messages |
| `send_message(chat_id, content, ...)` | Send message |
| `send_message_stream(chat_id, content, ...)` | Stream response |
| `quick_chat(content, model)` | One-off chat |
| `quick_chat_stream(content, model)` | One-off streaming |

## License

MIT License
