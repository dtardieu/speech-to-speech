from dataclasses import dataclass, field


@dataclass
class PulsochatLanguageModelHandlerArguments:
    pulsochat_config_file: str = field(
        # default="HuggingFaceTB/SmolLM-360M-Instruct",
        default="",
        metadata={
            "help": "The config_file for pulsochat"
        },
    )
    pulsochat_log_dir: str = field(
        default=".",
        metadata={
            "help": "directory for logging conversations"
        },
    )
    pulsochat_api_key: str = field(
        default=None,
        metadata={
            "help": "Is a unique code used to authenticate and authorize access to an API."
        },
    )
    pulsochat_stream: bool = field(
        default=False,
        metadata={
            "help": "The stream parameter typically indicates whether data should be transmitted in a continuous flow rather"
                    " than in a single, complete response, often used for handling large or real-time data.Default is False"
        },
    )
