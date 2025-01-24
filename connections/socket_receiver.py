import socket
import logging
import time
from rich.console import Console

logger = logging.getLogger(__name__)
console = Console()


class SocketReceiver:
    """
    Handles reception of the audio packets from the client.
    """

    def __init__(
        self,
        stop_event,
        queue_out,
        should_listen,
        host="0.0.0.0",
        port=12345,
        chunk_size=1024,
    ):
        self.stop_event = stop_event
        self.queue_out = queue_out
        self.should_listen = should_listen
        self.chunk_size = chunk_size
        self.host = host
        self.port = port

    def receive_full_chunk(self, conn, chunk_size):
        """
        Lit un chunk complet (chunk_size octets) depuis la connexion.
        Retourne None si la connexion est fermée avant d’avoir tout lu.
        """
        data = b""
        while len(data) < chunk_size:
            packet = conn.recv(chunk_size - len(data))
            if not packet:
                # connection closed
                return None
            data += packet
        return data

    def run(self):
        """
        Boucle principale :
        - Crée un socket, écoute sur self.host:self.port avec timeout.
        - Accepte une connexion s’il y en a une.
        - Lit les chunks tant que la connexion est active et que stop_event n’est pas set.
        - Si la connexion est fermée, on attend 2s avant de réécouter.
        """
        logger.info("SocketReceiver started. Waiting for incoming connections...")

        while not self.stop_event.is_set():
            try:
                # Étape 1 : Créer le socket
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    s.bind((self.host, self.port))
                    s.listen(1)
                    s.settimeout(2.0)  # Timeout de 2s pour accepter la connexion

                    logger.info(f"Listening on {self.host}:{self.port} ...")
                    try:
                        conn, addr = s.accept()  # Tente d'accepter la connexion
                    except socket.timeout:
                        # Personne ne s'est connecté pendant le timeout
                        continue

                    logger.info(f"Receiver connected from {addr}")
                    self.should_listen.set()

                    # Étape 2 : Lire en boucle tant que pas stoppé
                    while not self.stop_event.is_set():
                        audio_chunk = self.receive_full_chunk(conn, self.chunk_size)
                        if audio_chunk is None:
                            # connection fermée côté client
                            self.queue_out.put(b"END")
                            logger.warning("Connection closed by client.")
                            break
                        if self.should_listen.is_set():
                            self.queue_out.put(audio_chunk)

                    # Une fois la boucle terminée, fermer la connexion
                    conn.close()
                    logger.info("Connection closed. Will retry in 2 seconds.")
                    
                    # On attend 2 secondes avant de retenter une écoute
                    time.sleep(2)

            except Exception as e:
                logger.error(f"Error in SocketReceiver: {e}")
                time.sleep(2)

        logger.info("SocketReceiver stopped.")

