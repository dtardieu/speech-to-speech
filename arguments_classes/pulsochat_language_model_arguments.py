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
