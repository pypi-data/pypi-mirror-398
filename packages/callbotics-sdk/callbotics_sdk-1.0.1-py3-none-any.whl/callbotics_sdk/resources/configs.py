"""Configuration builders for voice agents"""
from typing import Dict, Any, Optional, List
from ..utils.helpers import make_request


class ConfigResource:
    """Base class for configuration resources"""

    def __init__(self, base_url: str, auth_headers: Dict[str, str]):
        self.base_url = base_url
        self.auth_headers = auth_headers


class LLMConfig(ConfigResource):
    """LLM (Language Model) configuration management"""

    def create(
        self,
        name: str,
        llm_type: str,
        model: str,
        temperature: float = 0.7,
        api_key: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create LLM configuration

        Args:
            name: Display name for this configuration
            llm_type: Type of LLM (agent_chat_gpt, agent_anthropic, agent_groq, agent_azure_open_ai)
            model: Model identifier (e.g., gpt-4, claude-3-opus-20240229)
            temperature: Model temperature (0.0 - 1.0)
            api_key: Optional API key (if not using default)
            **kwargs: Additional LLM-specific configuration

        Returns:
            Created LLM configuration
        """
        llm_config = {
            "model": model,
            "temperature": temperature,
            **kwargs,
        }

        if api_key:
            llm_config["api_key"] = api_key

        data = make_request(
            method="POST",
            url=f"{self.base_url}/v1/llm/config",
            headers=self.auth_headers,
            json={
                "placeholder_name": name,
                "llm_type": llm_type,
                "llm_config": llm_config,
            },
        )

        return data.get("data")

    def list(self, page: int = 1, per_page: int = 10) -> List[Dict[str, Any]]:
        """List all LLM configurations"""
        data = make_request(
            method="GET",
            url=f"{self.base_url}/v1/llm/config",
            headers=self.auth_headers,
            params={"current_page": page, "per_page": per_page},
        )
        return data.get("data", [])

    def get(self, config_id: str) -> Dict[str, Any]:
        """Get specific LLM configuration"""
        data = make_request(
            method="GET",
            url=f"{self.base_url}/v1/llm/config/{config_id}",
            headers=self.auth_headers,
        )
        return data.get("data")

    def delete(self, config_id: str) -> Dict[str, Any]:
        """Delete LLM configuration"""
        return make_request(
            method="DELETE",
            url=f"{self.base_url}/v1/llm/config/{config_id}",
            headers=self.auth_headers,
        )


class VoiceConfig(ConfigResource):
    """Voice/Synthesizer configuration management"""

    def create(
        self,
        name: str,
        voice_type: str,
        gender: str = "female",
        accent: str = "american",
        **config_params,
    ) -> Dict[str, Any]:
        """
        Create voice configuration

        Args:
            name: Display name for this configuration
            voice_type: Voice provider (rime, eleven_labs, deepgram, play_ht, cb)
            gender: Voice gender (male, female)
            accent: Voice accent (american, british, etc.)
            **config_params: Provider-specific configuration

        Returns:
            Created voice configuration

        Examples:
            # Rime voice
            voice_config.create(
                name="Rime Fast Voice",
                voice_type="rime",
                api_key="your_key",
                speaker="wildflower",
                model_id="mistv2",
                speed_alpha=1.2,
                reduce_latency=True
            )

            # ElevenLabs voice
            voice_config.create(
                name="ElevenLabs Natural",
                voice_type="eleven_labs",
                api_key="your_key",
                voice_id="21m00Tcm4TlvDq8ikWAM",
                stability=0.5,
                similarity_boost=0.75
            )
        """
        data = make_request(
            method="POST",
            url=f"{self.base_url}/v1/voice-configs",
            headers=self.auth_headers,
            json={
                "placeholder_name": name,
                "voice_type": voice_type,
                "gender": gender,
                "accent": accent,
                "voice_config": config_params,
            },
        )

        return data.get("data")

    def create_rime(
        self,
        name: str,
        api_key: str,
        speaker: str = "wildflower",
        model_id: str = "mistv2",
        speed_alpha: float = 1.2,
        reduce_latency: bool = True,
        sampling_rate: int = 22050,
        gender: str = "female",
        accent: str = "american",
    ) -> Dict[str, Any]:
        """
        Create Rime voice configuration with sensible defaults

        Args:
            name: Display name
            api_key: Rime API key
            speaker: Speaker voice name
            model_id: Model version (mistv2, mist, v1)
            speed_alpha: Speech speed multiplier
            reduce_latency: Enable low-latency mode
            sampling_rate: Audio sampling rate
            gender: Voice gender
            accent: Voice accent

        Returns:
            Created voice configuration
        """
        return self.create(
            name=name,
            voice_type="rime",
            gender=gender,
            accent=accent,
            base_url="https://users.rime.ai/v1/rime-tts",
            api_key=api_key,
            model_id=model_id,
            speaker=speaker,
            speed_alpha=speed_alpha,
            sampling_rate=sampling_rate,
            reduce_latency=reduce_latency,
            pause_between_brackets=True,
            phonemize_between_brackets=True,
            lang="eng",
        )

    def list(self, page: int = 1, per_page: int = 10) -> List[Dict[str, Any]]:
        """List all voice configurations"""
        data = make_request(
            method="GET",
            url=f"{self.base_url}/v1/voice-configs",
            headers=self.auth_headers,
            params={"current_page": page, "per_page": per_page},
        )
        return data.get("data", [])

    def get(self, config_id: str) -> Dict[str, Any]:
        """Get specific voice configuration"""
        data = make_request(
            method="GET",
            url=f"{self.base_url}/v1/voice-configs/{config_id}",
            headers=self.auth_headers,
        )
        return data.get("data")

    def delete(self, config_id: str) -> Dict[str, Any]:
        """Delete voice configuration"""
        return make_request(
            method="DELETE",
            url=f"{self.base_url}/v1/voice-configs/{config_id}",
            headers=self.auth_headers,
        )


class TranscriberConfig(ConfigResource):
    """Speech-to-Text configuration management"""

    def create(
        self, name: str, transcriber_type: str = "deepgram", **config_params
    ) -> Dict[str, Any]:
        """
        Create transcriber/STT configuration

        Args:
            name: Display name for this configuration
            transcriber_type: Transcriber provider (deepgram, cb, custom)
            **config_params: Provider-specific configuration

        Returns:
            Created transcriber configuration

        Examples:
            # Deepgram transcriber
            transcriber_config.create(
                name="Deepgram Phone",
                transcriber_type="deepgram",
                api_key="your_key",
                language="en-US",
                model="nova-2-phonecall",
                tier="nova"
            )
        """
        data = make_request(
            method="POST",
            url=f"{self.base_url}/v1/stt",
            headers=self.auth_headers,
            json={
                "placeholder_name": name,
                "transcriber_type": transcriber_type,
                "transcriber_config": config_params,
            },
        )

        return data.get("data")

    def create_deepgram(
        self,
        name: str,
        api_key: str,
        language: str = "en-US",
        model: str = "nova-2-phonecall",
        tier: str = "nova",
    ) -> Dict[str, Any]:
        """
        Create Deepgram transcriber configuration with sensible defaults

        Args:
            name: Display name
            api_key: Deepgram API key
            language: Language code
            model: Deepgram model name
            tier: Model tier

        Returns:
            Created transcriber configuration
        """
        return self.create(
            name=name,
            transcriber_type="deepgram",
            api_key=api_key,
            language=language,
            model=model,
            tier=tier,
            sampling_rate=8000,
            audio_encoding="mulaw",
            chunk_size=20,
            endpointing_config={
                "type": "endpointing_punctuation_based",
                "time_cutoff_seconds": 0.6,
            },
        )

    def list(self, page: int = 1, per_page: int = 10) -> List[Dict[str, Any]]:
        """List all transcriber configurations"""
        data = make_request(
            method="GET",
            url=f"{self.base_url}/v1/stt",
            headers=self.auth_headers,
            params={"current_page": page, "per_page": per_page},
        )
        return data.get("data", [])

    def get(self, config_id: str) -> Dict[str, Any]:
        """Get specific transcriber configuration"""
        data = make_request(
            method="GET",
            url=f"{self.base_url}/v1/stt/{config_id}",
            headers=self.auth_headers,
        )
        return data.get("data")

    def delete(self, config_id: str) -> Dict[str, Any]:
        """Delete transcriber configuration"""
        return make_request(
            method="DELETE",
            url=f"{self.base_url}/v1/stt/{config_id}",
            headers=self.auth_headers,
        )


class TelephonyConfig(ConfigResource):
    """Telephony provider configuration management"""

    def create(
        self, name: str, telephony_name: str, contact_email: Optional[str] = None, **config_params
    ) -> Dict[str, Any]:
        """
        Create telephony configuration

        Args:
            name: Display name for this configuration
            telephony_name: Provider name (telnyx, twilio)
            contact_email: Optional contact email
            **config_params: Provider-specific configuration

        Returns:
            Created telephony configuration

        Examples:
            # Telnyx configuration
            telephony_config.create(
                name="Telnyx Production",
                telephony_name="telnyx",
                auth_token="your_token",
                connection_id="your_connection_id"
            )

            # Twilio configuration
            telephony_config.create(
                name="Twilio Production",
                telephony_name="twilio",
                account_sid="your_account_sid",
                auth_token="your_auth_token"
            )
        """
        data = make_request(
            method="POST",
            url=f"{self.base_url}/v1/telephony",
            headers=self.auth_headers,
            json={
                "placeholder_name": name,
                "telephony_name": telephony_name,
                "contact_email": contact_email,
                "telephony_config": config_params,
            },
        )

        return data.get("data")

    def create_telnyx(
        self, name: str, auth_token: str, connection_id: str, from_number: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create Telnyx telephony configuration

        Args:
            name: Display name
            auth_token: Telnyx API auth token
            connection_id: Telnyx connection ID
            from_number: Optional default caller ID

        Returns:
            Created telephony configuration
        """
        config = {
            "auth_token": auth_token,
            "connection_id": connection_id,
        }

        if from_number:
            config["from_number"] = from_number

        return self.create(name=name, telephony_name="telnyx", **config)

    def list(self, page: int = 1, per_page: int = 10) -> List[Dict[str, Any]]:
        """List all telephony configurations"""
        data = make_request(
            method="GET",
            url=f"{self.base_url}/v1/telephony",
            headers=self.auth_headers,
            params={"current_page": page, "per_page": per_page},
        )
        return data.get("data", [])

    def get(self, config_id: str) -> Dict[str, Any]:
        """Get specific telephony configuration"""
        data = make_request(
            method="GET",
            url=f"{self.base_url}/v1/telephony/{config_id}",
            headers=self.auth_headers,
        )
        return data.get("data")

    def delete(self, config_id: str) -> Dict[str, Any]:
        """Delete telephony configuration"""
        return make_request(
            method="DELETE",
            url=f"{self.base_url}/v1/telephony/{config_id}",
            headers=self.auth_headers,
        )


class PromptConfig(ConfigResource):
    """Prompt configuration management"""

    def create(
        self,
        name: str,
        background: str = "",
        business_logic: str = "",
        conversational_tips: str = "",
        prompt_variables: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create prompt configuration

        Args:
            name: Display name for this configuration
            background: Agent persona and background
            business_logic: Business rules and logic
            conversational_tips: How the agent should communicate
            prompt_variables: Dynamic variables for the prompt

        Returns:
            Created prompt configuration

        Example:
            prompt_config.create(
                name="Sales Assistant",
                background="You are a friendly sales assistant for Acme Corp",
                business_logic="Always confirm customer details before proceeding",
                conversational_tips="Be warm, professional, and empathetic"
            )
        """
        data = make_request(
            method="POST",
            url=f"{self.base_url}/v1/prompt",
            headers=self.auth_headers,
            json={
                "placeholder_name": name,
                "background": background,
                "business_logic": business_logic,
                "conversational_tips": conversational_tips,
                "prompt_variables": prompt_variables or {},
            },
        )

        return data.get("data")

    def list(self, page: int = 1, per_page: int = 10) -> List[Dict[str, Any]]:
        """List all prompt configurations"""
        data = make_request(
            method="GET",
            url=f"{self.base_url}/v1/prompt",
            headers=self.auth_headers,
            params={"current_page": page, "per_page": per_page},
        )
        return data.get("data", [])

    def get(self, config_id: str) -> Dict[str, Any]:
        """Get specific prompt configuration"""
        data = make_request(
            method="GET",
            url=f"{self.base_url}/v1/prompt/{config_id}",
            headers=self.auth_headers,
        )
        return data.get("data")

    def update(
        self,
        config_id: str,
        name: Optional[str] = None,
        background: Optional[str] = None,
        business_logic: Optional[str] = None,
        conversational_tips: Optional[str] = None,
        prompt_variables: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Update prompt configuration"""
        update_data = {}

        if name is not None:
            update_data["placeholder_name"] = name
        if background is not None:
            update_data["background"] = background
        if business_logic is not None:
            update_data["business_logic"] = business_logic
        if conversational_tips is not None:
            update_data["conversational_tips"] = conversational_tips
        if prompt_variables is not None:
            update_data["prompt_variables"] = prompt_variables

        data = make_request(
            method="PUT",
            url=f"{self.base_url}/v1/prompt/{config_id}",
            headers=self.auth_headers,
            json=update_data,
        )

        return data.get("data")

    def delete(self, config_id: str) -> Dict[str, Any]:
        """Delete prompt configuration"""
        return make_request(
            method="DELETE",
            url=f"{self.base_url}/v1/prompt/{config_id}",
            headers=self.auth_headers,
        )
