from dataclasses import dataclass, field

@dataclass
class PulsochatLanguageModelHandlerArguments:
    pulsochat_config_file: str = field(
        default="",
        metadata={
            "help": "The config_file for pulsochat"
        },
    )
    pulsochat_log_dir: str = field(
        default=".",
        metadata={
            "help": "Directory for logging conversations"
        },
    )
    pulsochat_api_key: str = field(
        default=None,
        metadata={
            "help": "A unique code used to authenticate and authorize access to an API."
        },
    )
    pulsochat_stream: bool = field(
        default=False,
        metadata={
            "help": "Indicates whether data should be transmitted in a continuous flow rather "
                    "than in a single, complete response. Default is False."
        },
    )
    pulsochat_enable_osc: bool = field(
        default=False,
        metadata={
            "help": "Activate OSC communication to restart the conversation and get updates on conversation status."
        },
    )
    pulsochat_osc_send_address: str = field(
        default="127.0.0.1",
        metadata={
            "help": "The address to send OSC messages to."
        },
    )
    pulsochat_osc_send_port: int = field(
        default=8000,
        metadata={
            "help": "The port that sends OSC messages."
        },
    )
    pulsochat_osc_receive_address: str = field(
        default="127.0.0.1",
        metadata={
            "help": "The address to receive OSC messages from."
        },
    )
    pulsochat_osc_receive_port: int = field(
        default=9000,
        metadata={
            "help": "The port that receives OSC messages."
        },
    )
