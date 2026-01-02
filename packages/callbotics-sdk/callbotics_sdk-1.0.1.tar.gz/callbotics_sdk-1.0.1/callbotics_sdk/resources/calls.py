"""Call resource management"""
from typing import Dict, Any, List, Optional
from ..utils.helpers import make_request, validate_phone_number
from ..exceptions import ValidationError


class CallResource:
    """Individual call management"""

    def __init__(self, base_url: str, auth_headers: Dict[str, str]):
        self.base_url = base_url
        self.auth_headers = auth_headers

    def create(
        self,
        agent_id: str,
        to_number: str,
        from_number: Optional[str] = None,
        direction: str = "outbound",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create and initiate a single call

        Args:
            agent_id: Voice agent ID to use for this call
            to_number: Phone number to call
            from_number: Optional caller ID (if not specified, uses agent's default)
            direction: Call direction (inbound or outbound)
            metadata: Optional metadata for the call

        Returns:
            Created call details

        Example:
            call = client.calls.create(
                agent_id="65f1a2b3c4d5e6f7g8h9i0j1",
                to_number="+15551234567",
                from_number="+15559876543"
            )
        """
        if not agent_id:
            raise ValidationError("agent_id is required")

        # Validate and format phone number
        try:
            to_number = validate_phone_number(to_number)
            if from_number:
                from_number = validate_phone_number(from_number)
        except ValueError as e:
            raise ValidationError(str(e))

        payload = {
            "direction": direction,
            "to_number": to_number,
            "voice_agent_id": agent_id,
        }

        if from_number:
            payload["from_number"] = from_number

        if metadata:
            payload["metadata"] = metadata

        data = make_request(
            method="POST",
            url=f"{self.base_url}/v1/calls/create-call",
            headers=self.auth_headers,
            json=payload,
        )

        return data.get("data")

    def list(
        self,
        page: int = 1,
        per_page: int = 10,
        campaign_id: Optional[str] = None,
        status: Optional[str] = None,
        direction: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        List calls

        Args:
            page: Page number (1-indexed)
            per_page: Items per page
            campaign_id: Optional filter by campaign
            status: Optional filter by status (initiated, ongoing, ended, failed, etc.)
            direction: Optional filter by direction (inbound, outbound)

        Returns:
            List of calls
        """
        params = {
            "current_page": page,
            "per_page": per_page,
        }

        if campaign_id:
            params["campaign_id"] = campaign_id
        if status:
            params["status"] = status
        if direction:
            params["direction"] = direction

        data = make_request(
            method="GET",
            url=f"{self.base_url}/v1/calls",
            headers=self.auth_headers,
            params=params,
        )

        return data.get("data", [])

    def get(self, call_id: str) -> Dict[str, Any]:
        """
        Get specific call by ID

        Args:
            call_id: Call ID

        Returns:
            Call details including transcript, duration, etc.
        """
        data = make_request(
            method="GET",
            url=f"{self.base_url}/v1/calls/{call_id}",
            headers=self.auth_headers,
        )

        return data.get("data")

    def delete(self, call_id: str) -> Dict[str, Any]:
        """
        Delete call (soft delete)

        Args:
            call_id: Call ID

        Returns:
            Deletion confirmation
        """
        return make_request(
            method="DELETE",
            url=f"{self.base_url}/v1/calls/{call_id}",
            headers=self.auth_headers,
        )

    def get_summary(
        self,
        campaign_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get call minutes summary/analytics

        Args:
            campaign_id: Optional filter by campaign
            start_date: Optional start date (ISO format)
            end_date: Optional end date (ISO format)

        Returns:
            Call duration analytics
        """
        params = {}

        if campaign_id:
            params["campaign_id"] = campaign_id
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        data = make_request(
            method="GET",
            url=f"{self.base_url}/v1/calls/call-minutes-summary",
            headers=self.auth_headers,
            params=params,
        )

        return data.get("data")
