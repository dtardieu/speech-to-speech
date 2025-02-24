from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ModuleArguments:
    device: Optional[str] = field(
        default=None,
        metadata={"help": "If specified, overrides the device for all handlers."},
    )
    mode: Optional[str] = field(
        default="socket",
        metadata={
            "help": "The mode to run the pipeline in. Either 'local' or 'socket'. Default is 'socket'."
        },
    )
    local_mac_optimal_settings: bool = field(
        default=False,
        metadata={
            "help": "If specified, sets the optimal settings for Mac OS. Hence whisper-mlx, MLX LM and MeloTTS will be used."
        },
    )
    stt: Optional[str] = field(
        default="whisper",
        metadata={
            "help": "The STT to use. Either 'whisper', 'whisper-mlx', 'faster-whisper', and 'paraformer'. Default is 'whisper'."
        },
    )
    llm: Optional[str] = field(
        default="transformers",
        metadata={
            "help": "The LLM to use. Either 'transformers' or 'mlx-lm'. Default is 'transformers'"
        },
    )
    tts: Optional[str] = field(
        default="parler",
        metadata={
            "help": "The TTS to use. Either 'parler', 'melo', 'chatTTS' or 'facebookMMS'. Default is 'parler'"
        },
    )
    log_level: str = field(
        default="info",
        metadata={
            "help": "Provide logging level. Example --log_level debug, default=info."
        },
    )
    input_device: int = field(
        default=None,
        metadata={
            "help": "input audio device"
        },
    )
    input_channel: int = field(
        default=0,
        metadata={
            "help": "input audio channel"
        },
    )
    output_device: bool = field(
        default=None,
        metadata={
            "help": "output audio device"
        },
    )
    output_channel: bool = field(
        default=0,
        metadata={
            "help": "output audio channel"
        },
    )

    enable_osc: bool = field(
        default=False,
        metadata={
            "help": "Enable OSC communications"
        },
    )
    osc_send_address: str = field(
        default="127.0.0.1",
        metadata={
            "help": "The address to send OSC messages to."
        },
    )
    osc_send_port: int = field(
        default=8000,
        metadata={
            "help": "The port that sends OSC messages."
        },
    )
    osc_receive_address: str = field(
        default="127.0.0.1",
        metadata={
            "help": "The address to receive OSC messages from."
        },
    )
    osc_receive_port: int = field(
        default=9000,
        metadata={
            "help": "The port that receives OSC messages."
        },
    )
