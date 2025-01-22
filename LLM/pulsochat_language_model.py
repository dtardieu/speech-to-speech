import logging
import time
import json

from nltk import sent_tokenize
from rich.console import Console

from baseHandler import BaseHandler
from LLM.chat import Chat
import requests

from pulsochat.ChatHandler import ChatHandler
from pulsochat.ConfigManager import ConfigManager
from pulsochat.InteractionLogger import InteractionLogger

# OSC imports
try:
    from pythonosc import udp_client
    from pythonosc import dispatcher
    from pythonosc import osc_server
    import threading
    OSC_AVAILABLE = True
except ImportError:
    # If python-osc is not installed, handle gracefully
    OSC_AVAILABLE = False

logger = logging.getLogger(__name__)
console = Console()

CHAT_SIZE = 1000

class PulsochatModelHandler(BaseHandler):
    """
    Handles the language model part and optionally starts an OSC server.
    """
    def setup(
        self,
        config_file,
        log_dir,
        api_key,
        stream,
        enable_osc,
        osc_send_address,
        osc_send_port,
        osc_receive_address,
        osc_receive_port,
        gen_kwargs={}
    ):
        """
        Setup the model handler and optionally the OSC server/client.

        :param enable_osc: Whether to enable OSC functionality (default: False).
        :param osc_send_address: IP address to which OSC messages will be sent.
        :param osc_send_port: Port to which OSC messages will be sent.
        :param osc_receive_address: IP address on which to listen for OSC messages.
        :param osc_receive_port: Port on which to listen for OSC messages.
        """
        with open(config_file) as f:
            config = json.load(f)

        self.stream = stream
        self.client = ChatHandler(config, api_key, InteractionLogger(log_dir))
        self.chat = Chat(CHAT_SIZE)

        self.osc = None
        if enable_osc and OSC_AVAILABLE:
            logger.info("OSC enabled. Initializing PulsochatOSC...")
            self.osc = self.PulsochatOSC(
                self.client,
                self.chat,
                send_address=osc_send_address,
                send_port=osc_send_port,
                receive_address=osc_receive_address,
                receive_port=osc_receive_port
            )
            self.osc.start_server()
        elif enable_osc:
            logger.warning("enable_osc=True, but python-osc is not installed or import failed.")
        else:
            logger.info("OSC disabled")

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
        self.chat.append({"role": "user", "content": prompt})
        logger.debug(prompt)
        generated_text = self.client.response(prompt, self.chat.to_list())
        if self.osc:
            self.osc.send_status()
        self.chat.append({"role": "assistant", "content": generated_text})
        yield generated_text, language_code


    def shutdown(self):
        """
        Cleanly shut down any running servers, threads, etc.
        """
        logger.info("Shutting down PulsochatModelHandler...")
        if self.osc:
            self.osc.stop_server()

    class PulsochatOSC:
        """
        Inner class to handle OSC communications for Pulsochat.
        """
        def __init__(
            self,
            chat_handler,
            chat,
            send_address="127.0.0.1",
            send_port=8000,
            receive_address="127.0.0.1",
            receive_port=9000
        ):
            """
            :param chat_handler: The ChatHandler instance to send or reset.
            :param chat: The Chat instance to reset.
            :param send_address: IP address to which OSC messages will be sent.
            :param send_port: Port to which OSC messages will be sent.
            :param receive_address: IP address on which to listen for incoming OSC messages.
            :param receive_port: Port on which to listen for incoming OSC messages.
            """
            self.chat_handler = chat_handler
            self.chat = chat

            # Create an OSC client for sending messages
            self.client = udp_client.SimpleUDPClient(send_address, send_port)

            # Create a dispatcher to handle incoming OSC messages
            self.dispatcher = dispatcher.Dispatcher()
            self.dispatcher.map("/pulsochat/reset", self._handle_reset)

            # Create and configure the OSC server for listening
            self.server = osc_server.ThreadingOSCUDPServer(
                (receive_address, receive_port),
                self.dispatcher
            )
            self.server_thread = threading.Thread(
                target=self.server.serve_forever,
                daemon=True
            )

        def start_server(self):
            """
            Start the OSC server in a separate daemon thread.
            """
            logger.info("Starting PulsochatOSC server...")
            self.server_thread.start()

        def stop_server(self):
            """
            Shutdown the OSC server and join the thread.
            """
            logger.info("Stopping PulsochatOSC server...")
            self.server.shutdown()
            self.server_thread.join()

        def send_status(self):
            current_state = self.chat_handler.get_current_state()
            logger.debug(f"Sending current state: {current_state}")
            self.client.send_message("/pulsochat/state", str(current_state))

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
            if hasattr(self.chat_handler, "reset"):
                self.chat_handler.reset()
            else:
                logger.warning("ChatHandler has no reset() method.")

        def _reset_chat(self):
            self.chat.buffer = []
