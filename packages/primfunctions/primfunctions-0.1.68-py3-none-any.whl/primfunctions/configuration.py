import json
from enum import Enum
from typing import Mapping


class CustomVoice:
    def __init__(
        self,
        id: str,
        organization_id: str,
        name: str,
        provider: str,
        provider_id: str,
        language: str,
    ):
        self.id = id
        self.organization_id = organization_id
        self.name = name
        self.provider = provider
        self.provider_id = provider_id
        self.language = language

    def __dict__(self):
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "name": self.name,
            "provider": self.provider,
            "provider_id": self.provider_id,
            "language": self.language,
        }

    @classmethod
    def from_dict(cls, data):
        if isinstance(data, str):
            data = json.loads(data)
        return cls(
            id=data["id"],
            organization_id=data.get("organization_id", data.get("organizationId")),
            name=data["name"],
            provider=data["provider"],
            provider_id=data.get("provider_id", data.get("providerId")),
            language=data["language"],
        )


class LLMProvider(Enum):
    OPENAI = "openai"
    GEMINI = "gemini"


class Origin(Enum):
    DEBUGGER = "debugger"
    WEB = "web"
    PHONE = "phone"
    SIMULATION = "simulation"
    UNKNOWN = "unknown"


class Configuration:
    def __init__(
        self,
        input_type: str = "mic",
        origin: Origin = Origin.UNKNOWN,
        default_voice: str = "nova",
        custom_voices: Mapping[str, CustomVoice] = {},
        llm_provider: LLMProvider = LLMProvider.OPENAI,
        stt_model: str = "nova-3",
        stt_prompt: str = "",
        stt_endpointing: int = 300,
        stt_language: str = "en",
        module_rule: str = "default",
        recording_enabled: bool = False,
        recording_location: str = None,
        timeout: int = 5,
        audio_input_delay: int = 0,
        stt_noise_reduction_type: str = "near_field",
        stt_prewarm_model: str = "",
        stt_auto_switch: bool = False,
        stt_filter: str = None,
        eot_threshold: float = 0.8,
        eot_timeout_ms: int = 2500,
        eager_eot_threshold: float = None,
        vad_mode: str = "server_vad",
        vad_eagerness: str = "auto",
        error_fallback_type: str = "",
        error_fallback_value: str = "",
        error_fallback_timeout_seconds: int = 0,
        error_fallback_occurrence_threshold: int = 5,
        error_fallback_time_window_seconds: int = 300,
        startup_audio_url: str = None,
        startup_audio_interruptible: bool = False,
    ):
        self.input_type = input_type
        self.default_voice = default_voice
        self.custom_voices = {
            k: CustomVoice.from_dict(v) if isinstance(v, dict) else v
            for k, v in custom_voices.items()
        }
        self.stt_model = stt_model
        self.stt_prompt = stt_prompt
        self.stt_endpointing = stt_endpointing
        self.stt_language = stt_language
        self.module_rule = module_rule
        self.recording_enabled = recording_enabled
        self.recording_location = recording_location
        self.timeout = timeout
        self.audio_input_delay = audio_input_delay
        self.stt_noise_reduction_type = stt_noise_reduction_type
        self.stt_prewarm_model = stt_prewarm_model
        self.stt_auto_switch = stt_auto_switch
        self.stt_filter = stt_filter
        self.eot_threshold = eot_threshold
        self.eot_timeout_ms = eot_timeout_ms
        self.eager_eot_threshold = eager_eot_threshold
        self.vad_mode = vad_mode
        self.vad_eagerness = vad_eagerness
        self.error_fallback_type = error_fallback_type
        self.error_fallback_value = error_fallback_value
        self.error_fallback_timeout_seconds = error_fallback_timeout_seconds
        self.error_fallback_occurrence_threshold = error_fallback_occurrence_threshold
        self.error_fallback_time_window_seconds = error_fallback_time_window_seconds
        self.startup_audio_url = startup_audio_url
        self.startup_audio_interruptible = startup_audio_interruptible

        if isinstance(llm_provider, str):
            self.llm_provider = LLMProvider(llm_provider)
        else:
            self.llm_provider = llm_provider

        if isinstance(origin, str):
            self.origin = Origin(origin)
        else:
            self.origin = origin

    def set_llm_provider(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider

    def __dict__(self):
        return {
            "input_type": self.input_type,
            "origin": self.origin.value,
            "default_voice": self.default_voice,
            "custom_voices": {k: v.__dict__() for k, v in self.custom_voices.items()},
            "llm_provider": self.llm_provider.value,
            "stt_model": self.stt_model,
            "stt_prompt": self.stt_prompt,
            "stt_endpointing": self.stt_endpointing,
            "stt_language": self.stt_language,
            "module_rule": self.module_rule,
            "recording_enabled": self.recording_enabled,
            "recording_location": self.recording_location,
            "timeout": self.timeout,
            "audio_input_delay": self.audio_input_delay,
            "stt_noise_reduction_type": self.stt_noise_reduction_type,
            "stt_prewarm_model": self.stt_prewarm_model,
            "stt_auto_switch": self.stt_auto_switch,
            "stt_filter": self.stt_filter,
            "eot_threshold": self.eot_threshold,
            "eot_timeout_ms": self.eot_timeout_ms,
            "eager_eot_threshold": self.eager_eot_threshold,
            "vad_mode": self.vad_mode,
            "vad_eagerness": self.vad_eagerness,
            "error_fallback_type": self.error_fallback_type,
            "error_fallback_value": self.error_fallback_value,
            "error_fallback_timeout_seconds": self.error_fallback_timeout_seconds,
            "error_fallback_occurrence_threshold": self.error_fallback_occurrence_threshold,
            "error_fallback_time_window_seconds": self.error_fallback_time_window_seconds,
            "startup_audio_url": self.startup_audio_url,
            "startup_audio_interruptible": self.startup_audio_interruptible,
        }
