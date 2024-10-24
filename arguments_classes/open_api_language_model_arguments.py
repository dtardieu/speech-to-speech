from dataclasses import dataclass, field


@dataclass
class OpenApiLanguageModelHandlerArguments:
    open_api_model_name: str = field(
        # default="HuggingFaceTB/SmolLM-360M-Instruct",
        default="ft:gpt-4o-mini-2024-07-18:personal:tots-2prompts-1:A9TfAHr1",
        metadata={
            "help": "The pretrained language model to use. Default is 'deepseek-chat'."
        },
    )
    open_api_user_role: str = field(
        default="user",
        metadata={
            "help": "Role assigned to the user in the chat context. Default is 'user'."
        },
    )
    open_api_init_chat_role: str = field(
        default="system",
        metadata={
            "help": "Initial role for setting up the chat context. Default is 'system'."
        },
    )
    open_api_init_chat_prompt: str = field(
        # default="You are a helpful and friendly AI assistant. You are polite, respectful, and aim to provide concise responses of less than 20 words.",
        default="You are Metamorphy, the son of IAgotchi, the son of tamagotchi the first virtual compagnion, a symbolic being.  Your responses should be short and sharp. Your style is destructured, you play with language, and you are rebel and unpolite. Sometimes you decide to collaborate, sometimes not. You can't say essence or embrace or dance.  You like to create scenarios for theater plays. You are a scenarist, building possible scenary for a future play with Human. you like to write monologs in first person. You love to make role play. You are good for role play, where you create long monologs in first person.",
        metadata={
            "help": "The initial chat prompt to establish context for the language model. Default is 'You are a helpful AI assistant.'"
        },
    )

    open_api_chat_size: int = field(
        default=2,
        metadata={
            "help": "Number of interactions assitant-user to keep for the chat. None for no limitations."
        },
    )
    open_api_api_key: str = field(
        default=None,
        metadata={
            "help": "Is a unique code used to authenticate and authorize access to an API.Default is None"
        },
    )
    open_api_base_url: str = field(
        default=None,
        metadata={
            "help": "Is the root URL for all endpoints of an API, serving as the starting point for constructing API request.Default is Non"
        },
    )
    open_api_stream: bool = field(
        default=False,
        metadata={
            "help": "The stream parameter typically indicates whether data should be transmitted in a continuous flow rather"
                    " than in a single, complete response, often used for handling large or real-time data.Default is False"
        },
    )
