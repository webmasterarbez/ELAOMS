# Requirements Document
## Eleven Labs Agents Open Memory System (ELAOMS)

**Version:** 1.0.0  
**Date:** 2024  
**Status:** Production

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Overview](#system-overview)
3. [Functional Requirements](#functional-requirements)
4. [Non-Functional Requirements](#non-functional-requirements)
5. [Security Requirements](#security-requirements)
6. [Performance Requirements](#performance-requirements)
7. [Integration Requirements](#integration-requirements)
8. [Configuration Requirements](#configuration-requirements)
9. [API Requirements](#api-requirements)
10. [Data Storage Requirements](#data-storage-requirements)
11. [Error Handling Requirements](#error-handling-requirements)
12. [Observability Requirements](#observability-requirements)
13. [Deployment Requirements](#deployment-requirements)
14. [Testing Requirements](#testing-requirements)

---

## Executive Summary

The Eleven Labs Agents Open Memory System (ELAOMS) is a Python FastAPI service that integrates Eleven Labs Agents with OpenMemory for persistent, personalized agent memory. The system enables AI agents to remember past conversations and personalize interactions based on user history through three primary webhook endpoints that handle post-call storage, conversation initiation, and in-call memory search.

**Key Capabilities:**
- Automatic storage of conversation data to OpenMemory after calls complete
- AI-powered personalized greetings based on user conversation history
- In-call memory search functionality via Eleven Labs Tools
- Agent profile caching to reduce API calls
- Secure webhook processing with HMAC validation
- File-based webhook payload storage with security and retention policies

---

## System Overview

### Architecture

ELAOMS is built as a FastAPI application that acts as a middleware service between Eleven Labs Agents Platform and OpenMemory. The system processes three types of webhooks:

1. **Post-Call Webhook** (`/webhooks/post-call`): Receives and stores complete conversation data after calls complete
2. **Client-Data Webhook** (`/webhooks/client-data`): Handles conversation initiation with personalized first messages
3. **Search-Data Webhook** (`/webhooks/search-data`): Provides in-call memory search as an Eleven Labs Tool

### Technology Stack

- **Framework:** FastAPI 0.109.0
- **Server:** Uvicorn 0.27.0
- **HTTP Client:** HTTPX 0.26.0
- **Configuration:** Pydantic Settings 2.1.0
- **Caching:** Redis 5.0.1 (optional), in-memory fallback
- **Encryption:** Cryptography 41.0.7 (optional)
- **Python Version:** 3.12+

### Key Components

- **Webhook Handlers** (`src/webhooks/`): Process incoming webhooks from Eleven Labs
- **API Clients** (`src/clients/`): Interact with Eleven Labs and OpenMemory APIs
- **Utilities** (`src/utils/`): Authentication, storage, helpers, and anomaly detection
- **Configuration** (`config.py`): Centralized settings management

---

## Functional Requirements

### FR-1: Post-Call Webhook Processing

**FR-1.1:** The system MUST receive POST requests at `/webhooks/post-call` endpoint.

**FR-1.2:** The system MUST validate HMAC signatures before processing any webhook payload.

**FR-1.3:** The system MUST parse the `elevenlabs-signature` header in the format `t=timestamp,v0=hash`.

**FR-1.4:** The system MUST validate timestamp with a 30-minute tolerance window.

**FR-1.5:** The system MUST use constant-time comparison (`hmac.compare_digest`) for signature validation to prevent timing attacks.

**FR-1.6:** The system MUST strip whitespace from parsed signature header parts to handle variations in header formatting.

**FR-1.7:** The system MUST read the request body as bytes before validation.

**FR-1.8:** The system MUST parse the payload as JSON after successful HMAC validation.

**FR-1.9:** The system MUST extract user_id from payload using the following priority order:
1. `system__caller_id` from `dynamic_variables` (most consistent for same caller)
2. `user_id` from `conversation_initiation_client_data`
3. `user_id` from `metadata`
4. `user_id` from `dynamic_variables`
5. `caller_id` from `metadata`
6. `conversation_id` (fallback)

**FR-1.10:** The system MUST store the entire post-call webhook payload to OpenMemory for `post_call_transcription` webhook types.

**FR-1.11:** The system MUST save webhook payloads to local filesystem in `data/webhooks/` directory structure.

**FR-1.12:** The system MUST schedule background tasks to store agent profiles after successful webhook processing.

**FR-1.13:** The system MUST return appropriate HTTP status codes:
- `401 Unauthorized` for HMAC validation failures
- `400 Bad Request` for invalid JSON or missing required fields
- `500 Internal Server Error` for storage failures
- `200 OK` with `{"status": "received", "memory_id": "..."}` for successful processing

**FR-1.14:** The system MUST handle three webhook types:
- `post_call_transcription`: Store to OpenMemory and save files
- `post_call_audio`: Cache temporarily (don't save until transcription arrives)
- `call_initiation_failure`: Save immediately

### FR-2: Client-Data Webhook Processing

**FR-2.1:** The system MUST receive POST requests at `/webhooks/client-data` endpoint.

**FR-2.2:** The system MUST validate header-based authentication before processing.

**FR-2.3:** The system MUST parse request body containing:
- `caller_id`: Phone number of caller
- `agent_id`: Agent identifier (required)
- `called_number`: Number being called
- `call_sid`: Call session identifier

**FR-2.4:** The system MUST query OpenMemory for user summary using `caller_id` as `user_id`.

**FR-2.5:** The system MUST fetch or retrieve cached agent profile from OpenMemory.

**FR-2.6:** The system MUST generate personalized first messages using OpenMemory's query API.

**FR-2.7:** The system MUST return `conversation_initiation_client_data` JSON format with:
- `type`: "conversation_initiation_client_data"
- `dynamic_variables`: Caller information and user context
- `conversation_config_override`: Agent configuration overrides (first_message, language, voice_id, system_prompt)

**FR-2.8:** The system MUST fallback to default agent configuration if personalization fails.

**FR-2.9:** The system MUST NOT store agent profiles during client-data processing (storage happens in post-call webhook).

### FR-3: Search-Data Webhook Processing

**FR-3.1:** The system MUST receive POST requests at `/webhooks/search-data` endpoint.

**FR-3.2:** The system MUST validate header-based authentication before processing.

**FR-3.3:** The system MUST parse request body containing:
- `query` or `search_query`: Search query string (required)
- `user_id` or `caller_id`: User identifier (optional, defaults to "unknown")
- `limit`: Maximum number of results (default: 5)

**FR-3.4:** The system MUST query OpenMemory for relevant memories matching the search query.

**FR-3.5:** The system MUST return formatted response with:
- `status`: "success"
- `memories_found`: Number of memories found
- `context`: Combined memory context as text
- `memories`: Array of matching memory objects

**FR-3.6:** The system MUST return empty result set if no memories found.

### FR-4: Webhook Payload File Storage

**FR-4.1:** The system MUST save webhook payloads to local filesystem.

**FR-4.2:** The system MUST organize files in directory structure: `{base_path}/{directory_name}/{conversation_id}_{webhook_type}.{ext}`

**FR-4.3:** The system MUST determine directory name using priority: `agent_id` > `caller_phone` > `conversation_id`.

**FR-4.4:** The system MUST support three file types:
- Transcription webhooks: JSON files (`.json`)
- Audio webhooks: MP3 files (`.mp3`)
- Failure webhooks: JSON files (`.json`)

**FR-4.5:** The system MUST sanitize all identifiers (conversation_id, caller_phone, agent_id) before using in file paths.

**FR-4.6:** The system MUST handle file conflicts by appending timestamp to filename.

**FR-4.7:** The system MUST save metadata files (`.metadata.json`) alongside webhook files containing:
- `webhook_type`: Type of webhook
- `validated`: Whether HMAC validation passed
- `timestamp`: ISO format timestamp
- `file_path`: Path to webhook file
- `request_id`: Request tracking ID
- `file_size`: Size of file in bytes
- `directory_name`: Directory where file is stored

**FR-4.8:** The system MUST support quarantine directory for unvalidated files (optional feature).

**FR-4.9:** The system MUST move files from quarantine to main storage after successful validation.

### FR-5: Agent Profile Caching

**FR-5.1:** The system MUST cache agent profiles in OpenMemory using `agent_id` as `user_id`.

**FR-5.2:** The system MUST store complete agent payload from Eleven Labs API as JSON content.

**FR-5.3:** The system MUST store agent profiles with metadata filter `{"type": "agent_profile", "agent_id": "..."}`.

**FR-5.4:** The system MUST check OpenMemory cache before fetching from Eleven Labs API.

**FR-5.5:** The system MUST fetch agent profiles from Eleven Labs API endpoint `/v1/convai/agents/{agent_id}`.

**FR-5.6:** The system MUST extract commonly used fields for backward compatibility:
- `agent_id`
- `title` (from `name`)
- `first_message`
- `system_prompt`
- `language`
- `voice_id`

**FR-5.7:** The system MUST store agent profiles in background tasks after post-call webhook processing.

**FR-5.8:** The system MUST NOT store agent profiles during client-data webhook processing (only fetch/cache lookup).

### FR-6: Audio Webhook Caching

**FR-6.1:** The system MUST cache audio webhooks temporarily until transcription arrives.

**FR-6.2:** The system MUST support Redis caching for distributed environments (optional).

**FR-6.3:** The system MUST fallback to in-memory cache if Redis is unavailable.

**FR-6.4:** The system MUST decode base64 audio data from `post_call_audio` webhook payloads.

**FR-6.5:** The system MUST store audio cache entries with timestamp for TTL expiration.

**FR-6.6:** The system MUST process cached audio when transcription webhook arrives and save audio file.

**FR-6.7:** The system MUST expire audio cache entries after TTL period (default: 1 hour).

### FR-7: User ID Extraction

**FR-7.1:** The system MUST extract user_id from webhook payloads using priority ordering.

**FR-7.2:** The system MUST log which user_id source was used for debugging.

**FR-7.3:** The system MUST use `system__caller_id` as primary identifier for consistent caller identification.

**FR-7.4:** The system MUST fallback to `conversation_id` if no user_id found.

### FR-8: Personalized Message Generation

**FR-8.1:** The system MUST query OpenMemory for user summary during conversation initiation.

**FR-8.2:** The system MUST generate personalized first messages using OpenMemory query API.

**FR-8.3:** The system MUST include user context in dynamic variables (limited to 500 characters).

**FR-8.4:** The system MUST fallback to default agent first_message if personalization fails.

### FR-9: Background Task Processing

**FR-9.1:** The system MUST use FastAPI BackgroundTasks for asynchronous agent profile storage.

**FR-9.2:** The system MUST create new client instances in background tasks (not reuse main thread clients).

**FR-9.3:** The system MUST handle background task failures gracefully without affecting main webhook response.

**FR-9.4:** The system MUST close all client connections in background tasks after completion.

---

## Non-Functional Requirements

### NFR-1: Reliability

**NFR-1.1:** The system MUST handle transient network failures with retry logic.

**NFR-1.2:** The system MUST continue processing even if file storage fails (log error but continue).

**NFR-1.3:** The system MUST gracefully degrade when optional services (Redis, encryption) are unavailable.

**NFR-1.4:** The system MUST not fail webhook processing if background tasks fail.

### NFR-2: Maintainability

**NFR-2.1:** The system MUST use structured logging with request IDs for traceability.

**NFR-2.2:** The system MUST organize code in modular structure (webhooks, clients, utils).

**NFR-2.3:** The system MUST use type hints for all function parameters and return values.

**NFR-2.4:** The system MUST provide comprehensive error messages in logs.

### NFR-3: Scalability

**NFR-3.1:** The system MUST support horizontal scaling through stateless design.

**NFR-3.2:** The system MUST support distributed caching via Redis for multi-instance deployments.

**NFR-3.3:** The system MUST handle concurrent webhook requests efficiently.

### NFR-4: Usability

**NFR-4.1:** The system MUST provide clear error messages in HTTP responses.

**NFR-4.2:** The system MUST provide API documentation via Swagger UI at `/docs`.

**NFR-4.3:** The system MUST provide health check endpoint at `/health`.

---

## Security Requirements

### SEC-1: HMAC Signature Validation

**SEC-1.1:** The system MUST validate HMAC signatures for all post-call webhooks.

**SEC-1.2:** The system MUST use constant-time comparison (`hmac.compare_digest`) to prevent timing attacks.

**SEC-1.3:** The system MUST validate timestamp with 30-minute tolerance to prevent replay attacks.

**SEC-1.4:** The system MUST strip whitespace from signature header parts to handle formatting variations.

**SEC-1.5:** The system MUST reject requests with missing or invalid signature headers (401 Unauthorized).

**SEC-1.6:** The system MUST compute HMAC signature as: `HMAC-SHA256(secret, timestamp + "." + payload)`.

**SEC-1.7:** The system MUST compare computed signature with header signature using `hmac.compare_digest`.

### SEC-2: Header-Based Authentication

**SEC-2.1:** The system MUST validate header-based authentication for client-data and search-data webhooks.

**SEC-2.2:** The system MUST check for presence of `authorization` or `x-api-key` headers.

**SEC-2.3:** The system MUST be extensible to validate against Eleven Labs secrets manager (TODO in code).

### SEC-3: Input Sanitization

**SEC-3.1:** The system MUST sanitize all identifiers before using in file paths.

**SEC-3.2:** The system MUST prevent path traversal attacks by removing `..`, `../`, `..\\` patterns.

**SEC-3.3:** The system MUST replace unsafe characters (`<>:"|?*` and control characters) with safe alternatives.

**SEC-3.4:** The system MUST handle Windows reserved names (CON, PRN, AUX, NUL, COM1-9, LPT1-9).

**SEC-3.5:** The system MUST limit filename length to 255 characters.

**SEC-3.6:** The system MUST normalize path separators and prevent absolute paths.

**SEC-3.7:** The system MUST encode non-ASCII characters safely (ASCII fallback).

### SEC-4: File System Security

**SEC-4.1:** The system MUST set file permissions to `0o600` (read/write for owner only) by default.

**SEC-4.2:** The system MUST set directory permissions to `0o700` (read/write/execute for owner only).

**SEC-4.3:** The system MUST support configurable file permissions via `FILE_PERMISSIONS_MODE` setting.

**SEC-4.4:** The system MUST handle permission setting failures gracefully (log warning, continue).

### SEC-5: Encryption at Rest

**SEC-5.1:** The system MUST support optional encryption at rest using Fernet (cryptography library).

**SEC-5.2:** The system MUST require `ENCRYPTION_KEY` environment variable when encryption is enabled.

**SEC-5.3:** The system MUST encrypt files after writing if `enable_encryption_at_rest` is true.

**SEC-5.4:** The system MUST handle encryption failures gracefully (log error, continue without encryption).

**SEC-5.5:** The system MUST use Fernet symmetric encryption for file encryption.

### SEC-6: Quarantine System

**SEC-6.1:** The system MUST support quarantine directory for unvalidated files.

**SEC-6.2:** The system MUST save unvalidated files to quarantine path before HMAC validation.

**SEC-6.3:** The system MUST move files from quarantine to main storage after successful validation.

**SEC-6.4:** The system MUST track quarantine failures and alert on spikes (configurable).

**SEC-6.5:** The system MUST clean up old quarantine files (default: 7 days retention).

### SEC-7: Anomaly Detection

**SEC-7.1:** The system MUST track validation failures per IP address.

**SEC-7.2:** The system MUST detect anomaly patterns (configurable threshold, default: 5 failures in 5 minutes).

**SEC-7.3:** The system MUST log anomaly detections with structured data (IP, failure count, window).

**SEC-7.4:** The system MUST support IP throttling based on anomaly detection (optional).

**SEC-7.5:** The system MUST track rate limit hits and alert on spikes.

**SEC-7.6:** The system MUST track quarantine save failures and alert on spikes.

---

## Performance Requirements

### PERF-1: Caching

**PERF-1.1:** The system MUST support Redis caching for distributed environments.

**PERF-1.2:** The system MUST fallback to in-memory cache if Redis is unavailable.

**PERF-1.3:** The system MUST cache audio webhooks with configurable TTL (default: 1 hour).

**PERF-1.4:** The system MUST cache agent profiles in OpenMemory to reduce API calls.

**PERF-1.5:** The system MUST expire cache entries based on TTL configuration.

**PERF-1.6:** The system MUST clean up expired cache entries periodically.

### PERF-2: Retry Logic

**PERF-2.1:** The system MUST implement retry logic with exponential backoff for API calls.

**PERF-2.2:** The system MUST support configurable maximum retries (default: 3).

**PERF-2.3:** The system MUST retry on transient errors (network failures, 429 rate limits).

**PERF-2.4:** The system MUST NOT retry on 4xx errors (except 429).

**PERF-2.5:** The system MUST use exponential backoff: 1s, 2s, 4s, ... between retries.

### PERF-3: Rate Limiting

**PERF-3.1:** The system MUST support configurable rate limiting per minute.

**PERF-3.2:** The system MUST support rate limiting per user agent.

**PERF-3.3:** The system MUST support rate limiting per API key.

**PERF-3.4:** The system MUST track rate limit hits and log warnings.

**PERF-3.5:** The system MUST return appropriate HTTP status (429 Too Many Requests) when rate limited.

### PERF-4: File Cleanup

**PERF-4.1:** The system MUST support configurable file retention period (default: 30 days).

**PERF-4.2:** The system MUST clean up old webhook files beyond retention period.

**PERF-4.3:** The system MUST clean up old quarantine files (default: 7 days).

**PERF-4.4:** The system MUST support configurable cleanup frequency (request-based or time-based).

**PERF-4.5:** The system MUST track cleanup statistics (files deleted, bytes freed).

### PERF-5: Background Processing

**PERF-5.1:** The system MUST use background tasks for non-critical operations (agent profile storage).

**PERF-5.2:** The system MUST not block webhook response waiting for background tasks.

**PERF-5.3:** The system MUST handle background task failures without affecting main response.

---

## Integration Requirements

### INT-1: Eleven Labs Agents API

**INT-1.1:** The system MUST integrate with Eleven Labs Agents API at `https://api.elevenlabs.io/v1`.

**INT-1.2:** The system MUST authenticate using `xi-api-key` header with API key.

**INT-1.3:** The system MUST fetch agent configurations from `/convai/agents/{agent_id}` endpoint.

**INT-1.4:** The system MUST handle API errors (404, 429, 5xx) appropriately.

**INT-1.5:** The system MUST support retry logic for transient API failures.

**INT-1.6:** The system MUST use 30-second timeout for API requests.

### INT-2: OpenMemory API

**INT-2.1:** The system MUST integrate with OpenMemory API (configurable URL, default: `http://localhost:8080`).

**INT-2.2:** The system MUST authenticate using `X-API-Key` header.

**INT-2.3:** The system MUST store memories via `/memory/add` endpoint.

**INT-2.4:** The system MUST query memories via `/memory/query` endpoint.

**INT-2.5:** The system MUST retrieve user summaries via `/users/{user_id}/summary` endpoint.

**INT-2.6:** The system MUST handle 404 responses gracefully (user not found, no summary available).

**INT-2.7:** The system MUST use 30-second timeout for API requests.

### INT-3: Redis Integration

**INT-3.1:** The system MUST support optional Redis integration for distributed caching.

**INT-3.2:** The system MUST connect to Redis using URL from `REDIS_URL` environment variable.

**INT-3.3:** The system MUST fallback to in-memory cache if Redis is unavailable.

**INT-3.4:** The system MUST handle Redis connection failures gracefully.

**INT-3.5:** The system MUST use configurable TTL for Redis cache entries (default: 1 hour).

### INT-4: Twilio Webhook Support

**INT-4.1:** The system MUST accept Twilio webhook format for client-data webhooks.

**INT-4.2:** The system MUST extract `caller_id`, `called_number`, `call_sid` from Twilio payload.

**INT-4.3:** The system MUST use `caller_id` (phone number) as consistent user identifier.

---

## Configuration Requirements

### CONF-1: Environment Variables

**CONF-1.1:** The system MUST load configuration from `.env` file using pydantic-settings.

**CONF-1.2:** The system MUST support the following required environment variables:
- `OPENMEMORY_URL`: OpenMemory server URL
- `OPENMEMORY_API_KEY`: OpenMemory API key
- `ELEVENLABS_API_KEY`: Eleven Labs API key
- `ELEVENLABS_WEBHOOK_SECRET`: Webhook secret for HMAC validation

**CONF-1.3:** The system MUST support the following optional environment variables:
- `NGROK_AUTH_TOKEN`: ngrok authentication token (for local development)
- `REDIS_URL`: Redis connection URL (for distributed caching)
- `ENCRYPTION_KEY`: Encryption key for encryption at rest

### CONF-2: Webhook Storage Configuration

**CONF-2.1:** The system MUST support configurable webhook storage path (default: `data/webhooks`).

**CONF-2.2:** The system MUST support configurable quarantine path (default: `data/webhooks/quarantine`).

**CONF-2.3:** The system MUST support configurable payload size limits:
- `MAX_WEBHOOK_PAYLOAD_SIZE`: Default limit (10MB)
- `MAX_TRANSCRIPTION_PAYLOAD_SIZE`: Transcription limit (10MB)
- `MAX_AUDIO_PAYLOAD_SIZE`: Audio limit (50MB, larger due to base64)
- `MAX_FAILURE_PAYLOAD_SIZE`: Failure limit (5MB)

**CONF-2.4:** The system MUST support configurable retention period (default: 30 days).

**CONF-2.5:** The system MUST support configurable file permissions (default: `0o600`).

### CONF-3: Caching Configuration

**CONF-3.1:** The system MUST support configurable audio cache TTL (default: 1 hour).

**CONF-3.2:** The system MUST support configurable Redis TTL (default: 1 hour).

**CONF-3.3:** The system MUST support enabling/disabling Redis caching.

### CONF-4: Security Configuration

**CONF-4.1:** The system MUST support enabling/disabling encryption at rest.

**CONF-4.2:** The system MUST support enabling/disabling anomaly detection.

**CONF-4.3:** The system MUST support configurable anomaly detection threshold (default: 5 failures).

**CONF-4.4:** The system MUST support configurable anomaly detection window (default: 5 minutes).

**CONF-4.5:** The system MUST support enabling/disabling quarantine failure alerts.

### CONF-5: Performance Configuration

**CONF-5.1:** The system MUST support configurable maximum retries (default: 3).

**CONF-5.2:** The system MUST support configurable rate limits (optional, disabled by default).

**CONF-5.3:** The system MUST support configurable cleanup frequency (request-based or time-based).

---

## API Requirements

### API-1: Root Endpoint

**API-1.1:** The system MUST provide GET endpoint at `/` returning service information:
```json
{
  "service": "Eleven Labs Agents Open Memory System (ELAOMS)",
  "version": "1.0.0",
  "status": "running"
}
```

### API-2: Health Check Endpoint

**API-2.1:** The system MUST provide GET endpoint at `/health` returning:
```json
{
  "status": "healthy"
}
```

### API-3: Post-Call Webhook Endpoint

**API-3.1:** Endpoint: `POST /webhooks/post-call`

**API-3.2:** Authentication: HMAC signature validation via `elevenlabs-signature` header

**API-3.3:** Request: Complete post-call webhook payload from Eleven Labs (JSON)

**API-3.4:** Response (Success): `200 OK`
```json
{
  "status": "received",
  "memory_id": "memory-id-from-openmemory"
}
```

**API-3.5:** Response (HMAC Failure): `401 Unauthorized`
```json
{
  "detail": "Missing signature header" | "Invalid signature format" | "Timestamp too old" | "Invalid signature"
}
```

**API-3.6:** Response (Invalid JSON): `400 Bad Request`
```json
{
  "detail": "Invalid JSON payload"
}
```

**API-3.7:** Response (Storage Failure): `500 Internal Server Error`
```json
{
  "detail": "Failed to store memory"
}
```

### API-4: Client-Data Webhook Endpoint

**API-4.1:** Endpoint: `POST /webhooks/client-data`

**API-4.2:** Authentication: Header-based authentication

**API-4.3:** Request Body:
```json
{
  "caller_id": "+1234567890",
  "agent_id": "agent-id-here",
  "called_number": "+0987654321",
  "call_sid": "call-sid-here"
}
```

**API-4.4:** Response: `conversation_initiation_client_data` format
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
      "first_message": "Personalized greeting...",
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

**API-4.5:** Response (Missing agent_id): `400 Bad Request`
```json
{
  "detail": "Missing agent_id"
}
```

**API-4.6:** Response (Authentication Failure): `401 Unauthorized`
```json
{
  "detail": "Invalid authentication"
}
```

### API-5: Search-Data Webhook Endpoint

**API-5.1:** Endpoint: `POST /webhooks/search-data`

**API-5.2:** Authentication: Header-based authentication

**API-5.3:** Request Body:
```json
{
  "query": "user preferences",
  "user_id": "user-id-here",
  "limit": 5
}
```

**API-5.4:** Response (Success with Results):
```json
{
  "status": "success",
  "memories_found": 3,
  "context": "Combined memory context...",
  "memories": [
    {
      "id": "memory-id",
      "content": "Memory content...",
      "metadata": {...}
    }
  ]
}
```

**API-5.5:** Response (Success, No Results):
```json
{
  "status": "success",
  "memories_found": 0,
  "context": "No relevant memories found.",
  "memories": []
}
```

**API-5.6:** Response (Missing Query): `400 Bad Request`
```json
{
  "detail": "Missing query parameter"
}
```

**API-5.7:** Response (Search Failure): `500 Internal Server Error`
```json
{
  "detail": "Failed to search memories"
}
```

---

## Data Storage Requirements

### DS-1: OpenMemory Storage

**DS-1.1:** The system MUST store post-call webhook payloads as JSON strings in OpenMemory.

**DS-1.2:** The system MUST use `user_id` extracted from payload for memory isolation.

**DS-1.3:** The system MUST store metadata filters:
- `conversation_id`: Conversation identifier
- `agent_id`: Agent identifier
- `event_type`: Webhook type
- `event_timestamp`: Event timestamp

**DS-1.4:** The system MUST store agent profiles with:
- `user_id`: `agent_id` (for isolation)
- `metadata`: `{"type": "agent_profile", "agent_id": "..."}`
- `content`: Complete agent payload as JSON string

**DS-1.5:** The system MUST rely on OpenMemory for automatic text extraction and categorization.

### DS-2: File System Storage

**DS-2.1:** The system MUST store webhook payloads in directory structure: `{base_path}/{directory_name}/`

**DS-2.2:** The system MUST use filename format: `{conversation_id}_{webhook_type}.{ext}`

**DS-2.3:** The system MUST save metadata files alongside webhook files: `{filename}.metadata.json`

**DS-2.4:** The system MUST organize files by:
- Agent ID (for failure webhooks)
- Caller phone number (for transcription/audio webhooks)
- Conversation ID (fallback)

**DS-2.5:** The system MUST support file conflict resolution (append timestamp).

**DS-2.6:** The system MUST maintain file and directory permissions as configured.

### DS-3: Cache Storage

**DS-3.1:** The system MUST cache audio webhooks with TTL expiration.

**DS-3.2:** The system MUST support Redis cache for distributed environments.

**DS-3.3:** The system MUST support in-memory cache as fallback.

**DS-3.4:** The system MUST store cache entries with timestamp for expiration checking.

---

## Error Handling Requirements

### ERR-1: Webhook Processing Errors

**ERR-1.1:** The system MUST handle request body read errors and return `400 Bad Request`.

**ERR-1.2:** The system MUST handle JSON parsing errors and return `400 Bad Request`.

**ERR-1.3:** The system MUST handle HMAC validation errors and return `401 Unauthorized`.

**ERR-1.4:** The system MUST handle missing required fields and return `400 Bad Request`.

**ERR-1.5:** The system MUST log all errors with stack traces for debugging.

### ERR-2: API Client Errors

**ERR-2.1:** The system MUST handle OpenMemory API errors gracefully.

**ERR-2.2:** The system MUST handle Eleven Labs API errors with retry logic.

**ERR-2.3:** The system MUST handle 404 responses (agent not found, user not found) appropriately.

**ERR-2.4:** The system MUST handle 429 rate limit responses with retry logic.

**ERR-2.5:** The system MUST handle network timeouts and connection errors.

### ERR-3: File Storage Errors

**ERR-3.1:** The system MUST handle file write errors gracefully (log error, continue processing).

**ERR-3.2:** The system MUST handle permission setting errors gracefully (log warning, continue).

**ERR-3.3:** The system MUST handle encryption errors gracefully (log error, continue without encryption).

**ERR-3.4:** The system MUST handle directory creation errors.

**ERR-3.5:** The system MUST handle file move errors (quarantine to main storage).

### ERR-4: Background Task Errors

**ERR-4.1:** The system MUST handle background task failures without affecting main response.

**ERR-4.2:** The system MUST log background task errors with full stack traces.

**ERR-4.3:** The system MUST close client connections even if background tasks fail.

---

## Observability Requirements

### OBS-1: Logging

**OBS-1.1:** The system MUST use structured logging with consistent format.

**OBS-1.2:** The system MUST log at appropriate levels:
- `INFO`: Normal operations, successful processing
- `WARNING`: Recoverable errors, fallbacks, anomalies
- `ERROR`: Unrecoverable errors, exceptions
- `DEBUG`: Detailed debugging information

**OBS-1.3:** The system MUST include request IDs in all log entries for traceability.

**OBS-1.4:** The system MUST log webhook processing with:
- Request ID
- Client IP
- User agent
- Webhook type
- Processing time
- Result status

**OBS-1.5:** The system MUST log HMAC validation results with:
- Request ID
- Timestamp age
- Validation result
- Client IP

**OBS-1.6:** The system MUST log API calls with:
- Endpoint
- Status code
- Response time
- Retry attempts (if applicable)

**OBS-1.7:** The system MUST log file operations with:
- File path
- File size
- Operation type (save, move, delete)
- Validation status

**OBS-1.8:** The system MUST log anomaly detections with structured data:
- Anomaly type
- Client IP
- Failure count
- Time window
- Request ID

### OBS-2: Metrics

**OBS-2.1:** The system MUST track webhook processing metrics (count, success rate, latency).

**OBS-2.2:** The system MUST track API call metrics (count, success rate, latency, retries).

**OBS-2.3:** The system MUST track file storage metrics (files saved, bytes stored, cleanup stats).

**OBS-2.4:** The system MUST track cache metrics (hits, misses, expiration, cleanup).

**OBS-2.5:** The system MUST track anomaly detection metrics (failures per IP, rate limit hits).

### OBS-3: Health Monitoring

**OBS-3.1:** The system MUST provide health check endpoint for monitoring.

**OBS-3.2:** The system MUST log service startup and shutdown events.

**OBS-3.3:** The system MUST log configuration loading and validation.

---

## Deployment Requirements

### DEP-1: Environment Setup

**DEP-1.1:** The system MUST run on Python 3.12+.

**DEP-1.2:** The system MUST install dependencies from `requirements.txt`.

**DEP-1.3:** The system MUST load configuration from `.env` file or environment variables.

**DEP-1.4:** The system MUST create required directories on startup (webhook storage, quarantine).

### DEP-2: Service Deployment

**DEP-2.1:** The system MUST support deployment via Uvicorn ASGI server.

**DEP-2.2:** The system MUST support deployment via Gunicorn with Uvicorn workers for production.

**DEP-2.3:** The system MUST support CORS middleware for cross-origin requests.

**DEP-2.4:** The system MUST bind to `0.0.0.0:8000` by default (configurable).

### DEP-3: Production Considerations

**DEP-3.1:** The system MUST use HTTPS in production (handled by reverse proxy/load balancer).

**DEP-3.2:** The system MUST set secure file permissions in production.

**DEP-3.3:** The system MUST use environment variables for all secrets (never hardcode).

**DEP-3.4:** The system MUST support horizontal scaling (stateless design).

**DEP-3.5:** The system MUST support Redis for distributed caching in multi-instance deployments.

### DEP-4: Local Development

**DEP-4.1:** The system MUST support local development with ngrok for webhook testing.

**DEP-4.2:** The system MUST provide setup script (`scripts/setup.sh`) for initial configuration.

**DEP-4.3:** The system MUST support auto-reload during development (uvicorn --reload).

---

## Testing Requirements

### TEST-1: Unit Testing

**TEST-1.1:** The system MUST have unit tests for utility functions (user ID extraction, filename sanitization).

**TEST-1.2:** The system MUST have unit tests for authentication functions (HMAC validation).

**TEST-1.3:** The system MUST have unit tests for file storage functions.

### TEST-2: Integration Testing

**TEST-2.1:** The system MUST have integration tests for webhook endpoints.

**TEST-2.2:** The system MUST have integration tests for API client interactions.

**TEST-2.3:** The system MUST have integration tests for OpenMemory storage operations.

### TEST-3: End-to-End Testing

**TEST-3.1:** The system MUST support end-to-end testing with mock Eleven Labs webhooks.

**TEST-3.2:** The system MUST support end-to-end testing with OpenMemory test instance.

**TEST-3.3:** The system MUST have standalone test scripts for manual testing.

### TEST-4: Security Testing

**TEST-4.1:** The system MUST test HMAC signature validation with valid and invalid signatures.

**TEST-4.2:** The system MUST test timing attack prevention (constant-time comparison).

**TEST-4.3:** The system MUST test input sanitization with malicious inputs.

**TEST-4.4:** The system MUST test path traversal prevention.

---

## Appendix A: Configuration Reference

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENMEMORY_URL` | Yes | `http://localhost:8080` | OpenMemory server URL |
| `OPENMEMORY_API_KEY` | Yes | - | OpenMemory API key |
| `ELEVENLABS_API_KEY` | Yes | - | Eleven Labs API key |
| `ELEVENLABS_WEBHOOK_SECRET` | Yes | - | Webhook secret for HMAC |
| `NGROK_AUTH_TOKEN` | No | - | ngrok auth token (local dev) |
| `REDIS_URL` | No | - | Redis URL (optional caching) |
| `ENCRYPTION_KEY` | No | - | Encryption key (if encryption enabled) |
| `WEBHOOK_STORAGE_PATH` | No | `data/webhooks` | Webhook file storage path |
| `WEBHOOK_QUARANTINE_PATH` | No | `data/webhooks/quarantine` | Quarantine directory path |
| `MAX_WEBHOOK_PAYLOAD_SIZE` | No | `10485760` (10MB) | Default payload size limit |
| `MAX_TRANSCRIPTION_PAYLOAD_SIZE` | No | `10485760` (10MB) | Transcription payload limit |
| `MAX_AUDIO_PAYLOAD_SIZE` | No | `52428800` (50MB) | Audio payload limit |
| `MAX_FAILURE_PAYLOAD_SIZE` | No | `5242880` (5MB) | Failure payload limit |
| `AUDIO_CACHE_TTL` | No | `3600` (1 hour) | Audio cache TTL in seconds |
| `WEBHOOK_RETENTION_DAYS` | No | `30` | File retention period in days |
| `MAX_RETRIES` | No | `3` | Maximum API retry attempts |
| `WEBHOOK_RATE_LIMIT` | No | - | Rate limit per minute (optional) |
| `WEBHOOK_RATE_LIMIT_PER_USER_AGENT` | No | - | Rate limit per user agent |
| `WEBHOOK_RATE_LIMIT_PER_API_KEY` | No | - | Rate limit per API key |
| `CLEANUP_FREQUENCY_REQUESTS` | No | `100` | Cleanup every N requests |
| `CLEANUP_FREQUENCY_SECONDS` | No | `3600` | Cleanup every N seconds |
| `ANOMALY_DETECTION_ENABLED` | No | `true` | Enable anomaly detection |
| `ANOMALY_FAILURE_THRESHOLD` | No | `5` | Failures before alerting |
| `ANOMALY_WINDOW_SECONDS` | No | `300` (5 min) | Anomaly detection window |
| `ALERT_ON_QUARANTINE_FAILURES` | No | `true` | Alert on quarantine failures |
| `REDIS_TTL` | No | `3600` (1 hour) | Redis cache TTL in seconds |
| `FILE_PERMISSIONS_MODE` | No | `384` (0o600) | File permissions (octal) |
| `ENABLE_ENCRYPTION_AT_REST` | No | `false` | Enable file encryption |

---

## Appendix B: API Endpoints Summary

| Method | Endpoint | Authentication | Purpose |
|--------|----------|---------------|---------|
| GET | `/` | None | Service information |
| GET | `/health` | None | Health check |
| POST | `/webhooks/post-call` | HMAC signature | Post-call webhook processing |
| POST | `/webhooks/client-data` | Header auth | Conversation initiation |
| POST | `/webhooks/search-data` | Header auth | In-call memory search |

---

## Appendix C: Webhook Payload Examples

### Post-Call Transcription Webhook

```json
{
  "type": "post_call_transcription",
  "event_timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "conversation_id": "conv_123",
    "agent_id": "agent_456",
    "transcript": [...],
    "conversation_initiation_client_data": {
      "dynamic_variables": {
        "system__caller_id": "+1234567890"
      }
    },
    "metadata": {
      "caller_id": "+1234567890"
    }
  }
}
```

### Client-Data Webhook Request

```json
{
  "caller_id": "+1234567890",
  "agent_id": "agent_456",
  "called_number": "+0987654321",
  "call_sid": "CA1234567890"
}
```

### Search-Data Webhook Request

```json
{
  "query": "user preferences and favorite topics",
  "user_id": "+1234567890",
  "limit": 5
}
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2024 | - | Initial comprehensive requirements document |

---

**End of Requirements Document**



