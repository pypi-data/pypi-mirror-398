"""Main Callbotics SDK client"""
from typing import Optional
from .auth import AuthHandler
from .resources import (
    AgentResource,
    CampaignResource,
    CallResource,
    LLMConfig,
    VoiceConfig,
    TranscriberConfig,
    TelephonyConfig,
    PromptConfig,
)
from .exceptions import AuthenticationError


class CallboticsClient:
    """
    Main client for interacting with Callbotics Voice AI Platform

    Examples:
        # Initialize with default base URL (https://api.callbotics.ai)
        client = CallboticsClient()
        client.login("user@example.com", "password")

        # Initialize with custom base URL
        client = CallboticsClient("https://custom.api.url")
        client.login("user@example.com", "password")

        # Initialize with existing token
        client = CallboticsClient(api_token="your-jwt-token")

        # Create a bot
        agent = client.agents.create(
            name="Customer Support Bot",
            llm_config_id="...",
            prompt_config_id="...",
            voice_config_id="...",
            transcriber_config_id="...",
            telephony_config_id="..."
        )

        # Create a campaign
        campaign = client.campaigns.create(
            name="Q1 Outreach",
            agent_id=agent["id"],
            direction="outbound",
            concurrency=5
        )

        # Make a call
        call = client.calls.create(
            agent_id=agent["id"],
            to_number="+15551234567"
        )
    """

    def __init__(self, base_url: str = "https://api.callbotics.ai", api_token: Optional[str] = None):
        """
        Initialize Callbotics client

        Args:
            base_url: Base URL of Callbotics API (default: https://api.callbotics.ai)
            api_token: Optional pre-authenticated JWT token
        """
        self.base_url = base_url.rstrip("/")
        self._auth = AuthHandler(self.base_url, api_token)

        # Initialize resource managers
        self._initialize_resources()

    def _initialize_resources(self):
        """Initialize all resource managers with current auth"""
        auth_headers = self._get_auth_headers()

        # Configuration resources
        self.llm_configs = LLMConfig(self.base_url, auth_headers)
        self.voice_configs = VoiceConfig(self.base_url, auth_headers)
        self.transcriber_configs = TranscriberConfig(self.base_url, auth_headers)
        self.telephony_configs = TelephonyConfig(self.base_url, auth_headers)
        self.prompt_configs = PromptConfig(self.base_url, auth_headers)

        # Main resources
        self.agents = AgentResource(self.base_url, auth_headers)
        self.campaigns = CampaignResource(self.base_url, auth_headers)
        self.calls = CallResource(self.base_url, auth_headers)

    def _get_auth_headers(self):
        """Get current auth headers (or empty dict if not authenticated)"""
        try:
            return self._auth.get_auth_headers()
        except AuthenticationError:
            return {}

    def login(self, email: str, password: str) -> str:
        """
        Authenticate with email and password

        Args:
            email: User email
            password: User password

        Returns:
            JWT access token

        Raises:
            AuthenticationError: If authentication fails
        """
        token = self._auth.login(email, password)
        # Reinitialize resources with new auth
        self._initialize_resources()
        return token

    def set_token(self, token: str):
        """
        Manually set authentication token

        Args:
            token: JWT access token
        """
        self._auth.set_token(token)
        # Reinitialize resources with new auth
        self._initialize_resources()

    @property
    def is_authenticated(self) -> bool:
        """Check if client is authenticated"""
        return self._auth.is_authenticated

    @property
    def user_info(self):
        """Get current user information"""
        return self._auth.user_info

    def create_complete_bot(
        self,
        name: str,
        # LLM configuration
        llm_type: str = "agent_chat_gpt",
        llm_model: str = "gpt-4",
        llm_temperature: float = 0.7,
        llm_api_key: Optional[str] = None,
        # Prompt configuration
        prompt_background: str = "",
        prompt_business_logic: str = "",
        prompt_conversational_tips: str = "",
        # Voice configuration (Rime defaults)
        voice_api_key: Optional[str] = None,
        voice_speaker: str = "wildflower",
        voice_speed: float = 1.2,
        # Transcriber configuration (Deepgram defaults)
        transcriber_api_key: Optional[str] = None,
        transcriber_language: str = "en-US",
        # Telephony configuration (Telnyx)
        telephony_provider: str = "telnyx",
        telephony_auth_token: Optional[str] = None,
        telephony_connection_id: Optional[str] = None,
    ):
        """
        Convenience method to create a complete bot with all configurations

        This creates all necessary configurations and the agent in one call.

        Args:
            name: Bot name
            llm_type: LLM provider type
            llm_model: LLM model name
            llm_temperature: Model temperature
            llm_api_key: Optional LLM API key
            prompt_background: Agent persona/background
            prompt_business_logic: Business rules
            prompt_conversational_tips: How agent should talk
            voice_api_key: Voice provider API key
            voice_speaker: Voice speaker name
            voice_speed: Speech speed multiplier
            transcriber_api_key: Transcriber API key
            transcriber_language: Language code
            telephony_provider: Telephony provider (telnyx or twilio)
            telephony_auth_token: Telephony auth token
            telephony_connection_id: Telephony connection ID

        Returns:
            Dictionary with all created resources:
            {
                "agent": {...},
                "configs": {
                    "llm": {...},
                    "voice": {...},
                    "transcriber": {...},
                    "telephony": {...},
                    "prompt": {...}
                }
            }

        Example:
            bot = client.create_complete_bot(
                name="Support Bot",
                llm_api_key="sk-...",
                prompt_background="You are a helpful support agent",
                voice_api_key="rime_...",
                transcriber_api_key="dg_...",
                telephony_auth_token="telnyx_...",
                telephony_connection_id="..."
            )

            print(f"Bot created: {bot['agent']['id']}")
        """
        print(f"Creating complete bot configuration for '{name}'...")

        # Create LLM config
        print("  - Creating LLM configuration...")
        llm_config = self.llm_configs.create(
            name=f"{name} - LLM",
            llm_type=llm_type,
            model=llm_model,
            temperature=llm_temperature,
            api_key=llm_api_key,
        )

        # Create prompt config
        print("  - Creating prompt configuration...")
        prompt_config = self.prompt_configs.create(
            name=f"{name} - Prompt",
            background=prompt_background,
            business_logic=prompt_business_logic,
            conversational_tips=prompt_conversational_tips,
        )

        # Create voice config (Rime)
        print("  - Creating voice configuration...")
        voice_config = self.voice_configs.create_rime(
            name=f"{name} - Voice",
            api_key=voice_api_key or "",
            speaker=voice_speaker,
            speed_alpha=voice_speed,
        )

        # Create transcriber config (Deepgram)
        print("  - Creating transcriber configuration...")
        transcriber_config = self.transcriber_configs.create_deepgram(
            name=f"{name} - Transcriber",
            api_key=transcriber_api_key or "",
            language=transcriber_language,
        )

        # Create telephony config
        print("  - Creating telephony configuration...")
        if telephony_provider == "telnyx":
            telephony_config = self.telephony_configs.create_telnyx(
                name=f"{name} - Telephony",
                auth_token=telephony_auth_token or "",
                connection_id=telephony_connection_id or "",
            )
        else:
            raise ValueError(f"Unsupported telephony provider: {telephony_provider}")

        # Create agent
        print("  - Creating agent...")
        agent = self.agents.create(
            name=name,
            llm_config_id=llm_config["id"],
            prompt_config_id=prompt_config["id"],
            voice_config_id=voice_config["id"],
            transcriber_config_id=transcriber_config["id"],
            telephony_config_id=telephony_config["id"],
        )

        print(f"✓ Bot '{name}' created successfully! Agent ID: {agent['id']}")

        return {
            "agent": agent,
            "configs": {
                "llm": llm_config,
                "voice": voice_config,
                "transcriber": transcriber_config,
                "telephony": telephony_config,
                "prompt": prompt_config,
            },
        }
