import logging
import threading
from pythonosc import dispatcher, osc_server

logger = logging.getLogger(__name__)

class OSCServer:
    """
    Handles receiving OSC messages and dispatching them to handlers.
    """

    def __init__(self, receive_address="127.0.0.1", receive_port=9000):
        """
        Initialize the OSC server.

        :param receive_address: IP address to listen for OSC messages.
        :param receive_port: Port to listen for OSC messages.
        """
        self.dispatcher = dispatcher.Dispatcher()
        self.server = osc_server.ThreadingOSCUDPServer(
            (receive_address, receive_port),
            self.dispatcher
        )
        self.server_thread = threading.Thread(
            target=self.server.serve_forever,
            daemon=True
        )
        self.is_running = False  # Tracks if the server is currently running

    def start_server(self):
        """
        Start the OSC server in a separate daemon thread.
        """
        if self.is_running:
            logger.warning("OSC server is already running. Skipping start.")
            return

        logger.info("Starting OSC server...")
        self.is_running = True
        self.server_thread.start()

    def stop_server(self):
        """
        Shutdown the OSC server and join the thread.
        """
        if not self.is_running:
            logger.warning("OSC server is not running. Skipping stop.")
            return

        logger.info("Stopping OSC server...")
        self.server.shutdown()
        self.server_thread.join()
        self.is_running = False

    def add_handler(self, address, handler):
        """
        Map an OSC address to a handler function.

        :param address: OSC address.
        :param handler: Handler function.
        """
        logger.debug(f"Mapping OSC address {address} to handler {handler}")
        self.dispatcher.map(address, handler)
