import logging
import numpy as np
import librosa
import tempfile
import os
from gtts import gTTS
from baseHandler import BaseHandler
from rich.console import Console
import soundfile as sf

logger = logging.getLogger(__name__)

console = Console()


class GoogleTTSHandler(BaseHandler):
    def setup(
        self,
        should_listen,
        language="en",
        blocksize=512,
    ):
        self.should_listen = should_listen
        self.language = language
        self.blocksize = blocksize
        logger.info(f"GoogleTTSHandler initialized with language {language}")
        self.warmup()

    def warmup(self):
        """Prepares TTS by generating a short silent audio file."""
        logger.info(f"Warming up {self.__class__.__name__}")
        _ = self.text_to_speech("Testing Google TTS.", self.language)

    def text_to_speech(self, text, language):
        """Converts text to speech and returns an audio array."""
        try:
            with tempfile.NamedTemporaryFile(delete=True, suffix=".wav") as temp_audio:
                tts = gTTS(text=text, lang=language, slow=False)
                temp_path = temp_audio.name.replace(".wav", ".mp3")  # gTTS only saves MP3
                tts.save(temp_path)

                # Load and process the audio
                audio, sr = librosa.load(temp_path, sr=16000)
                os.remove(temp_path)  # Cleanup MP3 file
                return audio
        except Exception as e:
            logger.error(f"Error in GoogleTTSHandler: {e}")
            return np.array([])

    def process(self, llm_sentence):
        """Processes text input and yields audio chunks."""
        language_code = None

        if isinstance(llm_sentence, tuple):
            llm_sentence, language_code = llm_sentence

        console.print(f"[green]ASSISTANT: {llm_sentence}")

        if language_code and self.language != language_code:
            console.print(f"[green]Language code: {language_code}")
            self.language = language_code  # Update language dynamically

        try:
            audio_chunk = self.text_to_speech(llm_sentence, self.language)
        except Exception as e:
            logger.error(f"GoogleTTSHandler error: {e}")
            audio_chunk = np.array([])

        if len(audio_chunk) == 0:
            self.should_listen.set()
            return

        # Normalize audio and convert to int16 format
        audio_chunk = (audio_chunk * 32768).astype(np.int16)

        # Yield in chunks
        for i in range(0, len(audio_chunk), self.blocksize):
            yield np.pad(
                audio_chunk[i : i + self.blocksize],
                (0, self.blocksize - len(audio_chunk[i : i + self.blocksize])),
            )

        self.should_listen.set()
