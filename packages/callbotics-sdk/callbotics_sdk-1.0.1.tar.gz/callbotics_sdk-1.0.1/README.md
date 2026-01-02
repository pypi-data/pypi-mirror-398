# Callbotics Python SDK

Official Python SDK for the Callbotics Voice AI Platform. Build, deploy, and manage voice AI bots with ease.

## Features

- 🚀 **Easy Bot Creation** - Create complete voice bots in just a few lines of code
- 🔧 **Full API Coverage** - Access all Callbotics platform features
- 🎯 **Type-Safe** - Built with type hints for better IDE support
- 📦 **Simple Installation** - Install via pip
- 🎨 **Flexible Configuration** - Fine-tune every aspect of your voice agents
- 🔄 **Campaign Management** - Orchestrate large-scale calling campaigns
- 📊 **Call Analytics** - Track and analyze call performance

## Installation

```bash
pip install callbotics-sdk
```

## Quick Start

### 1. Initialize the Client

```python
from callbotics_sdk import CallboticsClient

# Initialize with your API credentials
client = CallboticsClient("https://api.callbotics.ai")
client.login("your-email@example.com", "your-password")

# Or use an existing token
client = CallboticsClient(
    "https://api.callbotics.ai",
    api_token="your-jwt-token"
)
```

### 2. Create a Complete Bot (Easy Way)

The easiest way to create a bot is using the `create_complete_bot()` method:

```python
bot = client.create_complete_bot(
    name="Customer Support Bot",

    # LLM Configuration
    llm_type="agent_chat_gpt",
    llm_model="gpt-4.1",
    llm_api_key="sk-...",
    llm_temperature=0.7,

    # Prompt Configuration
    prompt_background="You are a friendly customer support agent for Acme Corp.",
    prompt_business_logic="Always verify customer account before proceeding. Be helpful and professional.",
    prompt_conversational_tips="Use a warm, empathetic tone. Keep responses concise.",

    # Voice Configuration (Rime AI)
    voice_api_key="your-rime-key",
    voice_speaker="wildflower",
    voice_speed=1.2,

    # Transcriber Configuration (Deepgram)
    transcriber_api_key="your-deepgram-key",
    transcriber_language="en-US",

    # Telephony Configuration (Telnyx)
    telephony_provider="telnyx",
    telephony_auth_token="your-telnyx-token",
    telephony_connection_id="your-connection-id"
)

print(f"Bot created with ID: {bot['agent']['id']}")
```

### 3. Make a Call

```python
call = client.calls.create(
    agent_id=bot['agent']['id'],
    to_number="+15551234567",
    from_number="+15559876543"
)

print(f"Call initiated: {call['id']}")
```

### 4. Create a Campaign

```python
campaign = client.campaigns.create(
    name="Q1 Customer Outreach",
    agent_id=bot['agent']['id'],
    direction="outbound",
    concurrency=5,  # Max 5 simultaneous calls
    from_phone="+15559876543",
    recording=True,
    initial_message="Hi, this is Sarah from Acme Corp."
)

# Start the campaign with a contact list
client.campaigns.start(
    campaign_id=campaign['id'],
    contact_list_id="your-contact-list-id"
)
```

## Advanced Usage

### Manual Bot Configuration

For more control, you can create each configuration separately:

```python
# 1. Create LLM Configuration
llm_config = client.llm_configs.create(
    name="GPT-4 Config",
    llm_type="agent_chat_gpt",
    model="gpt-4",
    temperature=0.7,
    api_key="sk-..."
)

# 2. Create Prompt Configuration
prompt_config = client.prompt_configs.create(
    name="Support Prompt",
    background="You are a customer support agent",
    business_logic="Verify account before proceeding",
    conversational_tips="Be warm and professional"
)

# 3. Create Voice Configuration (Rime)
voice_config = client.voice_configs.create_rime(
    name="Rime Voice",
    api_key="your-rime-key",
    speaker="wildflower",
    model_id="mistv2",
    speed_alpha=1.2,
    reduce_latency=True
)

# 4. Create Transcriber Configuration (Deepgram)
transcriber_config = client.transcriber_configs.create_deepgram(
    name="Deepgram STT",
    api_key="your-deepgram-key",
    language="en-US",
    model="nova-2-phonecall"
)

# 5. Create Telephony Configuration (Telnyx)
telephony_config = client.telephony_configs.create_telnyx(
    name="Telnyx Config",
    auth_token="your-token",
    connection_id="your-connection-id"
)

# 6. Create Agent with all configs
agent = client.agents.create(
    name="My Custom Bot",
    llm_config_id=llm_config['id'],
    prompt_config_id=prompt_config['id'],
    voice_config_id=voice_config['id'],
    transcriber_config_id=transcriber_config['id'],
    telephony_config_id=telephony_config['id']
)
```

### Managing Campaigns

```python
# List all campaigns
campaigns = client.campaigns.list(page=1, per_page=10)

# Get specific campaign
campaign = client.campaigns.get(campaign_id="...")

# Update campaign
client.campaigns.update(
    campaign_id="...",
    concurrency=10,
    recording=True
)

# Pause/Resume campaign
client.campaigns.pause(campaign_id="...")

# Check available concurrency
concurrency_info = client.campaigns.get_available_concurrency()
print(f"Available slots: {concurrency_info}")
```

### Managing Calls

```python
# List all calls
calls = client.calls.list(
    page=1,
    per_page=20,
    status="ended",
    campaign_id="..."
)

# Get call details
call = client.calls.get(call_id="...")
print(f"Duration: {call['duration']} seconds")
print(f"Transcript: {call['transcript']}")

# Get call analytics
summary = client.calls.get_summary(
    campaign_id="...",
    start_date="2024-01-01",
    end_date="2024-01-31"
)
print(f"Total minutes: {summary['total_minutes']}")
```

### Listing and Updating Configurations

```python
# List all voice configurations
voices = client.voice_configs.list()

# Get specific config
voice = client.voice_configs.get(config_id="...")

# Update prompt
client.prompt_configs.update(
    config_id="...",
    background="Updated persona",
    business_logic="New rules"
)

# Delete configuration
client.llm_configs.delete(config_id="...")
```

## Configuration Options

### Supported LLM Providers

- **OpenAI ChatGPT** (`agent_chat_gpt`)
  - Models: `gpt-4`, `gpt-3.5-turbo`, etc.
- **Anthropic Claude** (`agent_anthropic`)
  - Models: `claude-3-opus-20240229`, `claude-3-sonnet-20240229`, etc.
- **Groq** (`agent_groq`)
  - Models: `llama-3.1-70b-versatile`, etc.
- **Azure OpenAI** (`agent_azure_open_ai`)

### Supported Voice Providers

- **Rime AI** (`rime`) - Low-latency, high-quality TTS
  - Speakers: `wildflower`, `bloom`, etc.
  - Models: `mistv2`, `mist`, `v1`
- **ElevenLabs** (`eleven_labs`) - Natural-sounding voices
- **Deepgram** (`deepgram`) - Fast TTS
- **PlayHT** (`play_ht`)

### Supported Transcriber Providers

- **Deepgram** (`deepgram`) - Industry-leading STT
  - Models: `nova-2-phonecall`, `nova-2`, `enhanced`
  - Languages: 30+ supported

### Supported Telephony Providers

- **Telnyx** (`telnyx`)
- **Twilio** (`twilio`)

## Error Handling

```python
from callbotics_sdk import (
    CallboticsException,
    AuthenticationError,
    APIError,
    ResourceNotFoundError,
    ValidationError
)

try:
    call = client.calls.create(
        agent_id="invalid-id",
        to_number="+15551234567"
    )
except AuthenticationError:
    print("Authentication failed. Please check your credentials.")
except ValidationError as e:
    print(f"Validation error: {e}")
except ResourceNotFoundError:
    print("Agent not found.")
except APIError as e:
    print(f"API error: {e.status_code} - {e}")
except CallboticsException as e:
    print(f"General error: {e}")
```

## Examples

See the `/examples` directory for complete working examples:

- **basic_bot.py** - Create and use a simple bot
- **advanced_bot.py** - Advanced configuration and campaign management
- **campaign_management.py** - Running large-scale campaigns

## Authentication

The SDK supports two authentication methods:

### 1. Email/Password Login

```python
client = CallboticsClient("https://api.callbotics.ai")
token = client.login("user@example.com", "password")
print(f"Logged in with token: {token}")
```

### 2. Pre-authenticated Token

```python
client = CallboticsClient(
    "https://api.callbotics.ai",
    api_token="your-jwt-token"
)
```

### 3. Set Token Later

```python
client = CallboticsClient("https://api.callbotics.ai")
# ... later
client.set_token("your-jwt-token")
```

## API Reference

### Client

- `CallboticsClient(base_url, api_token=None)` - Initialize client
- `login(email, password)` - Authenticate with credentials
- `set_token(token)` - Set authentication token manually
- `create_complete_bot(...)` - Create a bot with all configurations

### Resources

- `client.agents` - Agent management
- `client.campaigns` - Campaign management
- `client.calls` - Call management
- `client.llm_configs` - LLM configuration
- `client.voice_configs` - Voice configuration
- `client.transcriber_configs` - Transcriber configuration
- `client.telephony_configs` - Telephony configuration
- `client.prompt_configs` - Prompt configuration

## Requirements

- Python 3.8+
- `requests>=2.28.0`
- `pydantic>=2.0.0`

## Support

- **Documentation**: [https://docs.callbotics.ai](https://docs.callbotics.ai)
- **Email**: anurag.singh@callbotics.ai

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please submit pull requests or open issues on GitHub.

## Changelog

### v1.0.1 (2025)
- Initial release
- Full API coverage for agents, campaigns, and calls
- Configuration builders for all providers
- Comprehensive error handling
- Easy bot creation with `create_complete_bot()`
