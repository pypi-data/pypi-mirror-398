"""Resource modules for Callbotics SDK"""
from .agents import AgentResource
from .campaigns import CampaignResource
from .calls import CallResource
from .configs import (
    LLMConfig,
    VoiceConfig,
    TranscriberConfig,
    TelephonyConfig,
    PromptConfig,
)

__all__ = [
    "AgentResource",
    "CampaignResource",
    "CallResource",
    "LLMConfig",
    "VoiceConfig",
    "TranscriberConfig",
    "TelephonyConfig",
    "PromptConfig",
]
