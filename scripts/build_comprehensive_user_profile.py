"""Build comprehensive user profile from stored conversations."""
import asyncio
import httpx
import json
import os
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime
import re

async def fetch_conversation_details(
    client: httpx.AsyncClient,
    conversation_id: str,
    elevenlabs_key: str
) -> Optional[Dict[str, Any]]:
    """Fetch full conversation details from Eleven Labs API."""
    url = f"https://api.elevenlabs.io/v1/convai/conversations/{conversation_id}"
    
    try:
        response = await client.get(
            url,
            headers={"xi-api-key": elevenlabs_key},
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"   ✗ Error fetching {conversation_id}: {e}")
        return None

def extract_caller_name(conversation_data: Dict[str, Any]) -> Optional[str]:
    """Extract caller name from conversation data."""
    # Check dynamic variables
    init_data = conversation_data.get("conversation_initiation_client_data", {})
    dynamic_vars = init_data.get("dynamic_variables", {})
    
    # Common name fields - prioritize system__caller_name (ElevenLabs system field)
    name_fields = [
        "system__caller_name",  # First priority - ElevenLabs system field
        "caller_name",
        "name",
        "user_name",
        "customer_name"
    ]
    
    for field in name_fields:
        name = dynamic_vars.get(field) or init_data.get(field)
        if name:
            return str(name).strip()
    
    # Try to extract from transcript (using 'message' field)
    transcript = conversation_data.get("transcript", [])
    for turn in transcript[:20]:  # Check first 20 turns
        message = turn.get("message", "")
        if not message:
            continue
        
        text = message.lower()
        # Look for patterns like "I'm [name]" or "My name is [name]"
        patterns = [
            r"i'?m\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
            r"my\s+name\s+is\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
            r"this\s+is\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
            r"call\s+me\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)"
        ]
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(1).strip()
    
    # Try to extract from summary
    analysis = conversation_data.get("analysis", {})
    summary = analysis.get("transcript_summary", "")
    if summary:
        # Look for name patterns in summary (e.g., "Sheila Cunningham shares...")
        name_match = re.search(r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:shares|recounts|discusses)", summary, re.IGNORECASE)
        if name_match:
            return name_match.group(1).strip()
    
    return None

def extract_preferences(transcript: List[Dict[str, Any]]) -> List[str]:
    """Extract user preferences from transcript."""
    preferences = []
    preference_patterns = [
        r"i\s+(?:like|love|prefer|enjoy|favorite|favourite)\s+([^.!?]+)",
        r"i\s+(?:don'?t|do\s+not)\s+(?:like|want|enjoy)\s+([^.!?]+)",
        r"my\s+(?:favorite|favourite|preferred)\s+([^.!?]+)",
        r"i\s+(?:would|will)\s+(?:like|prefer|want)\s+([^.!?]+)",
        r"i\s+(?:always|usually|often)\s+([^.!?]+)",
    ]
    
    for turn in transcript:
        message = turn.get("message", "")
        if not message:
            continue
        
        role = turn.get("role", "").lower()
        
        # Only extract from user turns (role is 'user' or 'caller')
        if role in ["user", "caller", "customer"]:
            text = message.lower()
            for pattern in preference_patterns:
                matches = re.findall(pattern, message, re.IGNORECASE)
                for match in matches:
                    pref = match.strip()
                    if len(pref) > 5 and len(pref) < 100:  # Reasonable length
                        preferences.append(pref)
    
    # Remove duplicates and return top preferences
    unique_prefs = []
    seen = set()
    for pref in preferences:
        pref_lower = pref.lower()
        if pref_lower not in seen:
            seen.add(pref_lower)
            unique_prefs.append(pref)
    
    return unique_prefs[:20]  # Top 20 preferences

def extract_events(transcript: List[Dict[str, Any]], conversation_id: str = None) -> List[Dict[str, Any]]:
    """Extract events and topics discussed from transcript."""
    events = []
    event_patterns = [
        r"(?:i|we|they)\s+(?:went|traveled|visited|saw|did|attended|experienced)\s+([^.!?]+)",
        r"(?:in|during|when)\s+(\d{4})\s+([^.!?]+)",
        r"(?:last|next|this)\s+(?:year|month|week|summer|winter|spring|fall)\s+([^.!?]+)",
        r"(?:i|we)\s+(?:were|was)\s+([^.!?]+)",
    ]
    
    for turn in transcript:
        message = turn.get("message", "")
        if not message:
            continue
        
        role = turn.get("role", "").lower()
        timestamp = turn.get("time_in_call_secs", "")
        
        if role in ["user", "caller", "customer"]:
            # Look for dates/years
            year_matches = re.findall(r"\b(19|20)\d{2}\b", message)
            # Look for locations
            location_patterns = [
                r"(?:in|to|from|at)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
                r"(?:visited|went\s+to|traveled\s+to)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"
            ]
            
            locations = []
            for pattern in location_patterns:
                loc_matches = re.findall(pattern, message)
                locations.extend(loc_matches)
            
            # Extract event descriptions
            for pattern in event_patterns:
                matches = re.findall(pattern, message, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        event_desc = " ".join(m for m in match if m).strip()
                    else:
                        event_desc = match.strip()
                    
                    if len(event_desc) > 10:
                        event = {
                            "description": event_desc[:200],
                            "mentioned_in": conversation_id,
                            "timestamp": timestamp,
                            "years": list(set(year_matches)) if year_matches else [],
                            "locations": list(set(locations[:5])) if locations else []
                        }
                        events.append(event)
    
    # Remove duplicates
    unique_events = []
    seen_descriptions = set()
    for event in events:
        desc_lower = event["description"].lower()
        if desc_lower not in seen_descriptions:
            seen_descriptions.add(desc_lower)
            unique_events.append(event)
    
    return unique_events[:30]  # Top 30 events

def extract_key_facts(transcript: List[Dict[str, Any]], analysis: Dict[str, Any]) -> List[str]:
    """Extract key facts about the user."""
    facts = []
    
    # Get summary from analysis
    summary = analysis.get("transcript_summary", "")
    if summary:
        facts.append(f"Summary: {summary[:200]}")
    
    # Extract facts from transcript
    fact_patterns = [
        r"i\s+(?:am|was|have|had|work|live|studied|born)\s+([^.!?]+)",
        r"my\s+(?:job|profession|occupation|hometown|birthplace|age)\s+(?:is|was)\s+([^.!?]+)",
        r"i\s+(?:grew\s+up|was\s+born|live|work)\s+(?:in|at)\s+([^.!?]+)",
    ]
    
    for turn in transcript:
        message = turn.get("message", "")
        if not message:
            continue
        
        role = turn.get("role", "").lower()
        
        if role in ["user", "caller", "customer"]:
            for pattern in fact_patterns:
                matches = re.findall(pattern, message, re.IGNORECASE)
                for match in matches:
                    fact = match.strip()
                    if len(fact) > 5 and len(fact) < 150:
                        facts.append(fact)
    
    return list(set(facts))[:20]  # Top 20 facts

def extract_topics(transcript: List[Dict[str, Any]]) -> List[str]:
    """Extract main topics discussed."""
    topics = []
    
    # Common topic keywords
    topic_keywords = {
        "travel": ["travel", "trip", "journey", "vacation", "visited", "went to"],
        "family": ["family", "mother", "father", "parent", "sibling", "brother", "sister"],
        "work": ["work", "job", "career", "profession", "occupation", "employer"],
        "education": ["school", "university", "college", "studied", "education", "degree"],
        "hobbies": ["hobby", "interest", "enjoy", "like to", "passion", "activity"],
        "memories": ["remember", "memory", "recall", "childhood", "past"],
        "location": ["live", "from", "hometown", "born", "grew up", "city", "country"]
    }
    
    all_text = " ".join(turn.get("message", "") or "" for turn in transcript).lower()
    
    for topic, keywords in topic_keywords.items():
        if any(keyword in all_text for keyword in keywords):
            topics.append(topic)
    
    return topics

async def build_comprehensive_profile(
    user_id: str,
    conversation_ids: List[str]
) -> Dict[str, Any]:
    """Build comprehensive user profile from conversations."""
    elevenlabs_key = os.getenv("ELEVENLABS_API_KEY", "")
    
    if not elevenlabs_key:
        print("⚠ Error: ELEVENLABS_API_KEY not set")
        return {"error": "ELEVENLABS_API_KEY not set"}
    
    print("=" * 80)
    print("BUILDING COMPREHENSIVE USER PROFILE")
    print("=" * 80)
    print(f"User ID: {user_id}")
    print(f"Conversations to analyze: {len(conversation_ids)}")
    print()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        all_transcripts = []
        all_analyses = []
        caller_names = []
        conversations_data = []
        
        # Fetch all conversations
        print("1. Fetching conversation data from Eleven Labs...")
        for i, conv_id in enumerate(conversation_ids, 1):
            print(f"   [{i}/{len(conversation_ids)}] Fetching {conv_id}...")
            conv_data = await fetch_conversation_details(client, conv_id, elevenlabs_key)
            
            if conv_data:
                conversations_data.append(conv_data)
                transcript = conv_data.get("transcript", [])
                analysis = conv_data.get("analysis", {})
                
                all_transcripts.extend(transcript)
                all_analyses.append(analysis)
                
                # Extract caller name
                name = extract_caller_name(conv_data)
                if name:
                    caller_names.append(name)
        
        print(f"   ✓ Fetched {len(conversations_data)} conversations")
        print(f"   Total transcript turns: {len(all_transcripts)}")
        print()
        
        # Extract information
        print("2. Extracting user information...")
        
        # Caller name - prioritize summary extraction (most reliable)
        caller_name = None
        
        # First, try to extract from summaries (most reliable)
        for conv_data in conversations_data:
            analysis = conv_data.get("analysis", {})
            summary = analysis.get("transcript_summary", "")
            if summary:
                # Look for name patterns in summary (e.g., "Sheila Cunningham shares...")
                name_match = re.search(r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:shares|recounts|discusses)", summary, re.IGNORECASE)
                if name_match:
                    caller_name = name_match.group(1).strip()
                    print(f"   ✓ Caller name (from summary): {caller_name}")
                    break
        
        # If not found in summaries, try from extracted names (filter invalid)
        if not caller_name and caller_names:
            from collections import Counter
            # Filter out invalid names (too short, common words, etc.)
            invalid_names = {"going", "to", "the", "and", "or", "but", "for", "with", "from", "in", "on", "at", "is", "was", "are", "were"}
            valid_names = [n for n in caller_names if n and len(n) > 2 and n.lower() not in invalid_names and n[0].isupper()]
            if valid_names:
                name_counts = Counter(valid_names)
                caller_name = name_counts.most_common(1)[0][0]
                print(f"   ✓ Caller name (from transcript): {caller_name}")
        
        if not caller_name:
            print(f"   ⚠ Caller name: Not found")
        
        # Preferences
        print("   Extracting preferences...")
        preferences = extract_preferences(all_transcripts)
        print(f"   ✓ Found {len(preferences)} preferences")
        
        # Events
        print("   Extracting events...")
        events = []
        for conv_data in conversations_data:
            conv_id = conv_data.get("conversation_id")
            conv_events = extract_events(conv_data.get("transcript", []), conv_id)
            events.extend(conv_events)
        print(f"   ✓ Found {len(events)} events")
        
        # Key facts
        print("   Extracting key facts...")
        key_facts = []
        for i, analysis in enumerate(all_analyses):
            # Use transcript from corresponding conversation
            if i < len(conversations_data):
                conv_transcript = conversations_data[i].get("transcript", [])
                facts = extract_key_facts(conv_transcript, analysis)
                key_facts.extend(facts)
        key_facts = list(set(key_facts))[:20]
        print(f"   ✓ Found {len(key_facts)} key facts")
        
        # Topics
        print("   Extracting topics...")
        topics = extract_topics(all_transcripts)
        print(f"   ✓ Found {len(topics)} topics: {', '.join(topics)}")
        print()
        
        # Build profile
        print("3. Building comprehensive profile...")
        
        # Calculate statistics
        total_turns = len(all_transcripts)
        successful_calls = sum(1 for a in all_analyses if a.get("call_successful") == True)
        
        profile = {
            "user_id": user_id,
            "caller_name": caller_name,
            "profile_generated_at": datetime.utcnow().isoformat(),
            "statistics": {
                "total_conversations": len(conversations_data),
                "total_transcript_turns": total_turns,
                "successful_calls": successful_calls,
                "failed_calls": len(conversations_data) - successful_calls,
                "average_turns_per_conversation": total_turns / len(conversations_data) if conversations_data else 0
            },
            "preferences": preferences,
            "events": events[:30],  # Top 30 events
            "key_facts": key_facts,
            "topics": topics,
            "conversation_summaries": [
                {
                    "conversation_id": conv.get("conversation_id"),
                    "summary": conv.get("analysis", {}).get("transcript_summary", "")[:200],
                    "call_successful": conv.get("analysis", {}).get("call_successful", False),
                    "transcript_turns": len(conv.get("transcript", []))
                }
                for conv in conversations_data
            ]
        }
        
        print("   ✓ Profile built successfully")
        print()
        
        return profile

async def main():
    """Main function."""
    # Get conversation IDs from storage results
    results_file = "data/conversation_storage_results.json"
    
    if os.path.exists(results_file):
        with open(results_file, "r") as f:
            results = json.load(f)
        
        # Get user_id from first result
        if results:
            user_id = results[0].get("user_id", "+15074595005")
            conversation_ids = [r.get("conversation_id") for r in results if r.get("conversation_id")]
            
            print(f"\nBuilding comprehensive profile for: {user_id}")
            print(f"Analyzing {len(conversation_ids)} conversations\n")
            
            profile = await build_comprehensive_profile(user_id, conversation_ids)
            
            # Save profile
            os.makedirs("data", exist_ok=True)
            output_file = f"data/comprehensive_profile_{user_id.replace('+', '')}.json"
            with open(output_file, "w") as f:
                json.dump(profile, f, indent=2)
            
            print("=" * 80)
            print("PROFILE SUMMARY")
            print("=" * 80)
            print(f"User ID: {profile['user_id']}")
            print(f"Caller Name: {profile.get('caller_name', 'Not found')}")
            print(f"Total Conversations: {profile['statistics']['total_conversations']}")
            print(f"Total Transcript Turns: {profile['statistics']['total_transcript_turns']}")
            print(f"Preferences Found: {len(profile['preferences'])}")
            print(f"Events Found: {len(profile['events'])}")
            print(f"Key Facts: {len(profile['key_facts'])}")
            print(f"Topics: {', '.join(profile['topics'])}")
            print()
            print(f"✓ Profile saved to: {output_file}")
            print("=" * 80)
        else:
            print("❌ No conversation results found")
    else:
        print(f"❌ Results file not found: {results_file}")
        print("Please run store_conversations.py first")

if __name__ == "__main__":
    asyncio.run(main())

