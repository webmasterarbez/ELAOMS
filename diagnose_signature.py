#!/usr/bin/env python3
"""Diagnose signature mismatch."""
import hmac
import hashlib
from config import settings

# Exact payload from user's request (as provided)
exact_payload = '{"type": "post_call_transcription", "event_timestamp": 1762713911, "data": {"agent_id": "agent_5001k9myfdmae9ntkrhxfr5b4tqy", "conversation_id": "conv_6601k9mywx20fxcbpyv2wtff3zph", "status": "done", "user_id": null, "branch_id": null, "transcript": [{"role": "agent", "agent_metadata": {"agent_id": "agent_5001k9myfdmae9ntkrhxfr5b4tqy", "branch_id": null, "workflow_node_id": null}, "message": "Hello! What is your name?", "multivoice_message": null, "tool_calls": [], "tool_results": [], "feedback": null, "llm_override": null, "time_in_call_secs": 0, "conversation_turn_metrics": {"metrics": {"convai_tts_service_ttfb": {"elapsed_time": 0.18307536099746358}}}, "rag_retrieval_info": null, "llm_usage": null, "interrupted": false, "original_message": null, "source_medium": null}, {"role": "user", "agent_metadata": null, "message": "My name is Stefan.", "multivoice_message": null, "tool_calls": [], "tool_results": [], "feedback": null, "llm_override": null, "time_in_call_secs": 2, "conversation_turn_metrics": {"metrics": {"convai_asr_trailing_service_latency": {"elapsed_time": 0.10322719800751656}}}, "rag_retrieval_info": null, "llm_usage": null, "interrupted": false, "original_message": null, "source_medium": "audio"}, {"role": "agent", "agent_metadata": {"agent_id": "agent_5001k9myfdmae9ntkrhxfr5b4tqy", "branch_id": null, "workflow_node_id": null}, "message": "It\'s a pleasure to meet you, Stefan. How can I assist you today?", "multivoice_message": null, "tool_calls": [], "tool_results": [], "feedback": null, "llm_override": null, "time_in_call_secs": 4, "conversation_turn_metrics": {"metrics": {"convai_llm_service_ttf_sentence": {"elapsed_time": 0.3677040940092411}, "convai_llm_service_ttfb": {"elapsed_time": 0.2512462360027712}, "convai_llm_service_tt_last_sentence": {"elapsed_time": 0.3676769800076727}, "convai_tts_service_ttfb": {"elapsed_time": 0.24353966901253443}}}, "rag_retrieval_info": null, "llm_usage": {"model_usage": {"gemini-2.5-flash": {"input": {"tokens": 452, "price": 6.78e-05}, "input_cache_read": {"tokens": 0, "price": 0.0}, "input_cache_write": {"tokens": 0, "price": 0.0}, "output_total": {"tokens": 18, "price": 1.0799999999999998e-05}}}}, "interrupted": false, "original_message": null, "source_medium": null}, {"role": "user", "agent_metadata": null, "message": "You know, can you help me build a full user profile?", "multivoice_message": null, "tool_calls": [], "tool_results": [], "feedback": null, "llm_override": null, "time_in_call_secs": 9, "conversation_turn_metrics": {"metrics": {"convai_asr_trailing_service_latency": {"elapsed_time": 0.11716135799360927}}}, "rag_retrieval_info": null, "llm_usage": null, "interrupted": false, "original_message": null, "source_medium": "audio"}, {"role": "agent", "agent_metadata": {"agent_id": "agent_5001k9myfdmae9ntkrhxfr5b4tqy", "branch_id": null, "workflow_node_id": null}, "message": "Yes, I can certainly help you build a full user profile. To do that, I\'ll need a few pieces of information from you. Could you please provide your first name, last name, email address, and address?", "multivoice_message": null, "tool_calls": [], "tool_results": [], "feedback": null, "llm_override": null, "time_in_call_secs": 15, "conversation_turn_metrics": {"metrics": {"convai_llm_service_ttf_sentence": {"elapsed_time": 0.34064114099601284}, "convai_llm_service_ttfb": {"elapsed_time": 0.26478277100250125}, "convai_llm_service_tt_last_sentence": {"elapsed_time": 0.42866607100586407}, "convai_tts_service_ttfb": {"elapsed_time": 0.22271765899495222}}}, "rag_retrieval_info": null, "llm_usage": {"model_usage": {"gemini-2.5-flash": {"input": {"tokens": 483, "price": 7.245e-05}, "input_cache_read": {"tokens": 0, "price": 0.0}, "input_cache_write": {"tokens": 0, "price": 0.0}, "output_total": {"tokens": 46, "price": 2.7599999999999997e-05}}}}, "interrupted": false, "original_message": null, "source_medium": null}, {"role": "user", "agent_metadata": null, "message": "My first name is Stefan. My last name is Briat. My email is stefan at arvez dot com. My address is 112 Cobblestone Lane Winona Minnesota 55987.", "multivoice_message": null, "tool_calls": [], "tool_results": [], "feedback": null, "llm_override": null, "time_in_call_secs": 26, "conversation_turn_metrics": {"metrics": {"convai_asr_trailing_service_latency": {"elapsed_time": 0.15962386199680623}}}, "rag_retrieval_info": null, "llm_usage": null, "interrupted": false, "original_message": null, "source_medium": "audio"}, {"role": "agent", "agent_metadata": {"agent_id": "agent_5001k9myfdmae9ntkrhxfr5b4tqy", "branch_id": null, "workflow_node_id": null}, "message": "Thank you, Stefan. I have recorded your first name as Stefan, your last name as Briat, your email address as stefan at arvez dot com, and your address as 112 Cobblestone Lane, Winona, Minnesota, 55987. Is there anything else I can help you with today?", "multivoice_message": null, "tool_calls": [], "tool_results": [], "feedback": null, "llm_override": null, "time_in_call_secs": 53, "conversation_turn_metrics": {"metrics": {"convai_llm_service_ttf_sentence": {"elapsed_time": 0.4076567839947529}, "convai_llm_service_ttfb": {"elapsed_time": 0.3491007470001932}, "convai_llm_service_tt_last_sentence": {"elapsed_time": 0.5599479519878514}, "convai_tts_service_ttfb": {"elapsed_time": 0.1714535430073738}}}, "rag_retrieval_info": null, "llm_usage": {"model_usage": {"gemini-2.5-flash": {"input": {"tokens": 571, "price": 8.565e-05}, "input_cache_read": {"tokens": 0, "price": 0.0}, "input_cache_write": {"tokens": 0, "price": 0.0}, "output_total": {"tokens": 66, "price": 3.96e-05}}}}, "interrupted": false, "original_message": null, "source_medium": null}, {"role": "user", "agent_metadata": null, "message": "No, this is great. Thank you so much. Have a great day.", "multivoice_message": null, "tool_calls": [], "tool_results": [], "feedback": null, "llm_override": null, "time_in_call_secs": 68, "conversation_turn_metrics": {"metrics": {"convai_asr_trailing_service_latency": {"elapsed_time": 0.21701358100108337}}}, "rag_retrieval_info": null, "llm_usage": null, "interrupted": false, "original_message": null, "source_medium": "audio"}, {"role": "agent", "agent_metadata": {"agent_id": "agent_5001k9myfdmae9ntkrhxfr5b4tqy", "branch_id": null, "workflow_node_id": null}, "message": "You\'re very welcome, Stefan! I\'m glad I could help. You have a great day too!", "multivoice_message": null, "tool_calls": [], "tool_results": [], "feedback": null, "llm_override": null, "time_in_call_secs": 72, "conversation_turn_metrics": {"metrics": {"convai_llm_service_ttf_sentence": {"elapsed_time": 0.38537538700620644}, "convai_llm_service_ttfb": {"elapsed_time": 0.3165526290104026}, "convai_llm_service_tt_last_sentence": {"elapsed_time": 0.4237879020074615}, "convai_tts_service_ttfb": {"elapsed_time": 0.23150092799915}}}, "rag_retrieval_info": null, "llm_usage": {"model_usage": {"gemini-2.5-flash": {"input": {"tokens": 653, "price": 9.795000000000001e-05}, "input_cache_read": {"tokens": 0, "price": 0.0}, "input_cache_write": {"tokens": 0, "price": 0.0}, "output_total": {"tokens": 23, "price": 1.3799999999999998e-05}}}}, "interrupted": false, "original_message": null, "source_medium": null}], "metadata": {"start_time_unix_secs": 1762713827, "accepted_time_unix_secs": 1762713827, "call_duration_secs": 79, "cost": 531, "deletion_settings": {"deletion_time_unix_secs": null, "deleted_logs_at_time_unix_secs": null, "deleted_audio_at_time_unix_secs": null, "deleted_transcript_at_time_unix_secs": null, "delete_transcript_and_pii": false, "delete_audio": false}, "feedback": {"type": null, "overall_score": null, "likes": 0, "dislikes": 0, "rating": null, "comment": null}, "authorization_method": "signed_url", "charging": {"dev_discount": false, "is_burst": false, "tier": "creator", "llm_usage": {"irreversible_generation": {"model_usage": {"gemini-2.5-flash": {"input": {"tokens": 2159, "price": 0.00032385}, "input_cache_read": {"tokens": 0, "price": 0.0}, "input_cache_write": {"tokens": 0, "price": 0.0}, "output_total": {"tokens": 153, "price": 9.18e-05}}}}, "initiated_generation": {"model_usage": {"gemini-2.5-flash": {"input": {"tokens": 2159, "price": 0.00032385}, "input_cache_read": {"tokens": 0, "price": 0.0}, "input_cache_write": {"tokens": 0, "price": 0.0}, "output_total": {"tokens": 153, "price": 9.18e-05}}}}}, "llm_price": 0.00041565, "llm_charge": 1, "call_charge": 530, "free_minutes_consumed": 0.0, "free_llm_dollars_consumed": 0.0}, "phone_call": {"direction": "inbound", "phone_number_id": "phnum_01jxj3hwx1fava7g3snzm5e2f8", "agent_number": "+16123241623", "external_number": "+16129782029", "type": "twilio", "stream_sid": "MZ34dda22b858da62893472c6884610479", "call_sid": "CA46088a7981a0f1671ea831f63c33fac3"}, "batch_call": null, "termination_reason": "Call ended by remote party", "error": null, "main_language": "en", "rag_usage": null, "text_only": false, "features_usage": {"language_detection": {"enabled": false, "used": false}, "transfer_to_agent": {"enabled": false, "used": false}, "transfer_to_string": {"enabled": false, "used": false}, "multivoice": {"enabled": false, "used": false}, "dtmf_tones": {"enabled": false, "used": false}, "external_mcp_servers": {"enabled": false, "used": false}, "pii_zrm_workspace": false, "pii_zrm_agent": false, "tool_dynamic_variable_updates": {"enabled": false, "used": false}, "is_livekit": false, "voicemail_detection": {"enabled": false, "used": false}, "workflow": {"enabled": false, "tool_node": {"enabled": false, "used": false}, "standalone_agent_node": {"enabled": false, "used": false}, "phone_number_node": {"enabled": false, "used": false}, "end_node": {"enabled": false, "used": false}}, "agent_testing": {"enabled": false, "tests_ran_after_last_modification": false, "tests_ran_in_last_7_days": false}}, "eleven_assistant": {"is_eleven_assistant": false}, "initiator_id": null, "conversation_initiation_source": "twilio", "conversation_initiation_source_version": null, "timezone": null, "initiation_trigger": {"trigger_type": "default"}, "async_metadata": null, "whatsapp": null, "agent_created_from": "ui", "agent_last_updated_from": "ui"}, "analysis": {"evaluation_criteria_results": {}, "data_collection_results": {}}'

received_signature = "v0=cdb6055034127af9ce8f8be05ca13cd61d1da45bdb6dfda3a5d296fe735e9f7b"
timestamp = "1762713911"

print("=" * 60)
print("Signature Diagnosis")
print("=" * 60)
print()
print(f"HMAC key configured: {'Yes' if settings.elevenlabs_post_call_hmac_key else 'No'}")
if settings.elevenlabs_post_call_hmac_key:
    print(f"HMAC key length: {len(settings.elevenlabs_post_call_hmac_key)}")
    print(f"HMAC key first 10 chars: {settings.elevenlabs_post_call_hmac_key[:10]}...")
    print(f"HMAC key last 10 chars: ...{settings.elevenlabs_post_call_hmac_key[-10:]}")
print()
print(f"Timestamp: {timestamp}")
print(f"Payload length: {len(exact_payload)} bytes")
print()

# Generate expected signature
full_payload_to_sign = f"{timestamp}.{exact_payload}"
print(f"Payload to sign (first 200 chars): {full_payload_to_sign[:200]}...")
print(f"Payload to sign length: {len(full_payload_to_sign)} bytes")
print()

mac = hmac.new(
    key=settings.elevenlabs_post_call_hmac_key.encode("utf-8"),
    msg=full_payload_to_sign.encode("utf-8"),
    digestmod=hashlib.sha256,
)
expected_digest = 'v0=' + mac.hexdigest()

print("=" * 60)
print("Signature Comparison")
print("=" * 60)
print()
print(f"Expected: {expected_digest}")
print(f"Received: {received_signature}")
print()
print(f"Match: {expected_digest == received_signature}")
print()

if expected_digest != received_signature:
    print("❌ SIGNATURE MISMATCH!")
    print()
    print("Possible causes:")
    print("1. HMAC key mismatch - Check ELEVENLABS_POST_CALL_HMAC_KEY in .env")
    print("2. Payload format difference - The exact JSON format matters")
    print("3. Payload truncation - The payload might be incomplete")
    print()
    print("To fix:")
    print("- Verify the webhook secret in .env matches ElevenLabs exactly")
    print("- Ensure no extra whitespace or formatting differences")
    print("- Check if the payload was truncated when copying")

