# Eleven Labs Agents Open Memory System (ELAOMS)

A Python FastAPI service that integrates Eleven Labs Agents with OpenMemory for persistent, personalized agent memory. This system enables agents to remember past conversations and personalize interactions based on user history.

## Features

- **Post-Call Memory Storage**: Automatically stores entire conversation data to OpenMemory after calls complete
- **Personalized First Messages**: Generates AI-powered personalized greetings based on user's conversation history
- **In-Call Memory Search**: Provides on-demand memory search during conversations via Eleven Labs Tools
- **Agent Profile Caching**: Caches agent configurations locally to reduce API calls

## Architecture

The system consists of three main webhook endpoints:

1. **`/webhooks/post-call`**: Receives post-call webhooks from Eleven Labs and stores entire payload to OpenMemory
2. **`/webhooks/client-data`**: Handles conversation initiation, queries OpenMemory for user context, and returns personalized first messages
3. **`/webhooks/search-data`**: Provides in-call memory search functionality as an Eleven Labs Tool

## Prerequisites

- Python 3.12+
- OpenMemory server running and accessible
- Eleven Labs API key
- (Optional) ngrok for local development

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ElevenLabsAgentsOpenMemorySystem
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file from `.env.example`:
```bash
cp .env.example .env
```

4. Configure your `.env` file with your credentials:
```env
OPENMEMORY_URL=http://localhost:8080
OPENMEMORY_API_KEY=your_openmemory_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
ELEVENLABS_WEBHOOK_SECRET=your_webhook_secret_here
DATABASE_URL=sqlite:///./elaoms.db
NGROK_AUTH_TOKEN=your_ngrok_auth_token_here  # Optional
```

## Running the Service

### Local Development with ngrok

1. Start the FastAPI service:
```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --reload --port 8000
```

2. In a separate terminal, start ngrok to expose the service:
```bash
ngrok http 8000
```

3. Use the ngrok HTTPS URL for your webhook endpoints in Eleven Labs configuration.

### Production

Deploy the FastAPI service to your preferred hosting platform (e.g., AWS, GCP, Heroku, Railway) and configure the webhook URLs in Eleven Labs.

## Configuration in Eleven Labs

### 1. Post-Call Webhook

1. Go to Agents Platform settings
2. Enable post-call webhooks
3. Set webhook URL to: `https://your-domain.com/webhooks/post-call`
4. Configure HMAC secret (store in `ELEVENLABS_WEBHOOK_SECRET`)

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

### POST `/webhooks/post-call`
Receives post-call transcription webhooks from Eleven Labs.

**Authentication**: HMAC signature validation via `ElevenLabs-Signature` header

**Response**: `{"status": "received", "memory_id": "..."}`

### POST `/webhooks/client-data`
Handles conversation initiation for Twilio calls.

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

**Response**: `conversation_initiation_client_data` JSON with personalized first message

### POST `/webhooks/search-data`
Provides in-call memory search functionality.

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
  "context": "Combined memory context...",
  "memories": [...]
}
```

## Memory Storage Strategy

- Entire `post_call_transcription` webhook payloads are stored to OpenMemory
- OpenMemory automatically handles memory categorization (Episodic, Semantic, Procedural, Emotional, Reflective)
- User isolation is maintained using `user_id` from webhook payloads
- OpenMemory manages decay rates and memory organization internally

## Agent Profile Caching

The system automatically caches agent profiles in a local database to avoid repeated API calls:

- Agent profiles are fetched from Eleven Labs API on first use
- Profiles are stored in SQLite/PostgreSQL database
- Subsequent requests use cached profiles
- Cache includes: `agent_id`, `title`, `first_message`, `system_prompt`, `language`, `voice_id`

## Development

### Project Structure

```
elaoms/
├── main.py                 # FastAPI app entry point
├── config.py              # Configuration settings
├── database.py            # Database models and setup
├── openmemory_client.py   # OpenMemory API client
├── elevenlabs_client.py   # Eleven Labs API client
├── webhooks/
│   ├── post_call.py       # Post-call webhook handler
│   ├── client_data.py     # Client data webhook handler
│   └── search_data.py     # Search data webhook handler
├── utils/
│   ├── auth.py            # Authentication utilities
│   └── helpers.py         # Helper functions
└── requirements.txt       # Python dependencies
```

### Testing

Test webhooks locally using ngrok:

1. Start the service: `python main.py`
2. Start ngrok: `ngrok http 8000`
3. Configure webhooks in Eleven Labs to use ngrok URL
4. Make test calls and monitor logs

## Troubleshooting

### Webhook Authentication Failures

- **Post-call webhook**: Verify `ELEVENLABS_WEBHOOK_SECRET` matches the secret configured in Eleven Labs
- **Client-data/Search-data webhooks**: Ensure headers are properly configured in Eleven Labs secrets manager

### OpenMemory Connection Issues

- Verify `OPENMEMORY_URL` is correct and accessible
- Check `OPENMEMORY_API_KEY` is valid
- Ensure OpenMemory server is running

### Agent Profile Not Found

- Verify `ELEVENLABS_API_KEY` is valid
- Check agent ID exists in your Eleven Labs workspace
- Review logs for API errors

## License

[Add your license here]

## Contributing

[Add contributing guidelines here]

