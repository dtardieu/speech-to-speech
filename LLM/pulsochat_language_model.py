import logging
import time
import json
import os

from nltk import sent_tokenize
from rich.console import Console
from google.cloud import translate_v2 as translate

from baseHandler import BaseHandler
from LLM.chat import Chat
import requests

from pulsochat.ChatHandler import ChatHandler
from pulsochat.ConfigManager import ConfigManager
from pulsochat.InteractionLogger import InteractionLogger

WHISPER_LANGUAGE_TO_LLM_LANGUAGE = {
    "en": "english",
    "fr": "french",
    "es": "spanish",
    "zh": "chinese",
    "ja": "japanese",
    "ko": "korean",
    "hi": "hindi",
    "de": "german",
    "pt": "portuguese",
    "pl": "polish",
    "it": "italian",
    "nl": "dutch",
}


logger = logging.getLogger(__name__)
console = Console()

key_file = "./metamorphy-266a29b4942c.json"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_file


CHAT_SIZE = 2000

class PulsochatModelHandler(BaseHandler):
    def setup(
        self,
        config_file,
        log_dir,
        api_key,
        stream,
        temperature,
        top_p,
        gen_kwargs={}
    ):
        with open(config_file) as f:
            config = json.load(f)

        self.stream = stream
        self.client = ChatHandler(config, api_key, InteractionLogger(log_dir))
        self.chat = Chat(CHAT_SIZE)
        self.translate_client = translate.Client()
        self.temperature=temperature
        self.top_p=top_p
        # Register handlers for OSC messages
        if self.osc_server:
            self.osc_server.add_handler("/pulsochat/reset", self._handle_reset)

        self.warmup()

    def warmup(self):
        logger.info(f"Warming up {self.__class__.__name__}")
        start = time.time()
        result = self.client.response("Hello!")
        end = time.time()
        logger.info(f"{self.__class__.__name__}: warmed up in {(end - start):.3f}s")

    def process(self, prompt):
        logger.debug("call api language model...")
        language_code = None
        if isinstance(prompt, tuple):
            prompt, language_code = prompt


        logger.debug(prompt)

        # Call the response generator

        if language_code != "en":
            prompt_en = self.translate_client.translate(prompt, target_language="en", format_="text")["translatedText"]
            #prompt_en=prompt
        else:
            prompt_en=prompt

        response_generator = self.client.response(prompt_en, self.chat.to_list(), stream=True, temperature=self.temperature, top_p=self.top_p)

        import time

        start = time.time()
        generated_text = ""
        for chunk in response_generator:
            generated_text += chunk
            if language_code != "en-fr":
                chunk_fr = self.translate_client.translate(chunk, target_language=language_code, format_="text")["translatedText"]
                #chunk_fr = chunk
            else:
                chunk_fr=chunk
            yield chunk_fr, language_code  # Yielding chunks in streaming mode
        end = time.time()
        if self.osc_client:
            self.send_osc_message("/pulsochat/state", str(self.client.get_current_state()))

        self.chat.append({"role": "user", "content": prompt_en})
        self.chat.append({"role": "assistant", "content": generated_text})



    def _handle_reset(self, address, *args):
        """
        OSC handler for the reset command.
        """
        logger.info("Received OSC reset command. Resetting ChatHandler and Chat.")
        self._reset_chat_handler()
        self._reset_chat()

    def _reset_chat_handler(self):
        """
        Invoke the ChatHandler's reset logic, if available.
        """
        if hasattr(self.client, "reset"):
            self.client.reset()
        else:
            logger.warning("ChatHandler has no reset() method.")

    def _reset_chat(self):
        self.chat.buffer = []
