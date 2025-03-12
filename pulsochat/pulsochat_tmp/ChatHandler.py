import openai
import json
from nltk.tokenize import sent_tokenize

class ChatHandler:
    """Manages chat interactions using an externally provided phase.

    Each phase is defined in the configuration file by a name and consists of an optional
    question and a prompt. The set_phase method uses the phase name to update the current phase.
    All responses are streamed.
    """

    def __init__(self, config, api_key, logger):
        self.config = config
        self.api_key = api_key
        self.logger = logger
        self.model_name = config.get("model_name", "")
        self.meta_prompt = config.get("meta_prompt", "")
        # Load the scenario (a list of phases) from the config.
        self.scenario = config.get("scenario", [])
        # The current phase is set externally via set_phase (by name).
        self.current_phase = None
        # Tracks whether the question in the current phase has already been sent.
        self.question_asked = False
        self.client = openai.OpenAI()
        self.nb_interactions=0


    def set_phase(self, phase_name):
        """
        Updates the current phase by its name.
        Searches the scenario list for a phase with the matching "name".
        Resets the question_asked flag so that the phase's question (if any) will be sent.
        """
        for phase in self.scenario:
            if phase.get("name") == phase_name:
                #if self.current_phase:
                #    if self.current_phase["name"]!=phase["name"]:
                self.nb_interactions=0
                self.current_phase = phase
                self.question_asked = False
                self.logger.log_interaction("SYSTEM", f"Phase set to: {phase_name}")
                print(f"changed phase to: {phase_name}")
                return
        self.logger.log_interaction("SYSTEM", f"Phase not found: {phase_name}")
        self.current_phase = None

    def _build_messages(self, message, history, prompt):
        """
        Constructs the messages payload for the API call.
        Begins with the meta prompt and history, then adds the user's message.
        If a prompt is provided, it is appended as a system message.
        """
        messages = [{"role": "system", "content": self.meta_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": message})
        #if prompt:
        #    messages.append({"role": "system", "content": prompt})
        return messages

    def _handle_streaming_response(self, response_obj, message):
        """
        Processes a streaming response from the API, yielding complete sentences.
        """
        full_response = ""
        buffer_text = ""
        for chunk in response_obj:
            new_text = new_text = chunk.choices[0].delta.content or ""
            full_response += new_text
            buffer_text += new_text
            sentences = sent_tokenize(buffer_text)
            if len(sentences) > 1:
                for sentence in sentences[:-1]:
                    yield sentence.replace("?", " ? ")
                buffer_text = sentences[-1]
        if buffer_text:
            yield buffer_text
        self.logger.log_interaction(message, full_response)

    def get_current_state(self):
        return self.nb_interactions

    def reset(self):
        print(f"ChatHandler - Reset")
        self.nb_interactions=0

    def response(self, message, history=None, temperature=1.0, top_p=1.0):
        """
        Generates a response based on the user message, conversation history, and the current phase.

        Behavior:
          - If the current phase has an optional "question" that hasn’t been sent yet, that question is yielded.
          - Otherwise, the "prompt" is used to generate text via the API.

        This method always streams the response.
        """
        if history is None:
            history = []

        # If no phase is set, fall back to the first phase if available.
        if self.current_phase is None:
            if self.scenario:
                print("init phase")
                self.current_phase = self.scenario[0]
                self.question_asked = False
            else:
                self.current_phase = {"prompt": ""}
        print(f"ChatHandler - Current phase: {self.current_phase}")
        # If there's an optional question and it hasn't been sent, yield it directly.
        if not self.question_asked and self.current_phase.get("question"):
            self.question_asked = True
            question_text = self.current_phase.get("question")
            self.logger.log_interaction(message, question_text)
            self.nb_interactions+=1
            yield question_text
            return

        prompt = self.current_phase.get("prompt", "")

        #if prompt:
        messages = self._build_messages(message, history, prompt)
        #print(json.dumps(messages, indent=4))
        response_obj = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            stream=True,
            top_p=top_p,
            temperature=temperature
        )
        self.nb_interactions+=1
        for part in self._handle_streaming_response(response_obj, message):
            yield part
