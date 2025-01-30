import socket
import logging
import time
from rich.console import Console

logger = logging.getLogger(__name__)
console = Console()


class SocketSender:
    """
    Handles sending generated audio packets to the clients.
    """

    def __init__(self, stop_event, queue_in, host="0.0.0.0", port=12346):
        self.stop_event = stop_event
        self.queue_in = queue_in
        self.host = host
        self.port = port

    def run(self):
        """
        Boucle principale :
        - Crée un socket, écoute sur self.host:self.port avec timeout.
        - Accepte une connexion s’il y en a une.
        - Transmet les chunks depuis la queue tant que la connexion est active et que stop_event n’est pas set.
        - Si la connexion est fermée, on attend 2s avant de réessayer d’écouter.
        """
        logger.info("SocketSender started. Waiting for incoming connections...")

        while not self.stop_event.is_set():
            try:
                # Étape 1 : création du socket et mise en écoute
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    s.bind((self.host, self.port))
                    s.listen(1)
                    s.settimeout(2.0)  # Timeout de 2s pour accepter la connexion

                    logger.info(f"Sender listening on {self.host}:{self.port} ...")
                    try:
                        conn, addr = s.accept()
                    except socket.timeout:
                        # Personne ne s'est connecté pendant le timeout
                        continue

                    logger.info(f"Sender connected with {addr}")

                    # Étape 2 : envoyer les chunks de la queue
                    while not self.stop_event.is_set():
                        audio_chunk = self.queue_in.get()
                        try:
                            conn.sendall(audio_chunk)
                        except (BrokenPipeError, ConnectionResetError) as e:
                            logger.warning(f"Sender connection lost: {e}")
                            break

                        if isinstance(audio_chunk, bytes) and audio_chunk == b"END":
                            logger.info("END signal received, closing Sender connection.")
                            break

                    # On ferme la connexion courante avant de retenter
                    conn.close()
                    logger.info("Sender connection closed. Will retry in 2 seconds.")
                    time.sleep(2)

            except Exception as e:
                logger.error(f"Error in SocketSender: {e}")
                time.sleep(2)

        logger.info("SocketSender stopped.")

