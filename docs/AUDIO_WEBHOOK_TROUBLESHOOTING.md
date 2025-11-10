# Audio Webhook Troubleshooting Guide

## Problem: Audio File Not Saved

When a transcription webhook is received but no corresponding audio file (`.mp3`) is created, this guide helps diagnose the issue.

## Diagnosis Steps

### 1. Check if Audio File Exists

```bash
# Check for audio file in the webhook directory
ls -la data/webhooks/+16129782029/conv_0901k9nsfrp6e4s9d81jt0jhe75n_audio.mp3
```

### 2. Check Logs

Look for these log messages:

**When audio webhook is received:**
```
INFO: Cached audio webhook for conversation {conversation_id}, waiting for transcription
```

**When transcription arrives and audio is processed:**
```
INFO: Processed cached audio webhook: {audio_path}
```

**When transcription arrives but no audio is found:**
```
WARNING: No cached audio webhook found for conversation {conversation_id}. Audio webhook may not have been received, expired from cache, or failed to cache.
```

### 3. Verify Phone Number Extraction

The phone number must be available for the audio file to be saved in the correct directory. Check that:
- `system__caller_id` is present in `dynamic_variables`
- Or `external_number` is present in `metadata.phone_call`

## Common Reasons Audio File Is Not Saved

### 1. Audio Webhook Never Received (Most Common)

**Cause:** ElevenLabs may not send audio webhooks in all cases, or there was a network issue.

**How to verify:**
- Check application logs for "Cached audio webhook" message
- Check if audio webhook endpoint was called (check web server logs)

**Solution:**
- Ensure ElevenLabs is configured to send audio webhooks
- Check network connectivity between ElevenLabs and your server
- Verify webhook endpoint is accessible

### 2. Audio Webhook Expired from Cache

**Cause:** The audio webhook was received and cached, but the transcription webhook arrived more than 1 hour later (default cache TTL).

**How to verify:**
- Check the timestamps:
  - Audio webhook timestamp (if logged)
  - Transcription webhook timestamp
  - If difference > 3600 seconds (1 hour), cache expired

**Solution:**
- Increase `AUDIO_CACHE_TTL` in `.env` file (default: 3600 seconds = 1 hour)
- Ensure transcription webhooks arrive promptly after audio webhooks

### 3. Audio Webhook Received But Not Cached

**Cause:** Error occurred during caching (Redis connection failure, memory issue, etc.)

**How to verify:**
- Check logs for caching errors:
  - "Redis cache failed, falling back to in-memory"
  - "Error caching audio webhook"
  - Any exceptions during `cache_audio_webhook()` call

**Solution:**
- Check Redis connection (if using Redis)
- Check available memory
- Review error logs for specific caching failures

### 4. Audio Webhook Cached But Not Found

**Cause:** Cache lookup failed (Redis connection issue, cache key mismatch, etc.)

**How to verify:**
- Check logs for cache retrieval errors
- Verify cache key format: `audio_webhook:{conversation_id}`
- Check if Redis is accessible (if using Redis)

**Solution:**
- Verify Redis connection (if using Redis)
- Check cache key format matches
- Review cache retrieval error logs

### 5. Error During Audio File Saving

**Cause:** File system error, permission issue, or disk space problem.

**How to verify:**
- Check logs for file saving errors
- Check disk space: `df -h`
- Check directory permissions: `ls -la data/webhooks/`

**Solution:**
- Ensure sufficient disk space
- Check directory permissions (should be writable)
- Review file system error logs

## Configuration

### Audio Cache TTL

Default: 3600 seconds (1 hour)

To increase cache TTL, set in `.env`:
```bash
AUDIO_CACHE_TTL=7200  # 2 hours
```

### Redis Configuration

If using Redis for distributed caching, ensure:
```bash
REDIS_URL=redis://localhost:6379
REDIS_TTL=3600  # Should match or exceed AUDIO_CACHE_TTL
```

## Prevention

1. **Monitor Logs:** Set up log monitoring to alert when audio webhooks are not received
2. **Increase Cache TTL:** If transcription webhooks consistently arrive late, increase `AUDIO_CACHE_TTL`
3. **Use Redis:** For distributed systems, use Redis to persist cache across server restarts
4. **Health Checks:** Monitor webhook endpoint health and availability
5. **Alerting:** Set up alerts for missing audio files

## Example: Diagnosing a Specific Conversation

```bash
# Use the diagnostic script
python scripts/diagnose_audio_webhook.py conv_0901k9nsfrp6e4s9d81jt0jhe75n
```

This will show:
- Whether transcription file exists
- Whether audio file exists
- Phone number extraction status
- Cache configuration
- Possible reasons for missing audio file

## Code Flow

1. **Audio Webhook Arrives:**
   - Decode base64 audio data
   - Cache audio data with timestamp
   - Log: "Cached audio webhook for conversation {conversation_id}"

2. **Transcription Webhook Arrives:**
   - Extract phone number
   - Save transcription file
   - Check cache for audio data
   - If found: Save audio file and log success
   - If not found: Log warning with possible reasons

## Recent Fixes

As of the latest update:
- Audio files are now processed even if `caller_phone` is `None` (uses `conversation_id` as fallback)
- Better logging added to diagnose missing audio files
- Priority 6 fallback added for `metadata.phone_call.external_number`

