import logging
import time

from nltk import sent_tokenize
from rich.console import Console
from openai import OpenAI

from baseHandler import BaseHandler
from LLM.chat import Chat

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

class OpenApiModelHandler(BaseHandler):
    """
    Handles the language model part.
    """
    def setup(
        self,
        model_name="deepseek-chat",
        device="cuda",
        gen_kwargs={},
        base_url =None,
        api_key=None,
        stream=False,
        user_role="user",
        chat_size=1,
        init_chat_role="system",
        init_chat_prompt="You are a helpful AI assistant.",
    ):
        self.model_name = model_name
        self.stream = stream
        self.chat = Chat(chat_size)
        if init_chat_role:
            if not init_chat_prompt:
                raise ValueError(
                    "An initial promt needs to be specified when setting init_chat_role."
                )
            self.chat.init_chat({"role": init_chat_role, "content": init_chat_prompt})
        self.user_role = user_role
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.warmup()

    def warmup(self):
        logger.info(f"Warming up {self.__class__.__name__}")
        start = time.time()
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": "Hello"},
            ],
            stream=self.stream
        )
        end = time.time()
        logger.info(
            f"{self.__class__.__name__}:  warmed up! time: {(end - start):.3f} s"
        )
    def process(self, prompt):
        logger.debug("call api language model...")

        # 1. If prompt is a (text, language_code) tuple, extract and handle "-auto" logic.
        language_code = None
        if isinstance(prompt, tuple):
            prompt, language_code = prompt
            if language_code.endswith("-auto"):
                language_code = language_code[:-5]
                # prepend the translation instruction to the prompt text
                prompt = f"Please reply to my message in {WHISPER_LANGUAGE_TO_LLM_LANGUAGE[language_code]}. " + prompt

        # 2. Append the new user message (with any translation‐prefix) to the Chat buffer
        self.chat.append({"role": self.user_role, "content": prompt})

        # 3. Build the messages payload from the entire history (including init_chat_message, if set)
        messages_payload = self.chat.to_list()

        # 4. Call the model with streaming enabled
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages_payload,
            stream=True
        )
        print(messages_payload)
        if self.stream:
            generated_text = ""
            printable_buffer = ""
            for chunk in response:
                new_delta = chunk.choices[0].delta.content or ""
                generated_text += new_delta
                printable_buffer += new_delta

                # Once we detect at least one full sentence, yield it
                sentences = sent_tokenize(printable_buffer)
                if len(sentences) > 1:
                    # yield the first complete sentence
                    yield sentences[0], language_code
                    # remove that sentence from printable_buffer
                    printable_buffer = printable_buffer[len(sentences[0]):]

            # After streaming ends, whatever remains is the final (partial or full) sentence
            if printable_buffer.strip():
                yield printable_buffer, language_code

            # 5. Finally append the assistant’s full response to chat history
            self.chat.append({"role": "assistant", "content": generated_text})

        else:
            # (This branch only happens if self.stream == False)
            full_response = response.choices[0].message.content
            self.chat.append({"role": "assistant", "content": full_response})
            yield full_response, language_code