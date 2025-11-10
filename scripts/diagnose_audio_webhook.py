#!/usr/bin/env python3
"""Diagnostic script to check why audio file was not saved for a conversation."""
import json
import sys
from pathlib import Path
from datetime import datetime

def diagnose_audio_webhook(conversation_id: str):
    """Diagnose why audio file was not saved for a conversation."""
    print("=" * 60)
    print(f"Diagnosing Audio Webhook for: {conversation_id}")
    print("=" * 60)
    print()
    
    # Find transcription file
    webhook_dir = Path("data/webhooks")
    transcription_file = None
    
    for subdir in webhook_dir.iterdir():
        if subdir.is_dir():
            for file in subdir.glob(f"*{conversation_id}*transcription.json"):
                transcription_file = file
                break
        if transcription_file:
            break
    
    if not transcription_file:
        print(f"❌ Transcription file not found for conversation {conversation_id}")
        return False
    
    print(f"✅ Found transcription file: {transcription_file}")
    
    # Load transcription payload
    with open(transcription_file, 'r') as f:
        payload = json.load(f)
    
    # Extract conversation data
    data = payload.get("data", {})
    conv_id = data.get("conversation_id")
    event_timestamp = payload.get("event_timestamp")
    
    print(f"   Conversation ID: {conv_id}")
    print(f"   Event timestamp: {event_timestamp}")
    if event_timestamp:
        event_time = datetime.fromtimestamp(event_timestamp)
        print(f"   Event time: {event_time}")
    
    # Check for phone number
    dynamic_vars = data.get("conversation_initiation_client_data", {}).get("dynamic_variables", {})
    system_caller_id = dynamic_vars.get("system__caller_id")
    phone_call = data.get("metadata", {}).get("phone_call", {})
    external_number = phone_call.get("external_number")
    
    print(f"\n📞 Phone Number Extraction:")
    print(f"   system__caller_id: {system_caller_id}")
    print(f"   external_number: {external_number}")
    
    # Check if audio file exists
    audio_file = transcription_file.parent / f"{conv_id}_audio.mp3"
    if audio_file.exists():
        print(f"\n✅ Audio file exists: {audio_file}")
        print(f"   File size: {audio_file.stat().st_size} bytes")
        return True
    else:
        print(f"\n❌ Audio file NOT found: {audio_file}")
    
    # Check metadata file
    metadata_file = transcription_file.with_suffix('.json.metadata.json')
    if metadata_file.exists():
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        print(f"\n📄 Metadata file exists: {metadata_file}")
        print(f"   Saved at: {metadata.get('timestamp')}")
        print(f"   Validated: {metadata.get('validated')}")
    else:
        print(f"\n⚠️  Metadata file not found: {metadata_file}")
    
    # Possible reasons
    print(f"\n🔍 Possible Reasons Audio File Was Not Saved:")
    print(f"   1. Audio webhook was never received from ElevenLabs")
    print(f"   2. Audio webhook was received but not cached (error during caching)")
    print(f"   3. Audio webhook was cached but expired before transcription arrived")
    print(f"   4. Audio webhook was cached but not found when transcription arrived")
    print(f"   5. Error occurred during audio file saving")
    
    # Check cache TTL settings
    print(f"\n⚙️  Cache Settings:")
    try:
        from config import settings
        print(f"   Audio cache TTL: {getattr(settings, 'audio_cache_ttl', 'Not set')} seconds")
        print(f"   Redis URL: {getattr(settings, 'redis_url', 'Not configured')}")
        if hasattr(settings, 'audio_cache_ttl') and event_timestamp:
            cache_ttl = settings.audio_cache_ttl
            print(f"   Cache TTL: {cache_ttl} seconds ({cache_ttl/60:.1f} minutes)")
            
            # Calculate if cache would have expired
            current_time = datetime.now().timestamp()
            time_since_event = current_time - event_timestamp
            print(f"   Time since event: {time_since_event:.0f} seconds ({time_since_event/60:.1f} minutes)")
            
            if time_since_event > cache_ttl:
                print(f"   ⚠️  Cache would have expired (event was {time_since_event/60:.1f} minutes ago)")
    except Exception as e:
        print(f"   ⚠️  Could not load settings: {e}")
    
    # Check if we can manually test extraction
    print(f"\n🧪 Testing Phone Number Extraction:")
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from src.utils.helpers import extract_user_id_from_payload
        
        user_id = extract_user_id_from_payload(payload)
        print(f"   ✅ Extracted user_id: {user_id}")
        
        if user_id:
            print(f"   ✅ Phone number extraction works correctly")
        else:
            print(f"   ❌ Phone number extraction returned None")
    except Exception as e:
        print(f"   ⚠️  Could not test extraction: {e}")
    
    print(f"\n" + "=" * 60)
    print("Diagnosis Complete")
    print("=" * 60)
    
    return False


if __name__ == "__main__":
    if len(sys.argv) > 1:
        conversation_id = sys.argv[1]
    else:
        # Default to the conversation from the user's question
        conversation_id = "conv_0901k9nsfrp6e4s9d81jt0jhe75n"
    
    diagnose_audio_webhook(conversation_id)

