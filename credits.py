#!/usr/bin/env python3
"""
ElevenLabs Credit Usage Analyzer

This script helps you understand how your ElevenLabs API credits are being used.
It connects to your ElevenLabs account and downloads detailed information about
all your API calls within a specific time period.

Think of this as a "credit usage detective" - it finds out exactly:
- When you made API calls
- How many credits each call used  
- What text was converted to speech
- Which voices were used
- How much your conversational AI calls cost

The results are automatically saved to JSON files (a computer-readable format)
and also printed to your screen so you can see them immediately.

HOW TO USE THIS SCRIPT:
    python credits.py <start_time> <end_time>

    The start_time and end_time are "Unix timestamps" - a special way computers
    measure time by counting seconds since January 1, 1970. You can get these
    timestamps from online tools like epochconverter.com

WHAT YOU NEED BEFORE RUNNING:
    1. Your ElevenLabs API key (get this from your ElevenLabs dashboard)
    2. Set it as an environment variable: export ELEVEN_API_STATS="your-key-here"
    3. Python 3.7+ and the 'elevenlabs' package installed (pip install elevenlabs)

WHAT FILES GET CREATED:
    - api_stats_<timestamp>.json: Automatic file with all your data
    - Custom filename if you use --output option
    - Both contain the same information in JSON format

EXAMPLE USAGE:
    export ELEVEN_API_STATS="sk-your-key-here"
    python credits.py 1640995200 1641081600
    python credits.py 1640995200000 1641081600000  # Milliseconds work too!
"""

# Import statements - these load the tools our script needs to work
import argparse  # Helps us handle command-line arguments (like start/end times)
import json      # Helps us work with JSON data format
import os        # Helps us access environment variables (like API keys)
import sys       # Helps us exit the program if something goes wrong
import time      # Helps us work with timestamps and current time
from datetime import datetime    # Helps us convert timestamps to readable dates
from typing import Dict, List, Any, Optional  # Helps with code documentation

from elevenlabs import ElevenLabs  # The official ElevenLabs Python library


def normalize_timestamp(timestamp: int) -> int:
    """
    Convert timestamp to milliseconds if it's in seconds.
    
    BEGINNER EXPLANATION:
    Sometimes people give us timestamps in seconds, sometimes in milliseconds.
    This function makes sure we're always working with milliseconds internally.
    
    If the timestamp is small (less than year 3000), we assume it's in seconds
    and multiply by 1000 to convert to milliseconds.
    
    Args:
        timestamp: A Unix timestamp in either seconds or milliseconds
        
    Returns:
        The timestamp converted to milliseconds
    """
    # If timestamp is less than year 3000 in seconds, assume it's in seconds
    if timestamp < 32503680000:  # Jan 1, 3000 in seconds
        return timestamp * 1000  # Convert seconds to milliseconds
    return timestamp  # Already in milliseconds


def format_timestamp(timestamp_ms: int) -> str:
    """
    Convert a timestamp in milliseconds to a human-readable date string.
    
    BEGINNER EXPLANATION:
    Computers store time as big numbers (milliseconds since 1970), but humans
    prefer to read dates like "2023-01-15 14:30:00". This function does that
    conversion for us.
    
    Args:
        timestamp_ms: Timestamp in milliseconds
        
    Returns:
        A nicely formatted date string like "2023-01-15 14:30:00 UTC"
    """
    # Convert milliseconds to seconds, then to a UTC datetime object, then to string
    # Using utcfromtimestamp ensures the time is correctly represented in UTC,
    # aligning with the "UTC" suffix we append to the formatted string.
    return datetime.utcfromtimestamp(timestamp_ms / 1000).strftime('%Y-%m-%d %H:%M:%S UTC')


def calculate_credits_used(item: Any) -> int:
    """
    Figure out how many credits an API call used by looking at character count changes.
    
    BEGINNER EXPLANATION:
    ElevenLabs tracks your credit usage by monitoring changes in your character count.
    When you make an API call, your available characters go down. This function
    calculates the difference to see how many credits that specific call used.
    
    Args:
        item: A history item from the ElevenLabs API
        
    Returns:
        Number of credits used for this API call
    """
    # Check if the item has character count information
    if hasattr(item, 'character_count_change_from') and hasattr(item, 'character_count_change_to'):
        # Credits used = starting count - ending count
        return item.character_count_change_from - item.character_count_change_to
    return 0  # If we can't calculate it, assume 0


def get_speech_history(client: ElevenLabs, start_ms: int, end_ms: int) -> List[Dict[str, Any]]:
    """
    Download all speech generation history (text-to-speech calls) within the time period.
    
    BEGINNER EXPLANATION:
    This function connects to ElevenLabs and downloads information about all the times
    you converted text to speech. It uses "pagination" - like flipping through pages
    of a book - to get all the data, since there might be thousands of calls.
    
    The API returns data in reverse chronological order (newest first), so we keep
    fetching pages until we get to calls older than our start time.
    
    Args:
        client: Connected ElevenLabs API client
        start_ms: Start time in milliseconds
        end_ms: End time in milliseconds
        
    Returns:
        List of dictionaries, each containing details about one speech generation call
    """
    print("📜 Fetching speech generation history...")
    
    all_history = []  # This will store all our API call data
    page_size = 1000  # How many items to fetch per request (1000 is the maximum)
    start_after_id = None  # Used for pagination - like a bookmark in the data
    
    # Keep looping until we've fetched all the data
    while True:
        try:
            # Make a request to the ElevenLabs API for a page of history
            response = client.history.list(
                page_size=page_size,
                start_after_history_item_id=start_after_id
            )
            
            # If this page has no items, we're done
            if not response.history:
                break
                
            # Look at each item in this page
            for item in response.history:
                item_time_ms = item.date_unix * 1000  # Convert to milliseconds
                
                # Only include items within our time range
                if start_ms <= item_time_ms <= end_ms:
                    credits_used = calculate_credits_used(item)
                    
                    # Create a dictionary with all the important information
                    call_data = {
                        "type": "speech_generation",  # What kind of API call this was
                        "id": item.history_item_id,   # Unique identifier
                        "timestamp": item.date_unix,  # When it happened (seconds)
                        "timestamp_ms": item_time_ms, # When it happened (milliseconds)
                        "formatted_time": format_timestamp(item_time_ms),  # Human-readable time
                        "credits_used": credits_used, # How many credits it cost
                        "text": item.text,           # The text that was converted to speech
                        "voice_id": item.voice_id,   # Which voice was used (ID)
                        "voice_name": item.voice_name, # Which voice was used (name)
                        "voice_category": str(item.voice_category) if item.voice_category else None,
                        "model_id": item.model_id,   # Which AI model was used
                        "content_type": item.content_type,  # File format (like mp3)
                        "source": str(item.source) if item.source else None,  # How the call was made
                        "character_count_from": item.character_count_change_from,  # Credits before
                        "character_count_to": item.character_count_change_to,    # Credits after
                        "request_id": item.request_id,  # Technical ID for debugging
                        "settings": item.settings,      # Voice settings used
                        "feedback": item.feedback.dict() if item.feedback else None,  # Any feedback given
                    }
                    all_history.append(call_data)
                
                # If this item is older than our start time, we can stop fetching
                # (since history is ordered newest to oldest)
                elif item_time_ms < start_ms:
                    return all_history
            
            # Check if there are more pages to fetch
            if not response.has_more:
                break
                
            # Set up to fetch the next page
            start_after_id = response.last_history_item_id
            print(f"📄 Fetched {len(all_history)} speech generations so far...")
            
        except Exception as e:
            print(f"❌ Error fetching speech history: {e}")
            break
    
    return all_history


def get_conversation_history(client: ElevenLabs, start_ms: int, end_ms: int) -> List[Dict[str, Any]]:
    """
    Download all conversational AI history within the time period.
    
    BEGINNER EXPLANATION:
    ElevenLabs offers conversational AI features where you can have phone calls
    or chats with AI agents. This function downloads information about all those
    conversations, including how much they cost and how long they lasted.
    
    This is more complex than speech generation because we need to fetch detailed
    information about each conversation individually.
    
    Args:
        client: Connected ElevenLabs API client
        start_ms: Start time in milliseconds  
        end_ms: End time in milliseconds
        
    Returns:
        List of dictionaries, each containing details about one conversation
    """
    print("🗣️  Fetching conversational AI history...")
    
    try:
        all_conversations = []  # Store all conversation data here
        cursor = None          # Used for pagination (like a bookmark)
        page_size = 100        # How many conversations to fetch per request
        
        # Convert milliseconds back to seconds for this specific API
        start_unix_secs = start_ms // 1000
        end_unix_secs = end_ms // 1000
        
        # Keep fetching pages until we have all conversations
        while True:
            # Get a page of conversations
            response = client.conversational_ai.conversations.list(
                cursor=cursor,
                call_start_after_unix=start_unix_secs,
                call_start_before_unix=end_unix_secs,
                page_size=page_size
            )
            
            # If no conversations on this page, we're done
            if not response.conversations:
                break
                
            # For each conversation, get detailed information
            for conversation in response.conversations:
                try:
                    # Fetch detailed data for this specific conversation
                    detailed_conv = client.conversational_ai.conversations.get(
                        conversation_id=conversation.conversation_id
                    )
                    
                    # Calculate total cost and token usage
                    total_cost = 0
                    total_llm_tokens = 0
                    
                    # Get the cost if available
                    if detailed_conv.metadata.cost:
                        total_cost = detailed_conv.metadata.cost
                    
                    # Sum up language model usage from the conversation transcript
                    for transcript_item in detailed_conv.transcript:
                        if hasattr(transcript_item, 'llm_usage') and transcript_item.llm_usage:
                            if hasattr(transcript_item.llm_usage, 'total_tokens'):
                                total_llm_tokens += transcript_item.llm_usage.total_tokens
                    
                    # Create a dictionary with all conversation information
                    conv_data = {
                        "type": "conversational_ai",  # Type of API call
                        "id": conversation.conversation_id,  # Unique ID
                        "agent_id": conversation.agent_id,   # Which AI agent was used
                        "timestamp": detailed_conv.metadata.start_time_unix_secs,  # When it started
                        "timestamp_ms": detailed_conv.metadata.start_time_unix_secs * 1000,  # In milliseconds
                        "formatted_time": format_timestamp(detailed_conv.metadata.start_time_unix_secs * 1000),
                        "credits_used": total_cost,  # How many credits it cost
                        "duration_secs": detailed_conv.metadata.call_duration_secs,  # How long it lasted
                        "status": str(conversation.status),  # Success, failed, etc.
                        "total_llm_tokens": total_llm_tokens,  # Language model usage
                        "accepted_time": detailed_conv.metadata.accepted_time_unix_secs,  # When call was answered
                        "termination_reason": detailed_conv.metadata.termination_reason,  # Why call ended
                        "main_language": detailed_conv.metadata.main_language,  # Primary language used
                        "charging_info": detailed_conv.metadata.charging.dict() if detailed_conv.metadata.charging else None,
                        "phone_call_info": detailed_conv.metadata.phone_call.dict() if detailed_conv.metadata.phone_call else None,
                        "error_info": detailed_conv.metadata.error.dict() if detailed_conv.metadata.error else None,
                        "transcript_summary": {
                            "total_items": len(detailed_conv.transcript),
                            "user_messages": len([t for t in detailed_conv.transcript if t.role == "user"]),
                            "assistant_messages": len([t for t in detailed_conv.transcript if t.role == "assistant"]),
                        }
                    }
                    all_conversations.append(conv_data)
                    
                except Exception as e:
                    # If we can't get detailed info, save basic info with error note
                    print(f"⚠️  Warning: Could not get details for conversation {conversation.conversation_id}: {e}")
                    conv_data = {
                        "type": "conversational_ai",
                        "id": conversation.conversation_id,
                        "agent_id": conversation.agent_id,
                        "timestamp": conversation.start_time_unix_secs,
                        "timestamp_ms": conversation.start_time_unix_secs * 1000,
                        "formatted_time": format_timestamp(conversation.start_time_unix_secs * 1000),
                        "credits_used": 0,
                        "duration_secs": conversation.call_duration_secs,
                        "status": str(conversation.status),
                        "error": f"Could not fetch detailed data: {e}"
                    }
                    all_conversations.append(conv_data)
            
            # Check if there are more pages
            if not hasattr(response, 'cursor') or not response.cursor:
                break
                
            cursor = response.cursor
            print(f"📞 Fetched {len(all_conversations)} conversations so far...")
        
        return all_conversations
        
    except Exception as e:
        # If conversational AI features aren't available, that's okay
        print(f"⚠️  Note: Could not fetch conversational AI data (might not be available): {e}")
        return []


def get_usage_analytics(client: ElevenLabs, start_ms: int, end_ms: int) -> Dict[str, Any]:
    """
    Get aggregated usage analytics for the time period.
    
    BEGINNER EXPLANATION:
    This function gets summary statistics about your usage during the time period.
    It's like getting a "bird's eye view" of your credit usage, broken down by
    different categories like voice type or day of the week.
    
    Args:
        client: Connected ElevenLabs API client
        start_ms: Start time in milliseconds
        end_ms: End time in milliseconds
        
    Returns:
        Dictionary containing usage analytics data
    """
    print("📊 Fetching usage analytics...")
    
    try:
        # Convert millisecond timestamps back to seconds as required by the API
        start_unix = start_ms // 1000
        end_unix = end_ms // 1000

        # Request analytics data from the API
        analytics = client.usage.get(
            start_unix=start_unix,   # Time range start (seconds)
            end_unix=end_unix,       # Time range end (seconds)
            breakdown_type="voice",  # Group data by voice type
            aggregation_interval="day",  # Group data by day
            metric="credits"         # Show credit usage (not just call counts)
        )
        
        return {
            "usage_analytics": analytics.dict() if hasattr(analytics, 'dict') else str(analytics),
            "fetched_at": format_timestamp(int(time.time() * 1000))  # When we got this data
        }
    except Exception as e:
        print(f"⚠️  Warning: Could not fetch usage analytics: {e}")
        return {"error": str(e)}


def get_subscription_info(client: ElevenLabs) -> Dict[str, Any]:
    """
    Get information about your current ElevenLabs subscription and usage limits.
    
    BEGINNER EXPLANATION:
    This function downloads information about your ElevenLabs account, including:
    - What plan you're on (Free, Starter, Pro, etc.)
    - How many credits you've used this month
    - How many credits you have left
    - When your credits will reset
    - How many voice slots you're using
    
    This helps you understand if you're getting close to your limits.
    
    Args:
        client: Connected ElevenLabs API client
        
    Returns:
        Dictionary containing subscription and usage information
    """
    print("💳 Fetching subscription information...")
    
    try:
        # Get user account information from the API
        user_info = client.user.get()
        subscription = user_info.subscription
        
        # Extract the important subscription details
        subscription_data = {
            "tier": subscription.tier,  # Your plan level (Free, Pro, etc.)
            "character_count_used": subscription.character_count,  # Credits used this cycle
            "character_limit": subscription.character_limit,       # Total credits per cycle
            "next_reset_unix": subscription.next_character_count_reset_unix,  # When credits reset
            "next_reset_formatted": format_timestamp(subscription.next_character_count_reset_unix * 1000) if subscription.next_character_count_reset_unix else None,
            "voice_slots_used": subscription.voice_slots_used,     # Custom voices you've made
            "voice_limit": subscription.voice_limit,               # Max custom voices allowed
            "professional_voice_slots_used": subscription.professional_voice_slots_used,  # Pro voices
            "professional_voice_limit": subscription.professional_voice_limit,            # Max pro voices
            "status": str(subscription.status),  # Active, cancelled, etc.
            "currency": str(subscription.currency) if subscription.currency else None,  # Billing currency
        }
        
        # Add detailed usage information if available
        if user_info.subscription_extras and user_info.subscription_extras.usage:
            usage = user_info.subscription_extras.usage
            subscription_data["detailed_usage"] = {
                "rollover_credits_used": usage.rollover_credits_used,           # Credits from previous month
                "rollover_credits_quota": usage.rollover_credits_quota,         # Max rollover allowed
                "subscription_cycle_credits_used": usage.subscription_cycle_credits_used,  # This month's usage
                "subscription_cycle_credits_quota": usage.subscription_cycle_credits_quota,  # This month's limit
                "manually_gifted_credits_used": usage.manually_gifted_credits_used,  # Bonus credits used
                "manually_gifted_credits_quota": usage.manually_gifted_credits_quota,  # Bonus credits available
                "paid_usage_based_credits_used": usage.paid_usage_based_credits_used,  # Pay-per-use credits
                "actual_reported_credits": usage.actual_reported_credits,  # Total credits used
            }
        
        return subscription_data
        
    except Exception as e:
        print(f"⚠️  Warning: Could not fetch subscription info: {e}")
        return {"error": str(e)}


def summarize_usage(all_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Create a summary of all the API calls and credit usage.
    
    BEGINNER EXPLANATION:
    This function takes all the individual API calls we've collected and creates
    useful summaries, like:
    - Total credits used
    - How many calls of each type were made
    - Which voices used the most credits
    - Which applications or sources made the most calls
    - The time range of all the calls
    
    It's like creating a "executive summary" of your API usage.
    
    Args:
        all_calls: List of all API calls (both speech and conversational AI)
        
    Returns:
        Dictionary containing various usage summaries
    """
    # Calculate total credits used across all calls
    total_credits = sum(call.get("credits_used", 0) for call in all_calls)
    
    # Group calls by type (speech generation vs conversational AI)
    by_type = {}
    for call in all_calls:
        call_type = call["type"]
        if call_type not in by_type:
            by_type[call_type] = {"count": 0, "credits": 0}
        by_type[call_type]["count"] += 1
        by_type[call_type]["credits"] += call.get("credits_used", 0)
    
    # Group speech generation calls by source (web app, API, mobile app, etc.)
    by_source = {}
    for call in all_calls:
        if call["type"] == "speech_generation" and call.get("source"):
            source = call["source"]
            if source not in by_source:
                by_source[source] = {"count": 0, "credits": 0}
            by_source[source]["count"] += 1
            by_source[source]["credits"] += call.get("credits_used", 0)
    
    # Group speech generation calls by voice used
    by_voice = {}
    for call in all_calls:
        if call["type"] == "speech_generation" and call.get("voice_name"):
            voice = call["voice_name"]
            if voice not in by_voice:
                by_voice[voice] = {"count": 0, "credits": 0}
            by_voice[voice]["count"] += 1
            by_voice[voice]["credits"] += call.get("credits_used", 0)
    
    # Create and return the complete summary
    return {
        "total_api_calls": len(all_calls),
        "total_credits_used": total_credits,
        "breakdown_by_type": by_type,
        "breakdown_by_source": by_source,
        "breakdown_by_voice": by_voice,
        "time_range": {
            "earliest_call": min(call["formatted_time"] for call in all_calls) if all_calls else None,
            "latest_call": max(call["formatted_time"] for call in all_calls) if all_calls else None,
        }
    }


def main():
    """
    Main function that runs when the script is executed.
    
    BEGINNER EXPLANATION:
    This is the "main" function that coordinates everything. It:
    1. Processes the command-line arguments you provided
    2. Sets up the connection to ElevenLabs
    3. Fetches all the data from various APIs
    4. Creates summaries and saves results to files
    5. Prints everything to your screen
    
    Think of this as the "conductor" that directs all the other functions.
    """
    # Set up command-line argument parsing
    # This lets users provide options like --output, --pretty, etc.
    parser = argparse.ArgumentParser(
        description="Retrieve detailed ElevenLabs credit usage information",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__  # Include the script's docstring in help
    )
    parser.add_argument("start_timestamp", type=int, help="Start Unix timestamp (seconds or milliseconds)")
    parser.add_argument("end_timestamp", type=int, help="End Unix timestamp (seconds or milliseconds)")
    parser.add_argument("--output", "-o", help="Additional output file (automatic timestamped file always created)")
    parser.add_argument("--pretty", action="store_true", help="Pretty print JSON output")
    parser.add_argument("--summary-only", action="store_true", help="Show only summary, not individual calls")
    
    # Parse the arguments the user provided
    args = parser.parse_args()
    
    # Get the API key from environment variables
    # Environment variables are a secure way to store sensitive information like API keys
    api_key = os.getenv("ELEVEN_API_STATS")
    if not api_key:
        print("❌ Error: ELEVEN_API_STATS environment variable not set")
        print("Please set your API key: export ELEVEN_API_STATS='your-api-key-here'")
        sys.exit(1)  # Exit with error code
    
    # Normalize timestamps to milliseconds (handles both seconds and milliseconds input)
    start_ms = normalize_timestamp(args.start_timestamp)
    end_ms = normalize_timestamp(args.end_timestamp)
    
    # Basic validation: start time must be before end time
    if start_ms >= end_ms:
        print("❌ Error: Start timestamp must be before end timestamp")
        sys.exit(1)
    
    # Generate a filename for the automatic output file
    # This ensures each run creates a unique file with a timestamp
    current_timestamp = int(time.time())
    auto_filename = f"api_stats_{current_timestamp}.json"
    
    # Print information about what we're about to do
    print(f"🔍 Analyzing ElevenLabs usage from {format_timestamp(start_ms)} to {format_timestamp(end_ms)}")
    print(f"🔑 Using API key: ...{api_key[-8:]}")  # Show only last 8 characters for security
    print(f"📁 Output will be saved to: {auto_filename}")
    print()
    
    # Try to connect to the ElevenLabs API
    try:
        client = ElevenLabs(api_key=api_key)
        print("✅ Connected to ElevenLabs API")
    except Exception as e:
        print(f"❌ Error connecting to ElevenLabs: {e}")
        sys.exit(1)
    
    # Gather all the data from different ElevenLabs APIs
    # Each function handles a different type of data
    subscription_info = get_subscription_info(client)
    speech_history = get_speech_history(client, start_ms, end_ms)
    conversation_history = get_conversation_history(client, start_ms, end_ms)
    usage_analytics = get_usage_analytics(client, start_ms, end_ms)
    
    # Combine all API calls into one list and sort by time
    all_calls = speech_history + conversation_history
    all_calls.sort(key=lambda x: x["timestamp"])  # Sort chronologically
    
    # Create a summary of all the usage data
    summary = summarize_usage(all_calls)
    
    # Print a quick summary to the screen
    print(f"\n📋 Summary:")
    print(f"   Total API calls: {summary['total_api_calls']}")
    print(f"   Total credits used: {summary['total_credits_used']}")
    print(f"   Speech generations: {summary['breakdown_by_type'].get('speech_generation', {}).get('count', 0)}")
    print(f"   Conversational AI calls: {summary['breakdown_by_type'].get('conversational_ai', {}).get('count', 0)}")
    
    # Prepare all the data for output in a structured format
    output_data = {
        "query_info": {
            "start_timestamp": args.start_timestamp,        # Original input
            "end_timestamp": args.end_timestamp,            # Original input
            "start_timestamp_ms": start_ms,                 # Normalized to milliseconds
            "end_timestamp_ms": end_ms,                     # Normalized to milliseconds
            "start_time_formatted": format_timestamp(start_ms),  # Human-readable
            "end_time_formatted": format_timestamp(end_ms),      # Human-readable
            "generated_at": format_timestamp(int(time.time() * 1000)),  # When this report was created
        },
        "subscription_info": subscription_info,
        "summary": summary,
        "usage_analytics": usage_analytics,
    }
    
    # Include individual calls unless user requested summary only
    if not args.summary_only:
        output_data["individual_calls"] = all_calls
    
    # Convert the data to JSON format
    # Pretty-print if requested (makes it easier to read but larger file size)
    json_output = json.dumps(output_data, indent=2 if args.pretty else None, ensure_ascii=False)
    
    # Always save to the automatic timestamped file
    with open(auto_filename, 'w', encoding='utf-8') as f:
        f.write(json_output)
    print(f"\n💾 Results automatically saved to {auto_filename}")
    
    # Also save to custom output file if the user specified one
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(json_output)
        print(f"💾 Results also saved to {args.output}")
    
    # Always print the full results to standard output (the screen)
    # This lets users pipe the output to other tools if needed
    print("\n" + "="*80)
    print(json_output)


# This is a Python convention - only run main() if this script is executed directly
# (not if it's imported as a module by another script)
if __name__ == "__main__":
    main() 