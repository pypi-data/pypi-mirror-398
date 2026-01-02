"""Campaign resource management"""
from typing import Dict, Any, List, Optional
from ..utils.helpers import make_request
from ..exceptions import ValidationError


class CampaignResource:
    """Campaign management for organizing voice bot calls"""

    def __init__(self, base_url: str, auth_headers: Dict[str, str]):
        self.base_url = base_url
        self.auth_headers = auth_headers

    def create(
        self,
        name: str,
        agent_id: str,
        direction: str = "outbound",
        description: Optional[str] = None,
        concurrency: int = 2,
        to_phone: Optional[str] = None,
        from_phone: Optional[str] = None,
        initial_message: Optional[str] = None,
        recording: bool = False,
        webhook_url: Optional[str] = None,
        live_transfer: str = "None",
        live_transfer_number: Optional[str] = None,
        auto_hangup_ivr: bool = False,
        auto_hangup_wait_time: int = 15,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a campaign

        Args:
            name: Campaign name
            agent_id: Voice agent ID to use for this campaign
            direction: Call direction (inbound or outbound)
            description: Optional campaign description
            concurrency: Maximum simultaneous calls (default: 2)
            to_phone: Phone number to call (for inbound campaigns)
            from_phone: Caller ID to display
            initial_message: Optional initial message from bot
            recording: Enable call recording
            webhook_url: Optional webhook URL for call events
            live_transfer: Transfer type (None, Blind, or Warm)
            live_transfer_number: Number to transfer to (if live_transfer enabled)
            auto_hangup_ivr: Automatically hang up on IVR detection
            auto_hangup_wait_time: Seconds to wait before auto-hangup
            **kwargs: Additional campaign parameters

        Returns:
            Created campaign

        Example:
            campaign = client.campaigns.create(
                name="Customer Outreach Q1",
                agent_id="65f1a2b3c4d5e6f7g8h9i0j1",
                direction="outbound",
                concurrency=5,
                from_phone="+15551234567",
                recording=True,
                initial_message="Hi, this is Sarah from Acme Corp."
            )
        """
        if not agent_id:
            raise ValidationError("agent_id is required")

        if direction not in ["inbound", "outbound"]:
            raise ValidationError("direction must be 'inbound' or 'outbound'")

        payload = {
            "name": name,
            "agent": agent_id,
            "direction": direction,
            "concurrency": concurrency,
            "recording": recording,
            "live_transfer": live_transfer,
            "auto_hangup_ivr": auto_hangup_ivr,
            "auto_hangup_wait_time": auto_hangup_wait_time,
        }

        if description:
            payload["description"] = description
        if to_phone:
            payload["to_phone"] = to_phone
        if from_phone:
            payload["display_number"] = from_phone
        if initial_message:
            payload["initial_message"] = initial_message
        if webhook_url:
            payload["webhook_url"] = webhook_url
        if live_transfer != "None" and live_transfer_number:
            payload["live_transfer_number"] = live_transfer_number

        # Add any additional parameters
        payload.update(kwargs)

        data = make_request(
            method="POST",
            url=f"{self.base_url}/v1/campaigns",
            headers=self.auth_headers,
            json=payload,
        )

        return data.get("data")

    def list(
        self,
        page: int = 1,
        per_page: int = 10,
        name: Optional[str] = None,
        status: Optional[str] = None,
        direction: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        List campaigns

        Args:
            page: Page number (1-indexed)
            per_page: Items per page
            name: Optional filter by name
            status: Optional filter by status (not_started, ongoing, paused, completed)
            direction: Optional filter by direction (inbound, outbound)

        Returns:
            List of campaigns
        """
        params = {
            "current_page": page,
            "per_page": per_page,
        }

        if name:
            params["name"] = name
        if status:
            params["status"] = status
        if direction:
            params["direction"] = direction

        data = make_request(
            method="GET",
            url=f"{self.base_url}/v1/campaigns",
            headers=self.auth_headers,
            params=params,
        )

        return data.get("data", [])

    def get(self, campaign_id: str) -> Dict[str, Any]:
        """
        Get specific campaign by ID

        Args:
            campaign_id: Campaign ID

        Returns:
            Campaign details
        """
        data = make_request(
            method="GET",
            url=f"{self.base_url}/v1/campaigns/{campaign_id}",
            headers=self.auth_headers,
        )

        return data.get("data")

    def update(self, campaign_id: str, **update_fields) -> Dict[str, Any]:
        """
        Update campaign

        Args:
            campaign_id: Campaign ID
            **update_fields: Fields to update (name, description, concurrency, etc.)

        Returns:
            Updated campaign
        """
        data = make_request(
            method="PUT",
            url=f"{self.base_url}/v1/campaigns/{campaign_id}",
            headers=self.auth_headers,
            json=update_fields,
        )

        return data.get("data")

    def delete(self, campaign_id: str) -> Dict[str, Any]:
        """
        Delete campaign (soft delete)

        Args:
            campaign_id: Campaign ID

        Returns:
            Deletion confirmation
        """
        return make_request(
            method="DELETE",
            url=f"{self.base_url}/v1/campaigns/{campaign_id}",
            headers=self.auth_headers,
        )

    def start(self, campaign_id: str, contact_list_id: str, contact_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Start a campaign with a contact list

        Args:
            campaign_id: Campaign ID
            contact_list_id: Contact list ID to use
            contact_ids: Optional specific contact IDs to call (if None, all contacts in list)

        Returns:
            Campaign start confirmation

        Example:
            # Start campaign with all contacts in list
            client.campaigns.start(
                campaign_id="65f1a2b3c4d5e6f7g8h9i0j1",
                contact_list_id="65f1a2b3c4d5e6f7g8h9i0j2"
            )

            # Start campaign with specific contacts
            client.campaigns.start(
                campaign_id="65f1a2b3c4d5e6f7g8h9i0j1",
                contact_list_id="65f1a2b3c4d5e6f7g8h9i0j2",
                contact_ids=["65f1...", "65f2..."]
            )
        """
        payload = {"contact_list_id": contact_list_id}

        if contact_ids:
            payload["contact_ids"] = contact_ids

        data = make_request(
            method="POST",
            url=f"{self.base_url}/v1/campaigns/start/{campaign_id}",
            headers=self.auth_headers,
            json=payload,
        )

        return data.get("data")

    def pause(self, campaign_id: str) -> Dict[str, Any]:
        """
        Pause/unpause a campaign

        Args:
            campaign_id: Campaign ID

        Returns:
            Campaign status update
        """
        data = make_request(
            method="POST",
            url=f"{self.base_url}/v1/campaigns/pause/{campaign_id}",
            headers=self.auth_headers,
        )

        return data.get("data")

    def get_available_concurrency(self) -> Dict[str, Any]:
        """
        Check available concurrency for starting campaigns

        Returns:
            Available concurrency information
        """
        data = make_request(
            method="GET",
            url=f"{self.base_url}/v1/campaigns/available_concurrency",
            headers=self.auth_headers,
        )

        return data.get("data")
