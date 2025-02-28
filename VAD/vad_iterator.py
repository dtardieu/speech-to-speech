import torch

class VADIterator:
    def __init__(
        self,
        model,
        threshold: float = 0.5,
        sampling_rate: int = 16000,
        min_silence_duration_ms: int = 100,
        speech_pad_ms: int = 30,
        osc_client=None
    ):
        self.model = model
        self.threshold = threshold
        self.sampling_rate = sampling_rate
        self.osc_client = osc_client

        if sampling_rate not in [8000, 16000]:
            raise ValueError(
                "VADIterator does not support sampling rates other than [8000, 16000]"
            )

        self.min_silence_samples = int(sampling_rate * min_silence_duration_ms / 1000)
        self.speech_pad_samples = int(sampling_rate * speech_pad_ms / 1000)
        self.reset_states()

    def reset_states(self):
        self.model.reset_states()
        self.triggered = False
        self.temp_end = 0
        self.current_sample = 0
        self.buffer = []           # Main speech buffer.
        self.pre_buffer = torch.tensor([])  # Pre-padding buffer.
        self.post_buffer = torch.tensor([]) # Post-padding buffer.

    @torch.no_grad()
    def __call__(self, x):
        if not torch.is_tensor(x):
            try:
                x = torch.Tensor(x)
            except Exception:
                raise TypeError("Audio cannot be cast to tensor. Cast it manually")

        window_size_samples = x.shape[0]
        self.current_sample += window_size_samples

        # Update pre_buffer: keep the last speech_pad_samples worth of audio.
        if self.pre_buffer.numel() == 0:
            self.pre_buffer = x.clone()
        else:
            self.pre_buffer = torch.cat((self.pre_buffer, x))
        if self.pre_buffer.numel() > self.speech_pad_samples:
            self.pre_buffer = self.pre_buffer[-self.speech_pad_samples:]

        # Obtain speech probability.
        speech_prob = self.model(x, self.sampling_rate).item()

        # If speech resumes, clear the post_buffer.
        if speech_prob >= self.threshold and self.temp_end:
            # This means we had a dip but speech came back.
            if self.post_buffer.numel() > 0:
                # Incorporate any transitional audio back into the main buffer.
                self.buffer.append(self.post_buffer.clone())
                self.post_buffer = torch.tensor([])
            self.temp_end = 0

        # If speech is just starting.
        if speech_prob >= self.threshold and not self.triggered:
            if self.osc_client:
                self.osc_client.send_message("/vad_handler/speech_detected", "start")
            print("------------------- start of speech detected ----------------")
            self.triggered = True
            # Start with the pre-buffer for pre-padding.
            self.buffer = [self.pre_buffer.clone()]
            # Clear any old post-buffer.
            self.post_buffer = torch.tensor([])
            return None

        # If in an active speech segment:
        if self.triggered:
            # If the probability is below threshold (even if it's above threshold - 0.15),
            # accumulate into post_buffer.
            if speech_prob < self.threshold:
                # Begin tracking the moment we started to lose confidence.
                if not self.temp_end:
                    self.temp_end = self.current_sample
                self.post_buffer = torch.cat((self.post_buffer, x))
                # Check if enough silence has been observed.
                if self.current_sample - self.temp_end >= self.min_silence_samples:
                    # Once enough silence, take post_buffer as padding.
                    if self.post_buffer.numel() >= self.speech_pad_samples:
                        pad_chunk = self.post_buffer[:self.speech_pad_samples]
                    else:
                        pad_chunk = self.post_buffer.clone()
                    self.buffer.append(pad_chunk)
                    if self.osc_client:
                        self.osc_client.send_message("/vad_handler/speech_detected", "stop")
                    print("------------------- end of speech detected ----------------")
                    utterance = self.buffer
                    self.reset_states()
                    return utterance
                else:
                    # Not enough silence yet; wait.
                    return None
            else:
                # If speech probability is back above threshold,
                # then the current chunk is considered active speech.
                # If we had accumulated any transitional (post) audio, add it to the main buffer.
                if self.post_buffer.numel() > 0:
                    self.buffer.append(self.post_buffer.clone())
                    self.post_buffer = torch.tensor([])
                self.buffer.append(x)
        return None
