"""Agent/Bot resource management"""
from typing import Dict, Any, List, Optional
from ..utils.helpers import make_request
from ..exceptions import ValidationError


class AgentResource:
    """Voice agent/bot management"""

    def __init__(self, base_url: str, auth_headers: Dict[str, str]):
        self.base_url = base_url
        self.auth_headers = auth_headers

    def create(
        self,
        name: str,
        llm_config_id: str,
        prompt_config_id: str,
        voice_config_id: str,
        transcriber_config_id: str,
        telephony_config_id: str,
        report_config_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a voice agent

        Args:
            name: Agent name
            llm_config_id: LLM configuration ID
            prompt_config_id: Prompt configuration ID
            voice_config_id: Voice/synthesizer configuration ID
            transcriber_config_id: Transcriber/STT configuration ID
            telephony_config_id: Telephony configuration ID
            report_config_id: Optional report configuration ID

        Returns:
            Created agent

        Raises:
            ValidationError: If required configurations are missing
        """
        if not all([llm_config_id, prompt_config_id, voice_config_id, transcriber_config_id, telephony_config_id]):
            raise ValidationError("All configuration IDs are required to create an agent")

        payload = {
            "name": name,
            "llm": llm_config_id,
            "prompt": prompt_config_id,
            "synthesizer": voice_config_id,
            "transcriber": transcriber_config_id,
            "telephony": telephony_config_id,
        }

        if report_config_id:
            payload["report"] = report_config_id

        data = make_request(
            method="POST",
            url=f"{self.base_url}/v1/agents",
            headers=self.auth_headers,
            json=payload,
        )

        return data.get("data")

    def list(
        self,
        page: int = 1,
        per_page: int = 10,
        name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        List agents

        Args:
            page: Page number (1-indexed)
            per_page: Items per page
            name: Optional filter by name (regex search)

        Returns:
            List of agents
        """
        params = {
            "current_page": page,
            "per_page": per_page,
        }

        if name:
            params["name"] = name

        data = make_request(
            method="GET",
            url=f"{self.base_url}/v1/agents",
            headers=self.auth_headers,
            params=params,
        )

        return data.get("data", [])

    def get(self, agent_id: str) -> Dict[str, Any]:
        """
        Get specific agent by ID

        Args:
            agent_id: Agent ID

        Returns:
            Agent details
        """
        data = make_request(
            method="GET",
            url=f"{self.base_url}/v1/agents/{agent_id}",
            headers=self.auth_headers,
        )

        return data.get("data")

    def update(
        self,
        agent_id: str,
        name: Optional[str] = None,
        llm_config_id: Optional[str] = None,
        prompt_config_id: Optional[str] = None,
        voice_config_id: Optional[str] = None,
        transcriber_config_id: Optional[str] = None,
        telephony_config_id: Optional[str] = None,
        report_config_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update agent configuration

        Args:
            agent_id: Agent ID
            name: Optional new name
            llm_config_id: Optional new LLM configuration ID
            prompt_config_id: Optional new prompt configuration ID
            voice_config_id: Optional new voice configuration ID
            transcriber_config_id: Optional new transcriber configuration ID
            telephony_config_id: Optional new telephony configuration ID
            report_config_id: Optional new report configuration ID

        Returns:
            Updated agent
        """
        update_data = {}

        if name is not None:
            update_data["name"] = name
        if llm_config_id is not None:
            update_data["llm"] = llm_config_id
        if prompt_config_id is not None:
            update_data["prompt"] = prompt_config_id
        if voice_config_id is not None:
            update_data["synthesizer"] = voice_config_id
        if transcriber_config_id is not None:
            update_data["transcriber"] = transcriber_config_id
        if telephony_config_id is not None:
            update_data["telephony"] = telephony_config_id
        if report_config_id is not None:
            update_data["report"] = report_config_id

        data = make_request(
            method="PUT",
            url=f"{self.base_url}/v1/agents/{agent_id}",
            headers=self.auth_headers,
            json=update_data,
        )

        return data.get("data")

    def delete(self, agent_id: str) -> Dict[str, Any]:
        """
        Delete agent (soft delete)

        Args:
            agent_id: Agent ID

        Returns:
            Deletion confirmation
        """
        return make_request(
            method="DELETE",
            url=f"{self.base_url}/v1/agents/{agent_id}",
            headers=self.auth_headers,
        )
