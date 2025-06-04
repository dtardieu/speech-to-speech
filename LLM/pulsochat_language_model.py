import os
import time
import json
import logging
from nltk.tokenize import sent_tokenize
from google.cloud import translate_v2 as translate
import openai
from baseHandler import BaseHandler

from LLM.chat import Chat
from pulsochat.InteractionLogger import InteractionLogger
from utils.scenario_manager import ScenarioManager
from utils.osc_manager import OSCManager

logger = logging.getLogger(__name__)

key_file = "./metamorphy-266a29b4942c.json"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_file

WHISPER_LANGUAGE_TO_LLM_LANGUAGE = {
    "en": "english", "fr": "french", "es": "spanish",
    "zh": "chinese", "ja": "japanese", "ko": "korean",
    "hi": "hindi", "de": "german", "pt": "portuguese",
    "pl": "polish", "it": "italian", "nl": "dutch"
}

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

        self.scenario_manager = ScenarioManager(config, InteractionLogger(log_dir))
        self.chat = Chat(CHAT_SIZE)
        self.translate_client = translate.Client()
        self.stream = stream
        self.temperature = temperature
        self.top_p = top_p
        self.queue_in = None

        if self.osc_server:
            self.osc_manager = OSCManager(self.osc_server, self.osc_client)
            self.osc_manager.setup_handlers(self._handle_reset, self._handle_state)
        else:
            self.osc_manager = None
        self.client = openai.OpenAI()
        self.model_name = config.get("model_name")
        print(self.model_name)

        self.warmup()

    def warmup(self):
        logger.info("Warming up LLM")
        start = time.time()
        _ = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": "Hello"}]
        )
        logger.info(f"Warmup done in {time.time() - start:.2f}s")

    def _translate(self, text, target):
        return self.translate_client.translate(text, target_language=target, format_="text")["translatedText"]

    def process(self, prompt_tuple):
        prompt, language_code = prompt_tuple if isinstance(prompt_tuple, tuple) else (prompt_tuple, "en")

        if not prompt.strip():
            return

        if language_code != "en":
            prompt_en = self._translate(prompt, "en")
        else:
            prompt_en = prompt


        if self.scenario_manager.has_question():
            question = self.scenario_manager.get_question()
            self.scenario_manager.mark_question_asked()
            self.scenario_manager.increment_interactions()
            yield self._translate(question, language_code), language_code
            return

        messages = [{"role": "system", "content": self.scenario_manager.meta_prompt}]
        messages.extend(self.chat.to_list())
        messages.append({"role": "user", "content": prompt_en})

        response_obj = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            stream=True,
            temperature=self.temperature,
            top_p=self.top_p
        )

        generated_text = ""
        buffer = ""

        for chunk in response_obj:
            delta = chunk.choices[0].delta.content or ""
            generated_text += delta
            buffer += delta

            sentences = sent_tokenize(buffer)
            if len(sentences) > 1:
                for sentence in sentences[:-1]:
                    yield self._translate(sentence, language_code), language_code
                buffer = sentences[-1]

        if buffer:
            yield self._translate(buffer, language_code), language_code

        self.chat.append({"role": "user", "content": prompt_en})
        self.chat.append({"role": "assistant", "content": generated_text})
        self.scenario_manager.increment_interactions()
        if self.osc_manager:
            self.osc_manager.send_state(self.scenario_manager.get_interactions())

    def _handle_reset(self, address, *args):
        logger.info("Resetting chat and scenario")
        self.chat.buffer = []
        self.scenario_manager.reset()
        if self.queue_in:
            self.queue_in.put(("-", "fr"))

    def _handle_state(self, address, *args):
        phase_name = args[0]
        logger.info(f"Setting phase to: {phase_name}")
        self.scenario_manager.set_phase(phase_name)