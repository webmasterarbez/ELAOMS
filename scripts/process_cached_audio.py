#!/usr/bin/env python3
"""Script to manually process cached audio webhook for a conversation."""
import sys
import os
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.webhook_storage import get_cached_audio_webhook, save_webhook_to_file, extract_caller_phone_from_payload
from src.utils.helpers import sanitize_filename
from config import settings

def process_cached_audio(conversation_id: str):
    """Process cached audio webhook for a conversation."""
    print("=" * 60)
    print(f"Processing Cached Audio for: {conversation_id}")
    print("=" * 60)
    print()
    
    # Check if audio is cached
    audio_data = get_cached_audio_webhook(conversation_id)
    if not audio_data:
        print(f"❌ No cached audio found for conversation {conversation_id}")
        print("   Audio may have expired from cache or was never cached")
        return False
    
    print(f"✅ Found cached audio data ({len(audio_data)} bytes)")
    
    # Find transcription file to extract caller phone
    transcription_file = None
    base_path = settings.webhook_storage_path
    
    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.startswith(f"{conversation_id}_transcription.json"):
                transcription_file = os.path.join(root, file)
                break
        if transcription_file:
            break
    
    if not transcription_file or not os.path.exists(transcription_file):
        print(f"❌ Transcription file not found for conversation {conversation_id}")
        print("   Cannot extract caller phone number")
        return False
    
    print(f"✅ Found transcription file: {transcription_file}")
    
    # Load transcription to extract caller phone
    try:
        with open(transcription_file, 'r') as f:
            transcription_payload = json.load(f)
        caller_phone = extract_caller_phone_from_payload(transcription_payload)
        if caller_phone:
            caller_phone = sanitize_filename(caller_phone)
            print(f"✅ Extracted caller phone: {caller_phone}")
        else:
            print(f"⚠️  Could not extract caller phone, will use conversation_id as directory")
            caller_phone = None
    except Exception as e:
        print(f"❌ Error loading transcription file: {e}")
        return False
    
    # Save audio file
    try:
        audio_path = save_webhook_to_file(
            payload=None,
            webhook_type="audio",
            conversation_id=conversation_id,
            caller_phone=caller_phone,
            audio_data=audio_data,
            validated=True,
            request_id=None,
            use_quarantine=False
        )
        print(f"✅ Saved audio file: {audio_path}")
        print(f"   File size: {os.path.getsize(audio_path)} bytes")
        return True
    except Exception as e:
        print(f"❌ Error saving audio file: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1:
        conversation_id = sys.argv[1]
    else:
        # Default to the conversation from the user's question
        conversation_id = "conv_0901k9nsfrp6e4s9d81jt0jhe75n"
    
    print(f"\nProcessing cached audio for conversation: {conversation_id}\n")
    
    success = process_cached_audio(conversation_id)
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Successfully processed cached audio!")
    else:
        print("❌ Failed to process cached audio")
    print("=" * 60)
    
    sys.exit(0 if success else 1)

