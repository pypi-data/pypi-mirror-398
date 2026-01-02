"""
Basic Bot Example

This example shows the simplest way to create and use a Callbotics voice bot.
"""

from callbotics_sdk import CallboticsClient

# Configuration
API_URL = "https://api.callbotics.ai"
EMAIL = "your-email@example.com"
PASSWORD = "your-password"

# API Keys (replace with your own)
OPENAI_API_KEY = "sk-..."
RIME_API_KEY = "your-rime-key"
DEEPGRAM_API_KEY = "your-deepgram-key"
TELNYX_AUTH_TOKEN = "your-telnyx-token"
TELNYX_CONNECTION_ID = "your-connection-id"


def main():
    # Initialize client
    print("Initializing Callbotics client...")
    client = CallboticsClient(API_URL)

    # Login
    print("Logging in...")
    client.login(EMAIL, PASSWORD)
    print(f"✓ Logged in as {client.user_info['email']}")

    # Create a complete bot in one call
    print("\nCreating bot...")
    bot = client.create_complete_bot(
        name="My First Support Bot",
        # LLM Configuration
        llm_type="agent_chat_gpt",
        llm_model="gpt-4",
        llm_api_key=OPENAI_API_KEY,
        llm_temperature=0.7,
        # Prompt Configuration
        prompt_background=(
            "You are a friendly and professional customer support agent. "
            "Your goal is to help customers with their questions and issues."
        ),
        prompt_business_logic=(
            "1. Always greet the customer warmly\n"
            "2. Listen to their concern carefully\n"
            "3. Provide clear and helpful solutions\n"
            "4. Ask if there's anything else you can help with before ending the call"
        ),
        prompt_conversational_tips=(
            "- Use a warm, empathetic tone\n"
            "- Keep responses concise and clear\n"
            "- Show genuine interest in helping\n"
            "- Use the customer's name when provided"
        ),
        # Voice Configuration
        voice_api_key=RIME_API_KEY,
        voice_speaker="wildflower",  # Female voice
        voice_speed=1.2,  # Slightly faster than normal
        # Transcriber Configuration
        transcriber_api_key=DEEPGRAM_API_KEY,
        transcriber_language="en-US",
        # Telephony Configuration
        telephony_provider="telnyx",
        telephony_auth_token=TELNYX_AUTH_TOKEN,
        telephony_connection_id=TELNYX_CONNECTION_ID,
    )

    print(f"✓ Bot created successfully!")
    print(f"  Agent ID: {bot['agent']['id']}")
    print(f"  Agent Name: {bot['agent']['name']}")

    # Make a test call
    print("\nMaking a test call...")
    call = client.calls.create(
        agent_id=bot["agent"]["id"],
        to_number="+15551234567",  # Replace with actual phone number
        from_number="+15559876543",  # Replace with your Telnyx number
    )

    print(f"✓ Call initiated!")
    print(f"  Call ID: {call['id']}")
    print(f"  Status: {call['status']}")

    # Get call details
    print("\nFetching call details...")
    call_details = client.calls.get(call["id"])
    print(f"  To: {call_details.get('to_phone')}")
    print(f"  From: {call_details.get('from_phone')}")
    print(f"  Duration: {call_details.get('duration', 0)} seconds")

    print("\n✓ Example completed successfully!")


if __name__ == "__main__":
    main()
