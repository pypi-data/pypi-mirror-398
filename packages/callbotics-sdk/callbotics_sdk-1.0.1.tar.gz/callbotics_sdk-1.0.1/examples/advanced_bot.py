"""
Advanced Bot Example

This example demonstrates advanced configuration including:
- Manual configuration of each component
- Campaign creation and management
- Call analytics
- Error handling
"""

from callbotics_sdk import CallboticsClient, APIError, ValidationError

# Configuration
API_URL = "https://api.callbotics.ai"
EMAIL = "your-email@example.com"
PASSWORD = "your-password"

# API Keys
OPENAI_API_KEY = "sk-..."
RIME_API_KEY = "your-rime-key"
DEEPGRAM_API_KEY = "your-deepgram-key"
TELNYX_AUTH_TOKEN = "your-telnyx-token"
TELNYX_CONNECTION_ID = "your-connection-id"


def create_bot_with_advanced_config(client):
    """Create a bot with full control over each configuration"""

    print("\n=== Creating Advanced Bot Configuration ===")

    # 1. Create LLM Configuration with custom parameters
    print("\n1. Creating LLM configuration...")
    llm_config = client.llm_configs.create(
        name="GPT-4 Sales Config",
        llm_type="agent_chat_gpt",
        model="gpt-4",
        temperature=0.8,  # Higher temperature for more creative responses
        api_key=OPENAI_API_KEY,
        max_tokens=500,  # Limit response length
        top_p=0.9,
        frequency_penalty=0.5,  # Reduce repetition
    )
    print(f"   ✓ LLM Config ID: {llm_config['id']}")

    # 2. Create detailed prompt configuration
    print("\n2. Creating prompt configuration...")
    prompt_config = client.prompt_configs.create(
        name="Sales Assistant Prompt",
        background="""
You are Emma, a senior sales consultant for TechCorp Solutions.
You have 10 years of experience in B2B software sales.
You are calling to discuss how our AI automation platform can help
businesses reduce costs and increase efficiency.
        """,
        business_logic="""
1. Introduction Phase:
   - Greet warmly and introduce yourself
   - Ask if it's a good time to talk (respect their time)

2. Discovery Phase:
   - Ask about current pain points with manual processes
   - Listen actively and take mental notes
   - Ask follow-up questions to understand their needs

3. Solution Phase:
   - Present relevant features based on their needs
   - Use specific examples and case studies
   - Handle objections professionally

4. Closing Phase:
   - Summarize key benefits discussed
   - Schedule a demo or next steps
   - Thank them for their time

5. Important Rules:
   - Never be pushy or aggressive
   - If they say "not interested", politely thank them and end the call
   - Always offer to send information via email
   - Never discuss pricing without manager approval
        """,
        conversational_tips="""
- Use a confident, professional tone
- Mirror their communication style (formal/casual)
- Use active listening: "I understand that...", "That makes sense..."
- Pause occasionally to let them speak
- Use their name naturally in conversation
- Show genuine enthusiasm about helping them
- Keep responses under 30 seconds when possible
        """,
        prompt_variables={
            "company_name": "TechCorp Solutions",
            "product_name": "AI AutoPilot",
            "demo_scheduling_url": "https://calendly.com/techcorp/demo",
        },
    )
    print(f"   ✓ Prompt Config ID: {prompt_config['id']}")

    # 3. Create Rime voice configuration with optimal settings
    print("\n3. Creating voice configuration...")
    voice_config = client.voice_configs.create_rime(
        name="Rime Professional Female",
        api_key=RIME_API_KEY,
        speaker="bloom",  # Different voice
        model_id="mistv2",
        speed_alpha=1.15,  # Optimal conversational speed
        reduce_latency=True,  # Enable low-latency mode
        sampling_rate=22050,
        gender="female",
        accent="american",
    )
    print(f"   ✓ Voice Config ID: {voice_config['id']}")

    # 4. Create Deepgram transcriber with custom settings
    print("\n4. Creating transcriber configuration...")
    transcriber_config = client.transcriber_configs.create_deepgram(
        name="Deepgram High Accuracy",
        api_key=DEEPGRAM_API_KEY,
        language="en-US",
        model="nova-2-phonecall",  # Best for phone calls
        tier="nova",
    )
    print(f"   ✓ Transcriber Config ID: {transcriber_config['id']}")

    # 5. Create Telnyx telephony configuration
    print("\n5. Creating telephony configuration...")
    telephony_config = client.telephony_configs.create_telnyx(
        name="Telnyx Production",
        auth_token=TELNYX_AUTH_TOKEN,
        connection_id=TELNYX_CONNECTION_ID,
        from_number="+15559876543",  # Default caller ID
    )
    print(f"   ✓ Telephony Config ID: {telephony_config['id']}")

    # 6. Create the agent
    print("\n6. Creating agent...")
    agent = client.agents.create(
        name="Sales Bot - Emma",
        llm_config_id=llm_config["id"],
        prompt_config_id=prompt_config["id"],
        voice_config_id=voice_config["id"],
        transcriber_config_id=transcriber_config["id"],
        telephony_config_id=telephony_config["id"],
    )
    print(f"   ✓ Agent ID: {agent['id']}")

    return agent


def create_and_run_campaign(client, agent_id, contact_list_id):
    """Create and run a calling campaign"""

    print("\n=== Creating Campaign ===")

    try:
        campaign = client.campaigns.create(
            name="Q1 2024 Sales Outreach",
            agent_id=agent_id,
            direction="outbound",
            description="Reach out to potential clients about AI automation",
            concurrency=10,  # Make up to 10 simultaneous calls
            from_phone="+15559876543",
            recording=True,  # Record all calls for quality assurance
            initial_message="Hi, this is Emma from TechCorp Solutions. How are you doing today?",
            live_transfer="Warm",  # Enable warm transfer to human agent
            live_transfer_number="+15551234567",  # Sales manager number
            auto_hangup_ivr=True,  # Automatically hang up on voicemail/IVR
            auto_hangup_wait_time=15,  # Wait 15 seconds before auto-hangup
            webhook_url="https://your-app.com/webhooks/callbotics",
        )

        print(f"✓ Campaign created: {campaign['id']}")
        print(f"  Name: {campaign['name']}")
        print(f"  Status: {campaign['status']}")
        print(f"  Concurrency: {campaign['concurrency']}")

        # Check available concurrency before starting
        print("\nChecking available concurrency...")
        concurrency_info = client.campaigns.get_available_concurrency()
        print(f"  Available slots: {concurrency_info}")

        # Start the campaign
        print(f"\nStarting campaign with contact list: {contact_list_id}")
        result = client.campaigns.start(
            campaign_id=campaign["id"], contact_list_id=contact_list_id
        )

        print(f"✓ Campaign started successfully!")
        print(f"  Calls initiated: {result.get('total_calls', 0)}")

        return campaign

    except ValidationError as e:
        print(f"✗ Validation error: {e}")
        return None
    except APIError as e:
        print(f"✗ API error: {e}")
        return None


def monitor_campaign_progress(client, campaign_id):
    """Monitor campaign progress and call analytics"""

    print("\n=== Monitoring Campaign Progress ===")

    # Get campaign details
    campaign = client.campaigns.get(campaign_id)
    print(f"\nCampaign: {campaign['name']}")
    print(f"Status: {campaign['status']}")
    print(f"Total runs: {campaign.get('total_campaign_run', 0)}")

    # Get call statistics
    print("\nFetching call statistics...")
    calls = client.calls.list(campaign_id=campaign_id, per_page=100)

    if calls:
        total_calls = len(calls)
        completed = sum(1 for c in calls if c.get("status") == "ended")
        ongoing = sum(1 for c in calls if c.get("status") == "ongoing")
        failed = sum(1 for c in calls if c.get("status") == "failed")

        print(f"\nCall Statistics:")
        print(f"  Total calls: {total_calls}")
        print(f"  Completed: {completed}")
        print(f"  Ongoing: {ongoing}")
        print(f"  Failed: {failed}")

        # Get call duration summary
        summary = client.calls.get_summary(campaign_id=campaign_id)
        print(f"\nDuration Summary:")
        print(f"  Total minutes: {summary.get('total_minutes', 0)}")
        print(f"  Average duration: {summary.get('average_duration', 0)} seconds")

    else:
        print("No calls found for this campaign yet.")


def pause_and_resume_campaign(client, campaign_id):
    """Demonstrate pausing and resuming a campaign"""

    print("\n=== Pausing Campaign ===")
    result = client.campaigns.pause(campaign_id)
    print(f"✓ Campaign paused")

    print("\nPress Enter to resume the campaign...")
    input()

    print("\n=== Resuming Campaign ===")
    result = client.campaigns.pause(campaign_id)  # Toggle pause
    print(f"✓ Campaign resumed")


def main():
    # Initialize client
    print("Initializing Callbotics client...")
    client = CallboticsClient(API_URL)

    try:
        # Login
        print("Logging in...")
        client.login(EMAIL, PASSWORD)
        print(f"✓ Logged in as {client.user_info['email']}")

        # Create bot with advanced configuration
        agent = create_bot_with_advanced_config(client)

        # Note: You need to create a contact list separately
        # For this example, we'll use a placeholder ID
        contact_list_id = "your-contact-list-id"  # Replace with actual ID

        # Create and run campaign
        campaign = create_and_run_campaign(client, agent["id"], contact_list_id)

        if campaign:
            # Monitor progress
            monitor_campaign_progress(client, campaign["id"])

            # Optional: Pause and resume
            # pause_and_resume_campaign(client, campaign['id'])

        print("\n✓ Advanced example completed successfully!")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        raise


if __name__ == "__main__":
    main()
