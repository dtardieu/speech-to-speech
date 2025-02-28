import logging
import numpy as np
import librosa
import torch
from openai import OpenAI
from baseHandler import BaseHandler
from rich.console import Console

logger = logging.getLogger(__name__)
console = Console()

class OpenAITTSHandler(BaseHandler):
    def setup(
        self,
        should_listen,
        api_key=None,
        language="fr",
        voice="alloy",
        blocksize=512,
    ):
        self.should_listen = should_listen
        self.language = language
        self.voice = voice  # OpenAI TTS supports multiple voices
        self.blocksize = blocksize
        self.client = OpenAI()
        logger.info(f"Warming up {self.__class__.__name__} with language {language}")
        self.warmup()

    def warmup(self):
        logger.info(f"Warming up {self.__class__.__name__}")
        try:
            _ = self.client.audio.speech.create(
                input="This is a test.", voice=self.voice, model="tts-1"
            )
        except Exception as e:
            logger.error(f"Warmup failed: {e}")

    def process(self, llm_sentence):

        if isinstance(llm_sentence, tuple):
            llm_sentence, language_code = llm_sentence
        try:
            console.print(f"[green]ASSISTANT: {llm_sentence}")

            response = self.client.audio.speech.create(
                input=llm_sentence, voice=self.voice, model="tts-1", response_format="wav"
            )
            speech_file_path = "output.wav"
            response.stream_to_file(speech_file_path)

            with open(speech_file_path, "rb") as f:
                audio_data = np.frombuffer(f.read(), dtype=np.int16)

            audio_data = librosa.resample(audio_data.astype(np.float32), orig_sr=24000, target_sr=16000)
#            audio_data = (audio_data * 32768).astype(np.int16)

            for i in range(0, len(audio_data), self.blocksize):
                yield np.pad(
                    audio_data[i : i + self.blocksize],
                    (0, self.blocksize - len(audio_data[i : i + self.blocksize])),
                )
        except Exception as e:
            logger.error(f"Error in OpenAITTSHandler: {e}")

        self.should_listen.set()
