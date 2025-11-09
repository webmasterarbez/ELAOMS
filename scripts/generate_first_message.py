"""Generate personalized first message for Sheila Cunningham."""
import json
import os

def generate_first_message(profile_file: str = "data/comprehensive_profile_15074595005.json"):
    """Generate a personalized first message based on the user profile."""
    
    if not os.path.exists(profile_file):
        print(f"❌ Profile file not found: {profile_file}")
        return None
    
    with open(profile_file, "r") as f:
        profile = json.load(f)
    
    caller_name = profile.get("caller_name", "there")
    topics = profile.get("topics", [])
    events = profile.get("events", [])
    preferences = profile.get("preferences", [])
    conversation_summaries = profile.get("conversation_summaries", [])
    
    # Extract key information
    locations_mentioned = set()
    for event in events:
        locations_mentioned.update(event.get("locations", []))
    
    # Key locations from profile
    key_locations = ["Winona", "Minnesota", "Peru", "Iran", "Denver", "Mississippi River"]
    found_locations = [loc for loc in key_locations if any(loc.lower() in str(loc).lower() for loc in locations_mentioned)]
    
    # Build personalized message
    message_parts = []
    
    # Greeting with name
    if caller_name:
        message_parts.append(f"Hi {caller_name}!")
    else:
        message_parts.append("Hi there!")
    
    # Acknowledge previous conversations
    if conversation_summaries:
        message_parts.append("It's wonderful to hear from you again.")
    
    # Reference key memories
    if "travel" in topics:
        message_parts.append("I remember you sharing your incredible travel stories - from your time in Peru in 1964, to your adventures in Iran, Russia, and across Europe.")
    
    if "memories" in topics:
        message_parts.append("You've told me about growing up in Winona, Minnesota, and those wonderful memories of the Mississippi River and the bluffs.")
    
    # Invitation to continue
    message_parts.append("I'd love to hear more about your experiences or help you with anything today.")
    
    # Combine into natural message
    first_message = " ".join(message_parts)
    
    return first_message

if __name__ == "__main__":
    print("=" * 80)
    print("GENERATING PERSONALIZED FIRST MESSAGE")
    print("=" * 80)
    print()
    
    message = generate_first_message()
    
    if message:
        print("Personalized First Message:")
        print("-" * 80)
        print(message)
        print("-" * 80)
        print()
        print("=" * 80)
        print("MESSAGE FOR ELEVEN LABS")
        print("=" * 80)
        print()
        print("This message can be used as the 'first_message' override in the")
        print("conversation_initiation_client_data response.")
        print()
        print("JSON Format:")
        print(json.dumps({
            "type": "conversation_initiation_client_data",
            "dynamic_variables": {
                "caller_id": "+15074595005",
                "caller_name": "Sheila Cunningham"
            },
            "conversation_config_override": {
                "agent": {
                    "first_message": message
                }
            }
        }, indent=2))
    else:
        print("❌ Failed to generate message")

