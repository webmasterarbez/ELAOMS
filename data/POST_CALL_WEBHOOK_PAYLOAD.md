# Post-Call Webhook Payload Structure

This document shows the structure of the post-call webhook payload sent by ElevenLabs to the `/webhooks/post-call` endpoint.

## Webhook Types

The post-call webhook can have three different types:

1. **`post_call_transcription`** - Contains the full conversation transcript and analysis
2. **`post_call_audio`** - Contains base64-encoded audio data
3. **`call_initiation_failure`** - Contains failure information if call initiation failed

---

## 1. Post-Call Transcription Webhook

This is the main webhook type that contains the complete conversation data.

### Basic Structure

```json
{
  "type": "post_call_transcription",
  "event_timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "conversation_id": "conv_1234567890abcdef",
    "agent_id": "agent_abcdef123456",
    "status": "completed",
    "transcript": [...],
    "analysis": {...},
    "metadata": {...},
    "conversation_initiation_client_data": {...}
  }
}
```

### Full Example Payload

```json
{
  "type": "post_call_transcription",
  "event_timestamp": "2024-01-15T14:30:00Z",
  "data": {
    "conversation_id": "conv_01jxd5y165f62a0v7gtr6bkg56",
    "agent_id": "agent_abc123def456",
    "status": "completed",
    
    "transcript": [
      {
        "role": "user",
        "content": "Hello, I'd like to schedule an appointment.",
        "timestamp": 1705327800
      },
      {
        "role": "assistant",
        "content": "I'd be happy to help you schedule an appointment. What day works best for you?",
        "timestamp": 1705327805
      },
      {
        "role": "user",
        "content": "How about next Tuesday?",
        "timestamp": 1705327810
      }
    ],
    
    "analysis": {
      "call_successful": true,
      "transcript_summary": "User requested to schedule an appointment for next Tuesday. Agent confirmed availability and scheduled the appointment.",
      "sentiment": "positive",
      "topics": ["appointment", "scheduling"],
      "key_points": [
        "User wants appointment",
        "Tuesday selected",
        "Appointment confirmed"
      ]
    },
    
    "metadata": {
      "start_time_unix_secs": 1705327800,
      "end_time_unix_secs": 1705327900,
      "duration_seconds": 100,
      "caller_id": "+1234567890",
      "from": "+1234567890",
      "to": "+0987654321",
      "user_id": "user_12345",
      "call_sid": "CA1234567890abcdef"
    },
    
    "conversation_initiation_client_data": {
      "user_id": "user_12345",
      "dynamic_variables": {
        "system__caller_id": "+1234567890",
        "caller_name": "John Doe",
        "user_id": "user_12345",
        "custom_field_1": "value1"
      }
    }
  }
}
```

### Key Fields

#### Top Level
- **`type`** (string, required): Always `"post_call_transcription"` for transcription webhooks
- **`event_timestamp`** (string, optional): ISO 8601 timestamp of the event
- **`data`** (object, required): Contains all conversation data

#### Data Object
- **`conversation_id`** (string, required): Unique identifier for the conversation
- **`agent_id`** (string, required): Identifier of the agent that handled the call
- **`status`** (string): Status of the conversation (e.g., "completed", "failed")
- **`transcript`** (array): Array of transcript turns
- **`analysis`** (object): Analysis of the conversation
- **`metadata`** (object): Call metadata
- **`conversation_initiation_client_data`** (object): Data from conversation initiation

#### Transcript Array
Each transcript turn contains:
- **`role`** (string): Either `"user"` or `"assistant"`
- **`content`** (string): The text content of the turn
- **`timestamp`** (number, optional): Unix timestamp of when the turn occurred

#### Analysis Object
- **`call_successful`** (boolean): Whether the call was successful
- **`transcript_summary`** (string): AI-generated summary of the conversation
- **`sentiment`** (string, optional): Sentiment analysis (e.g., "positive", "neutral", "negative")
- **`topics`** (array, optional): Topics discussed in the conversation
- **`key_points`** (array, optional): Key points extracted from the conversation

#### Metadata Object
- **`start_time_unix_secs`** (number): Unix timestamp of call start
- **`end_time_unix_secs`** (number): Unix timestamp of call end
- **`duration_seconds`** (number): Duration of the call in seconds
- **`caller_id`** (string): Phone number of the caller
- **`from`** (string): Source phone number
- **`to`** (string): Destination phone number
- **`user_id`** (string, optional): User identifier
- **`call_sid`** (string, optional): Call session identifier

#### Conversation Initiation Client Data
- **`user_id`** (string, optional): User identifier from initiation
- **`dynamic_variables`** (object): Dynamic variables passed during initiation
  - **`system__caller_id`** (string): System caller ID (most consistent identifier)
  - **`caller_name`** (string, optional): Name of the caller
  - **`user_id`** (string, optional): User identifier
  - Additional custom fields as needed

---

## 2. Post-Call Audio Webhook

Contains base64-encoded audio data.

```json
{
  "type": "post_call_audio",
  "event_timestamp": "2024-01-15T14:30:00Z",
  "data": {
    "conversation_id": "conv_01jxd5y165f62a0v7gtr6bkg56",
    "agent_id": "agent_abc123def456",
    "full_audio": "UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA..."
  }
}
```

### Key Fields
- **`type`**: Always `"post_call_audio"`
- **`data.conversation_id`**: Conversation identifier
- **`data.agent_id`**: Agent identifier
- **`data.full_audio`**: Base64-encoded audio data (can be very large)

---

## 3. Call Initiation Failure Webhook

Contains failure information if call initiation failed.

```json
{
  "type": "call_initiation_failure",
  "event_timestamp": "2024-01-15T14:30:00Z",
  "data": {
    "conversation_id": "conv_01jxd5y165f62a0v7gtr6bkg56",
    "agent_id": "agent_abc123def456",
    "error": "Failed to initiate call",
    "error_code": "INIT_FAILED",
    "error_message": "Unable to connect to phone number"
  }
}
```

### Key Fields
- **`type`**: Always `"call_initiation_failure"`
- **`data.conversation_id`**: Conversation identifier
- **`data.agent_id`**: Agent identifier
- **`data.error`**: Error description
- **`data.error_code`**: Error code
- **`data.error_message`**: Detailed error message

---

## User ID Extraction Priority

The system extracts `user_id` from the payload in the following priority order:

1. **`system__caller_id`** from `data.conversation_initiation_client_data.dynamic_variables` (most consistent for same caller)
2. **`user_id`** from `data.conversation_initiation_client_data`
3. **`user_id`** from `data.metadata`
4. **`user_id`** from `data.conversation_initiation_client_data.dynamic_variables`
5. **`caller_id`** from `data.metadata` (or `from` field)
6. **`external_number`** from `data.metadata.phone_call` (ElevenLabs system field)

If none are found, the system uses `conversation_id` as a last resort.

---

## Authentication

All post-call webhooks are authenticated using HMAC signature validation:

- **Header**: `elevenlabs-signature`
- **Format**: `t=<timestamp>,v0=<hmac_signature>`
- **Algorithm**: HMAC SHA256
- **Payload**: `{timestamp}.{request_body}`

Example header:
```
elevenlabs-signature: t=1705327800,v0=abc123def456...
```

---

## Processing Flow

1. **HMAC Validation** (FIRST - before everything else)
   - Check for `elevenlabs-signature` header
   - Validate timestamp (30-minute tolerance)
   - Validate HMAC signature

2. **File Storage**
   - Save payload to file system
   - For `post_call_transcription`: Save immediately
   - For `post_call_audio`: Cache temporarily (wait for transcription)
   - For `call_initiation_failure`: Save immediately

3. **OpenMemory Storage** (only for `post_call_transcription`)
   - Extract `user_id` from payload
   - Store entire payload as JSON string to OpenMemory
   - Store agent profile in background if `agent_id` is present

---

## Response Format

### Success Response (200 OK)
```json
{
  "status": "received",
  "memory_id": "memory-id-from-openmemory"
}
```

### Error Responses

**401 Unauthorized** (HMAC validation failed):
```json
{
  "detail": "Missing signature header" | "Invalid signature format" | "Timestamp too old" | "Invalid signature"
}
```

**400 Bad Request** (Invalid JSON):
```json
{
  "detail": "Invalid JSON payload"
}
```

**500 Internal Server Error** (Storage failure):
```json
{
  "detail": "Failed to store memory"
}
```

---

## Notes

- The entire payload is stored as-is to OpenMemory (converted to JSON string)
- Only `post_call_transcription` webhooks are stored to OpenMemory
- Audio webhooks are cached temporarily until transcription arrives
- Failure webhooks are saved to file system but not stored to OpenMemory
- Agent profiles are fetched and stored in background tasks after transcription storage


