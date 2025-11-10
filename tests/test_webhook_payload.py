#!/usr/bin/env python3
"""Test script to send a webhook payload to the post-call endpoint."""
import requests
import json
import hmac
import hashlib
import time
from datetime import datetime

# The payload from the user (truncated, so I'll complete it)
payload_data = {
    "type": "post_call_transcription",
    "event_timestamp": 1762713911,
    "data": {
        "agent_id": "agent_5001k9myfdmae9ntkrhxfr5b4tqy",
        "conversation_id": "conv_6601k9mywx20fxcbpyv2wtff3zph",
        "status": "done",
        "user_id": None,
        "branch_id": None,
        "transcript": [
            {
                "role": "agent",
                "agent_metadata": {
                    "agent_id": "agent_5001k9myfdmae9ntkrhxfr5b4tqy",
                    "branch_id": None,
                    "workflow_node_id": None
                },
                "message": "Hello! What is your name?",
                "multivoice_message": None,
                "tool_calls": [],
                "tool_results": [],
                "feedback": None,
                "llm_override": None,
                "time_in_call_secs": 0,
                "conversation_turn_metrics": {
                    "metrics": {
                        "convai_tts_service_ttfb": {
                            "elapsed_time": 0.18307536099746358
                        }
                    }
                },
                "rag_retrieval_info": None,
                "llm_usage": None,
                "interrupted": False,
                "original_message": None,
                "source_medium": None
            },
            {
                "role": "user",
                "agent_metadata": None,
                "message": "My name is Stefan.",
                "multivoice_message": None,
                "tool_calls": [],
                "tool_results": [],
                "feedback": None,
                "llm_override": None,
                "time_in_call_secs": 2,
                "conversation_turn_metrics": {
                    "metrics": {
                        "convai_asr_trailing_service_latency": {
                            "elapsed_time": 0.10322719800751656
                        }
                    }
                },
                "rag_retrieval_info": None,
                "llm_usage": None,
                "interrupted": False,
                "original_message": None,
                "source_medium": "audio"
            }
        ],
        "metadata": {
            "start_time_unix_secs": 1762713827,
            "accepted_time_unix_secs": 1762713827,
            "call_duration_secs": 79,
            "cost": 531,
            "deletion_settings": {
                "deletion_time_unix_secs": None,
                "deleted_logs_at_time_unix_secs": None,
                "deleted_audio_at_time_unix_secs": None,
                "deleted_transcript_at_time_unix_secs": None,
                "delete_transcript_and_pii": False,
                "delete_audio": False
            },
            "feedback": {
                "type": None,
                "overall_score": None,
                "likes": 0,
                "dislikes": 0,
                "rating": None,
                "comment": None
            },
            "authorization_method": "signed_url",
            "charging": {
                "dev_discount": False,
                "is_burst": False,
                "tier": "creator",
                "llm_usage": {
                    "irreversible_generation": {
                        "model_usage": {
                            "gemini-2.5-flash": {
                                "input": {
                                    "tokens": 2159,
                                    "price": 0.00032385
                                },
                                "input_cache_read": {
                                    "tokens": 0,
                                    "price": 0.0
                                },
                                "input_cache_write": {
                                    "tokens": 0,
                                    "price": 0.0
                                },
                                "output_total": {
                                    "tokens": 153,
                                    "price": 9.18e-05
                                }
                            }
                        }
                    },
                    "initiated_generation": {
                        "model_usage": {
                            "gemini-2.5-flash": {
                                "input": {
                                    "tokens": 2159,
                                    "price": 0.00032385
                                },
                                "input_cache_read": {
                                    "tokens": 0,
                                    "price": 0.0
                                },
                                "input_cache_write": {
                                    "tokens": 0,
                                    "price": 0.0
                                },
                                "output_total": {
                                    "tokens": 153,
                                    "price": 9.18e-05
                                }
                            }
                        }
                    }
                }
            },
            "llm_price": 0.00041565,
            "llm_charge": 1,
            "call_charge": 530,
            "free_minutes_consumed": 0.0,
            "free_llm_dollars_consumed": 0.0
        },
        "phone_call": {
            "direction": "inbound",
            "phone_number_id": "phnum_01jxj3hwx1fava7g3snzm5e2f8",
            "agent_number": "+16123241623",
            "external_number": "+16129782029",
            "type": "twilio",
            "stream_sid": "MZ34dda22b858da62893472c6884610479",
            "call_sid": "CA46088a7981a0f1671ea831f63c33fac3"
        },
        "batch_call": None,
        "termination_reason": "Call ended by remote party",
        "error": None,
        "main_language": "en",
        "rag_usage": None,
        "text_only": False,
        "features_usage": {
            "language_detection": {
                "enabled": False,
                "used": False
            },
            "transfer_to_agent": {
                "enabled": False,
                "used": False
            },
            "transfer_to_number": {
                "enabled": False,
                "used": False
            },
            "multivoice": {
                "enabled": False,
                "used": False
            },
            "dtmf_tones": {
                "enabled": False,
                "used": False
            },
            "external_mcp_servers": {
                "enabled": False,
                "used": False
            },
            "pii_zrm_workspace": False,
            "pii_zrm_agent": False,
            "tool_dynamic_variable_updates": {
                "enabled": False,
                "used": False
            },
            "is_livekit": False,
            "voicemail_detection": {
                "enabled": False,
                "used": False
            },
            "workflow": {
                "enabled": False,
                "tool_node": {
                    "enabled": False,
                    "used": False
                },
                "standalone_agent_node": {
                    "enabled": False,
                    "used": False
                },
                "phone_number_node": {
                    "enabled": False,
                    "used": False
                },
                "end_node": {
                    "enabled": False,
                    "used": False
                }
            },
            "agent_testing": {
                "enabled": False,
                "tests_ran_after_last_modification": False,
                "tests_ran_in_last_7_days": False
            }
        },
        "eleven_assistant": {
            "is_eleven_assistant": False
        },
        "initiator_id": None,
        "conversation_initiation_source": "twilio",
        "conversation_initiation_source_version": None,
        "timezone": None,
        "initiation_trigger": {
            "trigger_type": "default"
        },
        "async_metadata": None,
        "whatsapp": None,
        "agent_created_from": "ui",
        "agent_last_updated_from": "ui"
    },
    "analysis": {
        "evaluation_criteria_results": {},
        "data_collection_results": {}
    }
}

def generate_hmac_signature(timestamp: int, payload: str, secret: str) -> str:
    """Generate HMAC signature for the webhook.
    
    Note: The server uses timestamp as a string (from header), so we convert to string
    to match the exact format the server expects.
    """
    # Convert timestamp to string to match server's format (server uses string from header)
    timestamp_str = str(timestamp)
    payload_to_sign = f"{timestamp_str}.{payload}"
    mac = hmac.new(
        key=secret.encode("utf-8"),
        msg=payload_to_sign.encode("utf-8"),
        digestmod=hashlib.sha256
    )
    return f"t={timestamp},v0={mac.hexdigest()}"

def test_webhook(use_provided_timestamp=False):
    """Test the webhook endpoint with the provided payload.
    
    Args:
        use_provided_timestamp: If True, use the timestamp from the payload (may fail validation if in future).
                                If False, use current timestamp (recommended).
    """
    # Import settings to get the webhook secret
    from config import settings
    
    # Use provided timestamp or current timestamp
    if use_provided_timestamp:
        timestamp = payload_data["event_timestamp"]
        print(f"⚠️  WARNING: Using provided timestamp {timestamp} which may be in the future!")
        print(f"   This may fail timestamp validation if it's more than 30 minutes in the future.")
    else:
        timestamp = int(time.time())
        print(f"✓ Using current timestamp: {timestamp}")
    
    # Convert payload to JSON string
    payload_json = json.dumps(payload_data, separators=(',', ':'))
    
    # Check if webhook secret is configured
    if not settings.elevenlabs_post_call_hmac_key:
        print("❌ ERROR: ELEVENLABS_POST_CALL_HMAC_KEY is not configured in .env file!")
        print("   Please set ELEVENLABS_POST_CALL_HMAC_KEY in your .env file.")
        return False
    
    # Generate HMAC signature
    signature = generate_hmac_signature(
        timestamp=timestamp,
        payload=payload_json,
        secret=settings.elevenlabs_post_call_hmac_key
    )
    
    # Debug: Show what we're signing
    payload_to_sign = f"{timestamp}.{payload_json}"
    print(f"Debug: Payload to sign length: {len(payload_to_sign)}")
    print(f"Debug: First 100 chars: {payload_to_sign[:100]}...")
    print(f"Debug: HMAC key configured: {'Yes' if settings.elevenlabs_post_call_hmac_key else 'No'}")
    print(f"Debug: HMAC key length: {len(settings.elevenlabs_post_call_hmac_key) if settings.elevenlabs_post_call_hmac_key else 0}")
    print()
    
    # Prepare headers - use lowercase header name as server expects
    headers = {
        "Content-Type": "application/json",
        "elevenlabs-signature": signature,  # Use lowercase to match server expectation
        "User-Agent": "ElevenLabs/1.0"
    }
    
    # Send request
    url = "http://localhost:8000/webhooks/post-call"
    
    print(f"Testing webhook endpoint: {url}")
    print(f"Timestamp: {timestamp} ({datetime.fromtimestamp(timestamp)})")
    print(f"Signature header: {signature[:50]}...")
    print(f"Payload size: {len(payload_json)} bytes")
    print()
    
    try:
        response = requests.post(
            url,
            headers=headers,
            data=payload_json,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("\n✅ SUCCESS: Webhook processed successfully!")
            response_data = response.json()
            if "memory_id" in response_data:
                print(f"Memory ID: {response_data['memory_id']}")
        else:
            print(f"\n❌ FAILED: Status {response.status_code}")
            if response.status_code == 401:
                print("Authentication failed - check webhook secret configuration")
        
        return response.status_code == 200
        
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to webhook endpoint.")
        print("Make sure the server is running: python main.py")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("Testing Post-Call Webhook Endpoint")
    print("=" * 60)
    print()
    
    # Check if user wants to use provided timestamp
    use_provided = "--use-provided-timestamp" in sys.argv or "-p" in sys.argv
    
    if use_provided:
        print("⚠️  Using provided timestamp from payload")
        print("   This may fail if timestamp is in the future!")
        print()
    
    success = test_webhook(use_provided_timestamp=use_provided)
    
    print()
    print("=" * 60)
    if success:
        print("✅ Test completed successfully!")
    else:
        print("❌ Test failed. Check the error messages above.")
        print()
        print("Common issues:")
        print("1. Server not running - Start with: python main.py")
            print("2. Wrong HMAC key - Check ELEVENLABS_POST_CALL_HMAC_KEY in .env")
        print("3. Timestamp validation - If using provided timestamp, it may be in the future")
    print("=" * 60)

