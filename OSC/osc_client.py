import logging
from pythonosc import udp_client

logger = logging.getLogger(__name__)

class OSCClient:
    """
    Handles sending OSC messages to a specified address and port.
    """

    def __init__(self, send_address="127.0.0.1", send_port=8000):
        """
        Initialize the OSC client.

        :param send_address: IP address to send OSC messages to.
        :param send_port: Port to send OSC messages to.
        """
        self.client = udp_client.SimpleUDPClient(send_address, send_port)

    def send_message(self, address, message):
        """
        Send an OSC message.

        :param address: OSC address.
        :param message: Message to send.
        """
        logger.debug(f"Sending OSC message to {address}: {message}")
        self.client.send_message(address, message)
