import logging
import time

from nltk import sent_tokenize
from rich.console import Console

from baseHandler import BaseHandler
from LLM.chat import Chat
import requests

from pulsochat.ChatHandler import ChatHandler
from pulsochat.ConfigManager import ConfigManager
from pulsochat.InteractionLogger import InteractionLogger
import json
logger = logging.getLogger(__name__)

console = Console()

WHISPER_LANGUAGE_TO_LLM_LANGUAGE = {
    "en": "english",
    "fr": "french",
    "es": "spanish",
    "zh": "chinese",
    "ja": "japanese",
    "ko": "korean",
}

class PulsochatModelHandler(BaseHandler):
    """
    Handles the language model part.
    """
    def setup(
        self,
        config_file,
        log_dir,
        api_key,
        gen_kwargs={},
        stream=False,
    ):
        with open(config_file) as f:
            config = json.load(f)
        self.stream = stream
        self.client = ChatHandler(config, api_key, InteractionLogger(log_dir))
        self.chat = Chat(1000)
        self.warmup()

    def warmup(self):
        logger.info(f"Warming up {self.__class__.__name__}")
        start = time.time()
        result = self.client.response("Hello !")
        end = time.time()
        logger.info(
            f"{self.__class__.__name__}:  warmed up! time: {(end - start):.3f} s"
        )

    def process(self, prompt):
        logger.debug("call api language model...")
        language_code = None
        if isinstance(prompt, tuple):
            prompt, language_code = prompt
        self.chat.append({"role": "user", "content": prompt})
        logger.debug(prompt)
        generated_text = self.client.response(prompt, self.chat.to_list())
        self.chat.append({"role": "assistant", "content": generated_text})
        yield generated_text, language_code
