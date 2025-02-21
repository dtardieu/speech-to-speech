import threading
import sounddevice as sd
import numpy as np
import time
import logging

logger = logging.getLogger(__name__)

class LocalAudioStreamer:
    def __init__(
        self,
        input_queue,
        output_queue,
        input_device=4,   # Input device (Microphone) index or name
        output_device=4,  # Output device (Speaker) index or name
        input_channel=1,  # Input channel index
        output_channel=3,  # Output channel index
        list_play_chunk_size=512,
    ):
        self.list_play_chunk_size = list_play_chunk_size
        self.input_device = input_device
        self.output_device = output_device
        self.input_channel = input_channel
        self.output_channel = output_channel

        self.stop_event = threading.Event()
        self.input_queue = input_queue
        self.output_queue = output_queue

    def run(self):
        def callback(indata, outdata, frames, time, status):
            if status:
                logger.warning(f"Audio callback error: {status}")

            selected_input_channel = indata[:, self.input_channel]  # Select specified input channel
            if self.output_queue.empty():
                self.input_queue.put(selected_input_channel.copy())  # Capture only the selected input channel
                outdata[:] = 0  # Silence if no output available
            else:
                try:
                    output_data = self.output_queue.get()
                    if output_data.ndim == 1:
                        selected_output_channel = output_data  # Use directly if 1D
                    else:
                        selected_output_channel = output_data[:, 0]  # Use first column if 2D

                    # Ensure all channels except the specified output channel are set to zero
                    outdata[:] = 0  # Default to silence
                    outdata[:, self.output_channel] = selected_output_channel  # Send audio to specified output channel

                except Exception as e:
                    logger.error(f"Error processing audio output: {e}")
                    outdata[:] = 0  # Fallback to silence

        try:
            with sd.Stream(
                samplerate=16000,
                dtype="int16",
                channels=(self.input_channel + 1, self.output_channel + 1),
                device=(self.input_device, self.output_device),  # Use selected devices
                callback=callback,
                blocksize=self.list_play_chunk_size,
            ):
                logger.info(f"Starting local audio stream (Input: {self.input_device}, Output: {self.output_device}, Input Channel: {self.input_channel}, Output Channel: {self.output_channel})")
                while not self.stop_event.is_set():
                    time.sleep(0.001)
        except Exception as e:
            logger.error(f"Failed to initialize audio stream: {e}")
