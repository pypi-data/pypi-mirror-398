"""
Campaign Management Example

This example demonstrates comprehensive campaign management including:
- Listing and filtering campaigns
- Managing campaign lifecycle
- Bulk operations
- Real-time monitoring
"""

from callbotics_sdk import CallboticsClient
import time
from datetime import datetime, timedelta


# Configuration
API_URL = "https://api.callbotics.ai"
API_TOKEN = "your-jwt-token"  # Or use email/password login


def list_all_campaigns(client):
    """List and filter campaigns"""

    print("\n=== Listing All Campaigns ===")

    # Get all campaigns (paginated)
    page = 1
    all_campaigns = []

    while True:
        campaigns = client.campaigns.list(page=page, per_page=20)

        if not campaigns:
            break

        all_campaigns.extend(campaigns)
        page += 1

    print(f"Total campaigns: {len(all_campaigns)}")

    # Group by status
    by_status = {}
    for campaign in all_campaigns:
        status = campaign.get("status", "unknown")
        by_status[status] = by_status.get(status, 0) + 1

    print("\nCampaigns by status:")
    for status, count in by_status.items():
        print(f"  {status}: {count}")

    return all_campaigns


def filter_campaigns(client):
    """Demonstrate campaign filtering"""

    print("\n=== Filtering Campaigns ===")

    # Filter by status
    print("\nOngoing campaigns:")
    ongoing = client.campaigns.list(status="ongoing", per_page=10)
    for campaign in ongoing:
        print(f"  - {campaign['name']} (ID: {campaign['id']})")

    # Filter by direction
    print("\nOutbound campaigns:")
    outbound = client.campaigns.list(direction="outbound", per_page=10)
    for campaign in outbound:
        print(f"  - {campaign['name']} (ID: {campaign['id']})")

    # Filter by name (regex search)
    print("\nCampaigns with 'sales' in name:")
    sales = client.campaigns.list(name="sales", per_page=10)
    for campaign in sales:
        print(f"  - {campaign['name']} (ID: {campaign['id']})")


def manage_campaign_lifecycle(client, agent_id, contact_list_id):
    """Demonstrate full campaign lifecycle management"""

    print("\n=== Campaign Lifecycle Management ===")

    # 1. Create campaign
    print("\n1. Creating campaign...")
    campaign = client.campaigns.create(
        name=f"Test Campaign {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        agent_id=agent_id,
        direction="outbound",
        concurrency=3,
        from_phone="+15559876543",
        recording=True,
    )
    print(f"   ✓ Created: {campaign['id']}")

    # 2. Update campaign settings
    print("\n2. Updating campaign settings...")
    updated_campaign = client.campaigns.update(
        campaign_id=campaign["id"],
        concurrency=5,  # Increase concurrency
        description="Updated campaign description",
    )
    print(f"   ✓ Updated concurrency to {updated_campaign['concurrency']}")

    # 3. Start campaign
    print("\n3. Starting campaign...")
    start_result = client.campaigns.start(
        campaign_id=campaign["id"], contact_list_id=contact_list_id
    )
    print(f"   ✓ Campaign started")

    # 4. Monitor for a bit
    print("\n4. Monitoring campaign (10 seconds)...")
    time.sleep(10)

    # Check status
    current = client.campaigns.get(campaign["id"])
    print(f"   Status: {current['status']}")
    print(f"   Total runs: {current.get('total_campaign_run', 0)}")

    # 5. Pause campaign
    print("\n5. Pausing campaign...")
    client.campaigns.pause(campaign["id"])
    print(f"   ✓ Campaign paused")

    # 6. Resume campaign
    print("\n6. Resuming campaign...")
    client.campaigns.pause(campaign["id"])  # Toggle
    print(f"   ✓ Campaign resumed")

    # 7. Stop campaign (pause permanently)
    print("\n7. Stopping campaign...")
    client.campaigns.pause(campaign["id"])
    print(f"   ✓ Campaign stopped")

    return campaign["id"]


def monitor_real_time_calls(client, campaign_id):
    """Monitor campaign calls in real-time"""

    print("\n=== Real-Time Call Monitoring ===")
    print("Monitoring calls for 30 seconds...")

    start_time = time.time()
    check_interval = 5  # Check every 5 seconds

    previous_call_count = 0

    while time.time() - start_time < 30:
        # Get current calls
        calls = client.calls.list(campaign_id=campaign_id, per_page=100)

        if len(calls) != previous_call_count:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] New activity detected!")
            print(f"  Total calls: {len(calls)}")

            # Show recent calls
            recent = sorted(calls, key=lambda x: x.get("created_at", ""), reverse=True)[:5]

            print("\n  Recent calls:")
            for call in recent:
                status = call.get("status", "unknown")
                to_phone = call.get("to_phone", "unknown")
                duration = call.get("duration", 0)

                print(f"    - {to_phone}: {status} ({duration}s)")

            previous_call_count = len(calls)

        time.sleep(check_interval)

    print("\n✓ Monitoring complete")


def get_campaign_analytics(client, campaign_id):
    """Get detailed campaign analytics"""

    print("\n=== Campaign Analytics ===")

    # Get campaign details
    campaign = client.campaigns.get(campaign_id)
    print(f"\nCampaign: {campaign['name']}")
    print(f"Created: {campaign.get('created_at', 'N/A')}")
    print(f"Status: {campaign['status']}")

    # Get all calls for this campaign
    all_calls = []
    page = 1

    while True:
        calls = client.calls.list(campaign_id=campaign_id, page=page, per_page=100)

        if not calls:
            break

        all_calls.extend(calls)
        page += 1

    print(f"\nTotal calls: {len(all_calls)}")

    if not all_calls:
        return

    # Calculate statistics
    statuses = {}
    total_duration = 0
    successful_calls = 0

    for call in all_calls:
        status = call.get("status", "unknown")
        statuses[status] = statuses.get(status, 0) + 1

        duration = call.get("duration", 0)
        total_duration += duration

        if status == "ended" and duration > 0:
            successful_calls += 1

    print("\nCall Status Breakdown:")
    for status, count in statuses.items():
        percentage = (count / len(all_calls)) * 100
        print(f"  {status}: {count} ({percentage:.1f}%)")

    print(f"\nDuration Statistics:")
    print(f"  Total duration: {total_duration} seconds ({total_duration / 60:.1f} minutes)")
    if successful_calls > 0:
        avg_duration = total_duration / successful_calls
        print(f"  Average successful call: {avg_duration:.1f} seconds")

    # Success rate
    if len(all_calls) > 0:
        success_rate = (successful_calls / len(all_calls)) * 100
        print(f"\nSuccess Rate: {success_rate:.1f}%")

    # Get call summary from API
    summary = client.calls.get_summary(campaign_id=campaign_id)
    print(f"\nAPI Summary:")
    print(f"  Total minutes: {summary.get('total_minutes', 0)}")


def bulk_campaign_operations(client):
    """Demonstrate bulk operations on campaigns"""

    print("\n=== Bulk Campaign Operations ===")

    # Get all ongoing campaigns
    ongoing = client.campaigns.list(status="ongoing", per_page=100)

    if not ongoing:
        print("No ongoing campaigns found.")
        return

    print(f"\nFound {len(ongoing)} ongoing campaigns")

    # Pause all ongoing campaigns
    print("\nPausing all ongoing campaigns...")
    paused_count = 0

    for campaign in ongoing:
        try:
            client.campaigns.pause(campaign["id"])
            paused_count += 1
            print(f"  ✓ Paused: {campaign['name']}")
        except Exception as e:
            print(f"  ✗ Failed to pause {campaign['name']}: {e}")

    print(f"\n✓ Paused {paused_count} campaigns")


def cleanup_old_campaigns(client, days_old=30):
    """Clean up old completed campaigns"""

    print(f"\n=== Cleaning Up Campaigns Older Than {days_old} Days ===")

    # Get all completed campaigns
    completed = client.campaigns.list(status="completed", per_page=100)

    if not completed:
        print("No completed campaigns found.")
        return

    cutoff_date = datetime.now() - timedelta(days=days_old)
    deleted_count = 0

    for campaign in completed:
        created_at = campaign.get("created_at", "")

        try:
            # Parse created date
            campaign_date = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

            if campaign_date < cutoff_date:
                # Delete old campaign
                client.campaigns.delete(campaign["id"])
                deleted_count += 1
                print(f"  ✓ Deleted: {campaign['name']} (created {created_at})")

        except Exception as e:
            print(f"  ✗ Failed to delete {campaign['name']}: {e}")

    print(f"\n✓ Deleted {deleted_count} old campaigns")


def main():
    # Initialize client
    print("Initializing Callbotics client...")
    client = CallboticsClient(API_URL, api_token=API_TOKEN)

    if not client.is_authenticated:
        print("Please provide a valid API token or use email/password login")
        return

    print(f"✓ Authenticated as {client.user_info.get('email', 'Unknown')}")

    # List all campaigns
    campaigns = list_all_campaigns(client)

    # Filter campaigns
    filter_campaigns(client)

    # Get campaign analytics for the first campaign
    if campaigns:
        get_campaign_analytics(client, campaigns[0]["id"])

    # Note: The following operations require actual agent_id and contact_list_id
    # Uncomment and provide valid IDs to test

    # agent_id = "your-agent-id"
    # contact_list_id = "your-contact-list-id"

    # # Full lifecycle management
    # campaign_id = manage_campaign_lifecycle(client, agent_id, contact_list_id)

    # # Real-time monitoring
    # monitor_real_time_calls(client, campaign_id)

    # # Bulk operations
    # bulk_campaign_operations(client)

    # # Cleanup (be careful with this!)
    # cleanup_old_campaigns(client, days_old=90)

    print("\n✓ Campaign management example completed!")


if __name__ == "__main__":
    main()
