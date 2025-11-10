#!/usr/bin/env python3
"""Simple script to move audio files to the correct phone number directory."""
import sys
import os
import json
import shutil
from pathlib import Path

def extract_phone_from_transcription(transcription_file):
    """Extract phone number from transcription file."""
    with open(transcription_file, 'r') as f:
        payload = json.load(f)
    
    data = payload.get("data", {})
    
    # Priority 1: system__caller_id from dynamic_variables
    dynamic_vars = data.get("conversation_initiation_client_data", {}).get("dynamic_variables", {})
    caller_id = dynamic_vars.get("system__caller_id")
    if caller_id:
        return str(caller_id).strip()
    
    # Priority 6: external_number from metadata.phone_call
    phone_call = data.get("metadata", {}).get("phone_call", {})
    external_number = phone_call.get("external_number")
    if external_number:
        return str(external_number).strip()
    
    return None

def move_audio_to_phone_directory(conversation_id: str):
    """Move audio file from conversation_id directory to phone number directory."""
    print("=" * 60)
    print(f"Moving Audio File for: {conversation_id}")
    print("=" * 60)
    print()
    
    # Find transcription file
    transcription_file = None
    base_path = Path("data/webhooks")
    
    for subdir in base_path.iterdir():
        if subdir.is_dir():
            for file in subdir.glob(f"*{conversation_id}*transcription.json"):
                transcription_file = file
                break
        if transcription_file:
            break
    
    if not transcription_file or not transcription_file.exists():
        print(f"❌ Transcription file not found for conversation {conversation_id}")
        return False
    
    print(f"✅ Found transcription file: {transcription_file}")
    
    # Extract caller phone
    caller_phone = extract_phone_from_transcription(transcription_file)
    if not caller_phone:
        print(f"❌ Could not extract caller phone from transcription file")
        return False
    print(f"✅ Extracted caller phone: {caller_phone}")
    
    # Find audio file in conversation_id directory
    audio_file = base_path / conversation_id / f"{conversation_id}_audio.mp3"
    if not audio_file.exists():
        print(f"❌ Audio file not found: {audio_file}")
        return False
    
    print(f"✅ Found audio file: {audio_file}")
    
    # Create phone number directory if it doesn't exist
    phone_dir = base_path / caller_phone
    phone_dir.mkdir(parents=True, exist_ok=True)
    print(f"✅ Phone number directory: {phone_dir}")
    
    # Target audio file path
    target_audio_file = phone_dir / f"{conversation_id}_audio.mp3"
    
    # Check if target already exists
    if target_audio_file.exists():
        print(f"⚠️  Target audio file already exists: {target_audio_file}")
        print("   Skipping move (file already in correct location)")
        return True
    
    # Move audio file
    try:
        shutil.move(str(audio_file), str(target_audio_file))
        print(f"✅ Moved audio file to: {target_audio_file}")
    except Exception as e:
        print(f"❌ Error moving audio file: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Move metadata file if exists
    metadata_file = base_path / conversation_id / f"{conversation_id}_audio.mp3.metadata.json"
    target_metadata_file = phone_dir / f"{conversation_id}_audio.mp3.metadata.json"
    if metadata_file.exists():
        try:
            shutil.move(str(metadata_file), str(target_metadata_file))
            print(f"✅ Moved metadata file to: {target_metadata_file}")
            
            # Update metadata file path
            with open(target_metadata_file, 'r') as f:
                metadata = json.load(f)
            metadata["file_path"] = str(target_audio_file)
            metadata["directory_name"] = caller_phone
            with open(target_metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            print(f"✅ Updated metadata file path")
        except Exception as e:
            print(f"⚠️  Error moving/updating metadata file: {e}")
    
    # Remove empty conversation_id directory
    conv_dir = base_path / conversation_id
    try:
        if conv_dir.exists() and not any(conv_dir.iterdir()):
            conv_dir.rmdir()
            print(f"✅ Removed empty directory: {conv_dir}")
    except Exception as e:
        print(f"⚠️  Could not remove directory: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Successfully moved audio file to phone number directory!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    if len(sys.argv) > 1:
        conversation_id = sys.argv[1]
    else:
        # Default to the conversation from the user's question
        conversation_id = "conv_7401k9nt1rh8fwbv3p1w8r8fyeqb"
    
    print(f"\nMoving audio file for conversation: {conversation_id}\n")
    
    success = move_audio_to_phone_directory(conversation_id)
    
    sys.exit(0 if success else 1)

