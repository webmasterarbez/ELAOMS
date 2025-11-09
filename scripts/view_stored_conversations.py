"""Script to view stored conversations from storage results."""
import json
import os
from typing import List, Dict, Any

def view_stored_conversations():
    """Display profile from stored conversation results."""
    results_file = "data/conversation_storage_results.json"
    
    if not os.path.exists(results_file):
        print(f"❌ Results file not found: {results_file}")
        return
    
    with open(results_file, "r") as f:
        results = json.load(f)
    
    if not results:
        print("❌ No conversation results found")
        return
    
    # Group by user_id
    by_user = {}
    for result in results:
        user_id = result.get("user_id", "unknown")
        if user_id not in by_user:
            by_user[user_id] = []
        by_user[user_id].append(result)
    
    # Display profile for each user
    for user_id, conversations in by_user.items():
        print("=" * 80)
        print("USER PROFILE FROM STORED CONVERSATIONS")
        print("=" * 80)
        print(f"User ID: {user_id}")
        print(f"Total Conversations: {len(conversations)}")
        print()
        
        # Calculate statistics
        total_turns = sum(c.get("transcript_turns", 0) for c in conversations)
        successful_calls = sum(1 for c in conversations if c.get("call_successful") == "success")
        failed_calls = sum(1 for c in conversations if c.get("call_successful") == "failure")
        
        print("=" * 80)
        print("CONVERSATION STATISTICS")
        print("=" * 80)
        print(f"Total Conversations: {len(conversations)}")
        print(f"Successful Calls: {successful_calls}")
        print(f"Failed Calls: {failed_calls}")
        print(f"Total Transcript Turns: {total_turns}")
        print(f"Average Turns per Conversation: {total_turns / len(conversations):.1f}")
        print()
        
        # Show each conversation
        print("=" * 80)
        print("CONVERSATION DETAILS")
        print("=" * 80)
        
        for i, conv in enumerate(conversations, 1):
            print(f"\n[{i}] Conversation ID: {conv.get('conversation_id', 'N/A')}")
            print(f"    Memory ID: {conv.get('memory_id', 'N/A')}")
            print(f"    Status: {conv.get('status', 'N/A')}")
            print(f"    Transcript Turns: {conv.get('transcript_turns', 0)}")
            print(f"    Call Successful: {conv.get('call_successful', 'N/A')}")
        
        print()
        print("=" * 80)
        print("STORAGE SUMMARY")
        print("=" * 80)
        print(f"All conversations stored successfully: {all(c.get('status') == 'success' for c in conversations)}")
        print(f"Unique Memory IDs: {len(set(c.get('memory_id') for c in conversations))}")
        print()
        
        # Note about OpenMemory
        print("=" * 80)
        print("NOTE")
        print("=" * 80)
        print("These conversations are stored in OpenMemory with the following memory IDs:")
        for conv in conversations:
            print(f"  - {conv.get('conversation_id')} → Memory ID: {conv.get('memory_id')}")
        print()
        print("To query these memories in OpenMemory, use:")
        print(f"  - User ID: {user_id}")
        print("  - Query endpoint: POST /memory/query")
        print("  - Or use the OpenMemoryClient in src/clients/openmemory.py")
        print("=" * 80)

if __name__ == "__main__":
    view_stored_conversations()

