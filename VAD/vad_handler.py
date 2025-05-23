import torchaudio
from VAD.vad_iterator import VADIterator
from baseHandler import BaseHandler
import numpy as np
import torch
from rich.console import Console

from utils.utils import int2float
from df.enhance import enhance, init_df
import logging
import tempfile
import scipy.io.wavfile

logger = logging.getLogger(__name__)

console = Console()


class VADHandler(BaseHandler):
    """
    Handles voice activity detection. When voice activity is detected, audio will be accumulated until the end of speech is detected and then passed
    to the following part.
    """

    def setup(
        self,
        should_listen,
        thresh=0.5,
        sample_rate=16000,
        min_silence_ms=1000,
        min_speech_ms=500,
        max_speech_ms=float("inf"),
        speech_pad_ms=30,
        audio_enhancement=False,
    ):
        self.should_listen = should_listen
        self.sample_rate = sample_rate
        self.min_silence_ms = min_silence_ms
        self.min_speech_ms = min_speech_ms
        self.max_speech_ms = max_speech_ms
        self.model, _ = torch.hub.load("snakers4/silero-vad", "silero_vad")
        self.iterator = VADIterator(
            self.model,
            threshold=thresh,
            sampling_rate=sample_rate,
            min_silence_duration_ms=min_silence_ms,
            speech_pad_ms=speech_pad_ms,
            osc_client = self.osc_client
        )
        self.audio_enhancement = audio_enhancement
        if audio_enhancement:
            self.enhanced_model, self.df_state, _ = init_df()

    def process(self, audio_chunk):
        audio_int16 = np.frombuffer(audio_chunk, dtype=np.int16)
        audio_float32 = int2float(audio_int16)
        vad_output = self.iterator(torch.from_numpy(audio_float32))
        if vad_output is not None and len(vad_output) != 0:
            logger.debug("VAD: end of speech detected")
            array = torch.cat(vad_output).cpu().numpy()
            duration_ms = len(array) / self.sample_rate * 1000
            if duration_ms < self.min_speech_ms or duration_ms > self.max_speech_ms:
                logger.debug(
                    f"audio input of duration: {len(array) / self.sample_rate}s, skipping"
                )
            else:
                self.should_listen.clear()
                logger.debug("Stop listening")
                if self.audio_enhancement:
                    if self.sample_rate != self.df_state.sr():
                        audio_float32 = torchaudio.functional.resample(
                            torch.from_numpy(array),
                            orig_freq=self.sample_rate,
                            new_freq=self.df_state.sr(),
                        )
                        enhanced = enhance(
                            self.enhanced_model,
                            self.df_state,
                            audio_float32.unsqueeze(0),
                        )
                        enhanced = torchaudio.functional.resample(
                            enhanced,
                            orig_freq=self.df_state.sr(),
                            new_freq=self.sample_rate,
                        )
                    else:
                        enhanced = enhance(
                            self.enhanced_model, self.df_state, audio_float32
                        )
                    array = enhanced.numpy().squeeze()
                #tmp_wav_path = self.save_audio_to_tmp_wav(array, self.sample_rate)
                #logger.info(f"Temporary WAV file saved at: {tmp_wav_path}")
                yield array


    def save_audio_to_tmp_wav(self, audio_array, sample_rate):
        # Create a temporary file that won't be automatically deleted
        tmp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        tmp_filename = tmp_file.name
        tmp_file.close()  # Close the file so that scipy can write to it

        # Write the audio array to the wav file.
        # Note: If your audio_array is float32 and in the range [-1, 1],
        # scipy will write it as a float file. If you prefer int16, you might
        # want to convert it:
        # audio_int16 = (audio_array * 32767).astype(np.int16)
        scipy.io.wavfile.write(tmp_filename, sample_rate, audio_array)

        return tmp_filename

    @property
    def min_time_to_debug(self):
        return 0.00001
