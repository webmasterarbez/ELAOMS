# Eleven Labs Agents Open Memory System (ELAOMS)

A Python FastAPI service that integrates Eleven Labs Agents with OpenMemory for persistent, personalized agent memory. This system enables agents to remember past conversations and personalize interactions based on user history.

## Features

- **Post-Call Memory Storage**: Automatically stores entire conversation data to OpenMemory after calls complete
- **Personalized First Messages**: Generates AI-powered personalized greetings based on user's conversation history
- **In-Call Memory Search**: Provides on-demand memory search during conversations via Eleven Labs Tools
- **Agent Profile Caching**: Caches agent configurations locally to reduce API calls

## Project Structure

```
ElevenLabsAgentsOpenMemorySystem/
├── main.py                    # FastAPI application entry point
├── config.py                  # Configuration and settings
├── requirements.txt           # Python dependencies
├── .gitignore                 # Git ignore rules
│
├── src/                       # Core application code
│   ├── __init__.py
│   ├── clients/               # API clients
│   │   ├── __init__.py
│   │   ├── openmemory.py     # OpenMemory API client
│   │   └── elevenlabs.py     # Eleven Labs API client
│   ├── models/                # Models package
│   │   └── __init__.py
│   ├── webhooks/              # Webhook handlers
│   │   ├── __init__.py
│   │   ├── post_call.py       # Post-call webhook handler
│   │   ├── client_data.py     # Client data webhook handler
│   │   └── search_data.py     # Search data webhook handler
│   └── utils/                 # Utility functions
│       ├── __init__.py
│       ├── auth.py            # Authentication utilities (HMAC, header auth)
│       └── helpers.py         # Helper functions (user ID extraction, response building)
│
├── scripts/                    # Utility scripts
│   ├── setup.sh               # Setup script for initial configuration
│   ├── push_to_github.sh      # Script to push to GitHub
│   ├── store_conversations.py # Script to store conversations manually
│   ├── build_comprehensive_user_profile.py  # Comprehensive user profile builder
│   ├── show_user_profile.py   # Display user profile from OpenMemory
│   ├── view_stored_conversations.py  # View stored conversations
│   └── generate_first_message.py  # Generate personalized first messages
│
├── tests/                     # Test scripts
│   └── test_post_call_storage_standalone.py  # Standalone test for post-call storage
│
└── data/                      # Output/data files (gitignored)
    └── .gitkeep               # Keep directory in git
```

## Architecture

The system consists of three main webhook endpoints:

1. **`/webhooks/post-call`**: Receives post-call webhooks from Eleven Labs and stores entire payload to OpenMemory
2. **`/webhooks/client-data`**: Handles conversation initiation, queries OpenMemory for user context, and returns personalized first messages
3. **`/webhooks/search-data`**: Provides in-call memory search functionality as an Eleven Labs Tool

## Prerequisites

- **Python 3.12+** (tested with Python 3.12)
- **OpenMemory server** running and accessible
- **Eleven Labs API key** with access to Agents API
- **Eleven Labs webhook secret** for HMAC signature validation
- **(Optional) ngrok** for local development and testing

## Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/cursor_elaoms.git
cd cursor_elaoms
```

2. Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file (you can use the setup script):
```bash
bash scripts/setup.sh
```

Or manually create a `.env` file with your credentials:
```env
# OpenMemory Configuration
OPENMEMORY_URL=http://localhost:8080
OPENMEMORY_API_KEY=your_openmemory_api_key_here

# Eleven Labs Configuration
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
ELEVENLABS_POST_CALL_HMAC_KEY=your_post_call_hmac_key_here
ELEVENLABS_CLIENT_DATA_WORKSPACE_SECRET=your_client_data_workspace_secret_here

# Webhook Storage Configuration
WEBHOOK_STORAGE_PATH=data/webhooks
WEBHOOK_QUARANTINE_PATH=data/webhooks/quarantine
AUDIO_CACHE_TTL=3600
WEBHOOK_RETENTION_DAYS=30
MAX_RETRIES=3
ANOMALY_DETECTION_ENABLED=true
ANOMALY_FAILURE_THRESHOLD=5
ANOMALY_WINDOW_SECONDS=300
ALERT_ON_QUARANTINE_FAILURES=true
REDIS_URL=
REDIS_TTL=3600
FILE_PERMISSIONS_MODE=384
ENABLE_ENCRYPTION_AT_REST=false
```

5. Start the service - no database initialization needed!

## Running the Service

### Quick Start

1. Start the FastAPI service:
```bash
python main.py
```

The service will start on `http://0.0.0.0:8000` by default.

2. Verify the service is running:
```bash
curl http://localhost:8000/health
```

3. Check the API documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Local Development with ngrok

For local development, you'll need to expose your local service to the internet:

1. Start the FastAPI service:
```bash
python main.py
```

Or using uvicorn directly with auto-reload:
```bash
uvicorn main:app --reload --port 8000
```

2. In a separate terminal, start ngrok to expose the service:
```bash
ngrok http 8000
```

3. Use the ngrok HTTPS URL (e.g., `https://abc123.ngrok.io`) for your webhook endpoints in Eleven Labs configuration.

### Production

Deploy the FastAPI service to your preferred hosting platform:

**Recommended Platforms**:
- **Railway**: Easy deployment with automatic HTTPS
- **Render**: Free tier available with automatic HTTPS
- **Fly.io**: Global edge deployment
- **AWS/GCP/Azure**: Enterprise-grade hosting
- **Heroku**: Simple deployment (requires credit card)

**Production Considerations**:
- Set up proper environment variables in your hosting platform
- Configure HTTPS (most platforms provide this automatically)
- Set up monitoring and logging
- Use a process manager like `gunicorn` with `uvicorn` workers:
  ```bash
  gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
  ```

## Configuration in Eleven Labs

### 1. Post-Call Webhook

1. Go to Agents Platform settings
2. Enable post-call webhooks
3. Set webhook URL to: `https://your-domain.com/webhooks/post-call`
4. Configure HMAC key (store in `ELEVENLABS_POST_CALL_HMAC_KEY`)

### 2. Client Data Webhook (Twilio Personalization)

1. Go to your agent's Security settings
2. Enable "Fetch conversation initiation data for inbound Twilio calls"
3. Configure webhook URL: `https://your-domain.com/webhooks/client-data`
4. Add any required secrets to headers in Eleven Labs secrets manager

### 3. Search Data Webhook (Tool)

1. Go to your agent's Tools settings
2. Add a webhook tool with URL: `https://your-domain.com/webhooks/search-data`
3. Configure tool parameters:
   - `query`: The search query string
   - `user_id`: User identifier (optional, will use caller_id if available)
   - `limit`: Maximum number of results (default: 5)

## API Endpoints

### GET `/`
Root endpoint that returns service information.

**Response**:
```json
{
  "service": "Eleven Labs Agents Open Memory System (ELAOMS)",
  "version": "1.0.0",
  "status": "running"
}
```

### GET `/health`
Health check endpoint for monitoring and load balancers.

**Response**:
```json
{
  "status": "healthy"
}
```

### POST `/webhooks/post-call`
Receives post-call transcription webhooks from Eleven Labs and stores the entire payload to OpenMemory.

**Authentication**: HMAC signature validation via `ElevenLabs-Signature` header

**Request**: Complete `post_call_transcription` webhook payload from Eleven Labs

**Response**:
```json
{
  "status": "received",
  "memory_id": "memory-id-from-openmemory"
}
```

**User ID Extraction Priority**:
1. `system__caller_id` from `dynamic_variables` (most consistent for same caller)
2. `user_id` from `conversation_initiation_client_data`
3. `user_id` from `metadata`
4. `user_id` from `dynamic_variables`
5. `caller_id` from `metadata`
6. `conversation_id` (fallback)

### POST `/webhooks/client-data`
Handles conversation initiation for Twilio calls. Queries OpenMemory for user context and returns personalized first messages.

**Authentication**: Header-based authentication (configured in Eleven Labs secrets manager)

**Request Body**:
```json
{
  "caller_id": "+1234567890",
  "agent_id": "agent-id-here",
  "called_number": "+0987654321",
  "call_sid": "call-sid-here"
}
```

**Response**: `conversation_initiation_client_data` JSON format:
```json
{
  "type": "conversation_initiation_client_data",
  "dynamic_variables": {
    "caller_id": "+1234567890",
    "called_number": "+0987654321",
    "call_sid": "call-sid-here",
    "user_context": "User summary from OpenMemory..."
  },
  "conversation_config_override": {
    "agent": {
      "first_message": "Personalized greeting based on user history",
      "language": "en",
      "prompt": {
        "prompt": "System prompt override"
      }
    },
    "tts": {
      "voice_id": "voice-id-here"
    }
  }
}
```

**Features**:
- Automatically caches agent profiles to reduce API calls
- Generates personalized first messages based on OpenMemory user summaries
- Falls back to default agent configuration if personalization fails

### POST `/webhooks/search-data`
Provides in-call memory search functionality as an Eleven Labs Tool.

**Authentication**: Header-based authentication

**Request Body**:
```json
{
  "query": "user preferences",
  "user_id": "user-id-here",
  "limit": 5
}
```

**Response**: 
```json
{
  "status": "success",
  "memories_found": 3,
  "context": "Combined memory context from matching memories...",
  "memories": [
    {
      "id": "memory-id",
      "content": "Memory content...",
      "metadata": {...}
    }
  ]
}
```

**Error Response**:
```json
{
  "detail": "Missing query parameter"
}
```

## Memory Storage Strategy

- **Minimal Processing Approach**: Only extract `system__caller_id` and set it as `user_id`
- Entire `post_call_transcription` webhook payload is stored as-is to OpenMemory
- OpenMemory automatically handles:
  - Text extraction from JSON payload
  - Memory categorization (Episodic, Semantic, Procedural, Emotional, Reflective)
  - Decay rates and memory organization
- **User Identification**: Uses `system__caller_id` (phone number) as the primary user_id for consistent caller identification across all conversations
- All conversations from the same caller (same phone number) are stored with the same `user_id`, making them retrievable together

## Agent Profile Caching

The system automatically caches agent profiles in OpenMemory to avoid repeated API calls:

- Agent profiles are fetched from Eleven Labs API on first use
- Profiles are stored in OpenMemory using `agent_id` as the `user_id` for isolation
- The complete agent payload from the Eleven Labs API is stored as JSON content
- Subsequent requests use cached profiles from OpenMemory, reducing API calls and improving response time
- Cache is automatically updated when agent profiles are fetched from the API
- Agent profiles are stored with metadata filter `{"type": "agent_profile"}` to distinguish them from conversation memories

**Storage Details**:
- **User ID**: `agent_id` (e.g., `"agent_123"`)
- **Content**: Complete agent payload from `/v1/convai/agents/{agent_id}` as JSON string
- **Metadata**: `{"type": "agent_profile", "agent_id": "agent_123"}`
- **Retrieval**: Queried using `user_id=agent_id` and `filters={"type": "agent_profile"}`

## Development

### Project Structure Details

The project follows a modular structure:

- **`main.py`**: FastAPI application entry point with CORS middleware, webhook routers, and health endpoints
- **`config.py`**: Pydantic settings for environment-based configuration using `.env` file
- **`src/clients/openmemory.py`**: OpenMemory API client with methods for:
  - Storing memories (`store_memory`, `store_post_call_payload`)
  - Querying memories (`query_memories`)
  - Getting user summaries (`get_user_summary`)
  - Generating personalized messages (`generate_personalized_message`)
  - Storing agent profiles (`store_agent_profile`)
  - Retrieving agent profiles (`get_agent_profile`)
- **`src/clients/elevenlabs.py`**: Eleven Labs API client for:
  - Fetching agent configurations (`get_agent`) - returns complete agent payload
  - Extracting agent fields (`extract_agent_fields`) - for backward compatibility
- **`src/webhooks/`**: Three webhook handlers:
  - `post_call.py`: Handles post-call webhooks with HMAC validation
  - `client_data.py`: Handles conversation initiation with agent caching
  - `search_data.py`: Handles in-call memory search
- **`src/utils/auth.py`**: Authentication utilities:
  - HMAC signature validation for post-call webhooks
  - Header-based authentication for client-data and search-data webhooks
- **`src/utils/helpers.py`**: Helper functions:
  - User ID extraction from payloads with priority ordering
  - Conversation initiation response building
- **`scripts/`**: Utility scripts for manual operations and testing
- **`data/sql_queries.sql`**: Reference examples for querying agent profiles from OpenMemory

### Testing

**Test the service locally:**

1. Start the service:
```bash
python main.py
```

2. Test the health endpoint:
```bash
curl http://localhost:8000/health
```

3. Test webhooks locally using ngrok:
   - Start ngrok: `ngrok http 8000`
   - Configure webhooks in Eleven Labs to use ngrok URL
   - Make test calls and monitor logs

**Run standalone tests:**

```bash
# Test post-call storage functionality
python tests/test_post_call_storage_standalone.py
```

**Test utility scripts:**

```bash
# Store conversations manually
python scripts/store_conversations.py

# View stored conversations
python scripts/view_stored_conversations.py

# Show user profile
python scripts/show_user_profile.py +1234567890

# Build comprehensive user profile
python scripts/build_comprehensive_user_profile.py

# Generate personalized first message
python scripts/generate_first_message.py
```

**Logging:**

The service uses Python's standard logging module with INFO level by default. Logs include:
- Webhook requests and responses
- OpenMemory operations (storing/querying memories and agent profiles)
- API client calls
- Error messages with stack traces

### Agent Profile Queries

Agent profiles are stored in OpenMemory and can be queried using the OpenMemory API:

```python
from src.clients.openmemory import OpenMemoryClient

openmemory = OpenMemoryClient()

# Get agent profile
agent_profile = await openmemory.get_agent_profile("agent_id_here")

# Store agent profile
await openmemory.store_agent_profile("agent_id_here", agent_data)
```

Agent profiles are stored with:
- `user_id` = `agent_id`
- `filters` = `{"type": "agent_profile", "agent_id": "agent_id_here"}`

### Utility Scripts

The `scripts/` directory contains utility scripts for manual operations:

- **`setup.sh`**: Initial setup script that creates `.env` file and installs dependencies
- **`push_to_github.sh`**: Script to push the repository to GitHub (optional deployment script)
- **`store_conversations.py`**: Manually store conversations from Eleven Labs to OpenMemory
- **`build_comprehensive_user_profile.py`**: Build comprehensive user profiles from stored conversations
- **`show_user_profile.py`**: Display a user's profile directly from OpenMemory
- **`view_stored_conversations.py`**: View stored conversations from local storage results
- **`generate_first_message.py`**: Generate personalized first messages based on user profiles

These scripts are useful for testing, debugging, and manual operations. All scripts require proper environment variables to be set (see `.env` file configuration).

## Security Best Practices

- **Never commit API keys or secrets**: All sensitive credentials should be stored in `.env` file, which is gitignored
- **Use environment variables**: All scripts use environment variables for API keys and configuration
- **Validate webhook signatures**: Post-call webhooks use HMAC signature validation for security
- **Secure header authentication**: Client-data and search-data webhooks use header-based authentication
- **OpenMemory security**: Ensure OpenMemory server is properly secured and accessible only to authorized services

## Troubleshooting

### Webhook Authentication Failures

- **Post-call webhook**: Verify `ELEVENLABS_POST_CALL_HMAC_KEY` matches the secret configured in Eleven Labs
- **Client-data/Search-data webhooks**: Ensure headers are properly configured in Eleven Labs secrets manager

### OpenMemory Connection Issues

- Verify `OPENMEMORY_URL` is correct and accessible
- Check `OPENMEMORY_API_KEY` is valid
- Ensure OpenMemory server is running

### Agent Profile Not Found

- Verify `ELEVENLABS_API_KEY` is valid
- Check agent ID exists in your Eleven Labs workspace
- Review logs for API errors

### Script Errors

- Ensure all required environment variables are set in `.env` file
- Check that OpenMemory and Eleven Labs services are accessible
- Verify API keys are valid and have proper permissions

## Dependencies

The project uses the following key dependencies:

- **FastAPI** (0.109.0): Modern web framework for building APIs
- **Uvicorn** (0.27.0): ASGI server for running FastAPI
- **Pydantic** (2.5.3): Data validation using Python type annotations
- **Pydantic Settings** (2.1.0): Settings management from environment variables
- **HTTPX** (0.26.0): Async HTTP client for API calls
- **Python-dotenv** (1.0.0): Load environment variables from `.env` file
- **Pyngrok** (6.0.0): Python wrapper for ngrok (optional, for local development)

See `requirements.txt` for the complete list of dependencies.

## Environment Variables

All configuration is done through environment variables (loaded from `.env` file):

### Required Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENMEMORY_URL` | OpenMemory server URL | `http://localhost:8080` |
| `OPENMEMORY_API_KEY` | OpenMemory API key for authentication | - |
| `ELEVENLABS_API_KEY` | Eleven Labs API key | - |
| `ELEVENLABS_POST_CALL_HMAC_KEY` | HMAC key for post-call webhook signature validation | - |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ELEVENLABS_CLIENT_DATA_WORKSPACE_SECRET` | Secret for client-data and search-data webhooks (X-Api-Key header) | - |
| `WEBHOOK_STORAGE_PATH` | Webhook file storage path | `data/webhooks` |
| `WEBHOOK_QUARANTINE_PATH` | Quarantine directory path | `data/webhooks/quarantine` |
| `AUDIO_CACHE_TTL` | Audio cache TTL in seconds | `3600` (1 hour) |
| `WEBHOOK_RETENTION_DAYS` | File retention period in days | `30` |
| `MAX_RETRIES` | Maximum API retry attempts | `3` |
| `ANOMALY_DETECTION_ENABLED` | Enable anomaly detection | `true` |
| `ANOMALY_FAILURE_THRESHOLD` | Number of validation failures before alerting | `5` |
| `ANOMALY_WINDOW_SECONDS` | Anomaly detection window in seconds | `300` (5 minutes) |
| `ALERT_ON_QUARANTINE_FAILURES` | Alert when quarantine save fails | `true` |
| `REDIS_URL` | Redis connection URL for distributed caching | - |
| `REDIS_TTL` | Redis cache TTL in seconds | `3600` (1 hour) |
| `FILE_PERMISSIONS_MODE` | File permissions (octal) | `384` (0o600) |
| `ENABLE_ENCRYPTION_AT_REST` | Enable encryption at rest | `false` |

## License

[Add your license here]

## Contributing

[Add contributing guidelines here]

## Support

For issues, questions, or contributions, please open an issue on the GitHub repository.

