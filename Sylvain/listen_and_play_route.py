import socket
import threading
from queue import Queue
from dataclasses import dataclass, field
import time
import numpy as np
import sounddevice as sd
from transformers import HfArgumentParser


@dataclass
class ListenAndPlayArguments:
    send_rate: int = field(default=16000, metadata={"help": "Taux d'échantillonnage en Hz (envoi)."})
    recv_rate: int = field(default=16000, metadata={"help": "Taux d'échantillonnage en Hz (réception)."})
    list_play_chunk_size: int = field(
        default=1024,
        metadata={"help": "Taille des blocs (en frames). Par défaut 1024."},
    )
    host: str = field(
        default="localhost",
        metadata={"help": "Le nom d'hôte ou l'adresse IP pour l'envoi et la réception."},
    )
    send_port: int = field(
        default=12345,
        metadata={"help": "Le port réseau pour l'envoi des données. Par défaut 12345."},
    )
    recv_port: int = field(
        default=12346,
        metadata={"help": "Le port réseau pour la réception des données. Par défaut 12346."},
    )
    input_device_index: int = field(
        default=0,
        metadata={"help": "Index du périphérique audio d'entrée."},
    )
    output_device_index: int = field(
        default=1,
        metadata={"help": "Index du périphérique audio de sortie."},
    )
    input_channel: int = field(
        default=0,
        metadata={"help": "Décalage canal entrée (non utilisé ici, on lit 1 canal mono)."},
    )
    output_channel: int = field(
        default=0,
        metadata={"help": "Décalage canal sortie (0 => on écrit dans [0], 1 => [1], etc.)."},
    )
    osc_ip: str = field(
        default="localhost",
        metadata={"help": "Le nom d'hôte ou l'adresse IP pour l'envoi OSC"},
    )
    osc_port: int = field(
        default=8000,
        metadata={"help": "Le port réseau pour l'envoi des données OSC. Par défaut 8000."},
    )


def listen_and_play(
    send_rate=16000,
    recv_rate=16000,
    list_play_chunk_size=1024,
    host="localhost",
    send_port=12345,
    recv_port=12346,
    input_device_index=0,
    output_device_index=1,
    input_channel=0,    # Modifié pour compatibilité avec mono
    output_channel=0,
    osc_ip,
    osc_port
):
    """
    Ouvre 1 canal en entrée (mono) et 'nb_output_channels = output_channel + 1' en sortie.
    On place le flux mono reçu dans le canal [output_channel].
    Fonctionne avec des versions anciennes de sounddevice (pas de param 'mapping').
    """

    stop_event = threading.Event()
    recv_queue = Queue()
    send_queue = Queue()

    # On ouvre suffisamment de canaux en sortie pour pouvoir "poser" notre mono
    nb_output_channels = output_channel + 1  # p. ex. 2 si output_channel=1

    bot_state = {"talking": False}

    osc_client = udp_client.SimpleUDPClient(osc_ip, osc_port)

    # --- Callback de sortie (lecture) ---
    def callback_recv(outdata, frames, time_info, status):
        """
        Récupère un bloc mono (frames * 1 canal * 2 octets) de recv_queue et
        le place dans [output_channel].
        """
        if not recv_queue.empty():
            data = recv_queue.get()
            if data is not None:
                data_np = np.frombuffer(data, dtype=np.int16)
                # On s'attend à frames*1 échantillon (mono)
                if len(data_np) == frames * 1:
                    data_np = data_np.reshape((frames, 1))
                else:
                    # S'il y a un écart (rare), on s'assure de reshaper proprement
                    data_np = data_np[: frames]
                    data_np = np.pad(data_np, (0, frames - len(data_np)), mode='constant')
                    data_np = data_np.reshape((frames, 1))

                # Prépare un tampon (frames, nb_output_channels) à zéro
                tmp = np.zeros((frames, nb_output_channels), dtype=np.int16)
                # Place le mono dans [output_channel]
                tmp[:, output_channel:output_channel+1] = data_np

                outdata[:] = tmp.tobytes()
            else:
                outdata[:] = b"\x00" * len(outdata)
        else:
            outdata[:] = b"\x00" * len(outdata)

    # --- Callback d'entrée (capture) ---
    def callback_send(indata, frames, time_info, status):
        """
        'indata' contient frames * 1 canal mono * 2 octets (int16).
        On l'envoie tel quel sur la socket (via la queue).
        """
        send_queue.put(indata)

    # --- Thread pour envoyer les données réseau ---
    def send_func(stop_event, send_queue, send_socket):
        while not stop_event.is_set():
            data = send_queue.get()
            if data is None:
                continue
            try:
                send_socket.sendall(data)
            except (socket.error, socket.timeout) as e:
                print(f"Erreur d'envoi : {e}. Reconnexion...")
                send_socket.close()
                send_socket = reconnect_socket(send_socket, host, send_port)

    # --- Thread pour recevoir les données réseau ---
    def recv_func(stop_event, recv_queue, recv_socket):
        """
        On reçoit frames*1*2 octets (mono, int16) à chaque bloc.
        """
        chunk_size = list_play_chunk_size * 1 * 2  # Modifié pour mono

        def receive_full_chunk(conn, chunk_size):
            data = b""
            while len(data) < chunk_size:
                packet = conn.recv(chunk_size - len(data))
                if not packet:
                    return None
                data += packet
            return data

        while not stop_event.is_set():
            try:
                data = receive_full_chunk(recv_socket, chunk_size)
                if data:
                    recv_queue.put(data)
            except (socket.error, socket.timeout) as e:
                print(f"Erreur de réception : {e}. Reconnexion...")
                recv_socket.close()
                recv_socket = reconnect_socket(recv_socket, host, recv_port)

    def reconnect_socket(sock, host, port):
        while True:
            try:
                print(f"Tentative de reconnexion à {host}:{port}...")
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((host, port))
                print(f"Reconnecté à {host}:{port}")
                return sock
            except (socket.error, socket.timeout) as e:
                print(f"Échec de connexion : {e}. Nouvel essai dans 3s...")
                time.sleep(3)

    try:
        print(f"> Périphérique d'entrée = {input_device_index}, 1 canal (mono).")
        print(f"> Périphérique de sortie = {output_device_index}, "
              f"ouverture de {nb_output_channels} canaux, flux dans [{output_channel}].")

        # -- En entrée, on lit 1 canal mono --
        send_stream = sd.RawInputStream(
            samplerate=send_rate,
            channels=1,  # Modifié pour mono
            dtype="int16",
            blocksize=list_play_chunk_size,
            callback=callback_send,
            device=input_device_index,
        )

        # -- En sortie, on ouvre (output_channel + 1) canaux --
        recv_stream = sd.RawOutputStream(
            samplerate=recv_rate,
            channels=nb_output_channels,
            dtype="int16",
            blocksize=list_play_chunk_size,
            callback=callback_recv,
            device=output_device_index,
        )

        # ---- Initialisation des sockets ----
        send_socket = reconnect_socket(socket.socket(socket.AF_INET, socket.SOCK_STREAM), host, send_port)
        recv_socket = reconnect_socket(socket.socket(socket.AF_INET, socket.SOCK_STREAM), host, recv_port)

        # ---- Démarrer les streams audio ----
        threading.Thread(target=send_stream.start).start()
        threading.Thread(target=recv_stream.start).start()

        # ---- Démarrer les threads réseau ----
        send_thread = threading.Thread(target=send_func, args=(stop_event, send_queue, send_socket))
        send_thread.start()
        recv_thread = threading.Thread(target=recv_func, args=(stop_event, recv_queue, recv_socket))
        recv_thread.start()

        input("Appuyez sur Entrée pour arrêter...")

    except KeyboardInterrupt:
        print("Fin du streaming (KeyboardInterrupt).")
    except Exception as e:
        print(f"Erreur inattendue: {e}")
    finally:
        stop_event.set()
        # Fermer les sockets
        if 'recv_socket' in locals():
            try:
                recv_socket.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            finally:
                recv_socket.close()
        if 'send_socket' in locals():
            send_socket.close()

        # Attendre la fin des threads
        if 'recv_thread' in locals():
            recv_thread.join()
        if 'send_thread' in locals():
            send_thread.join()
        print("Connexion fermée.")


def list_audio_devices():
    devices = sd.query_devices()
    print("=== Liste des périphériques audio disponibles ===")
    for i, dev in enumerate(devices):
        print(f"Device index {i}: {dev['name']}")
        print(f"  - Max input channels : {dev['max_input_channels']}")
        print(f"  - Max output channels: {dev['max_output_channels']}")
        print("------------------------------------------------")


if __name__ == "__main__":
    list_audio_devices()
    print()

    parser = HfArgumentParser((ListenAndPlayArguments,))
    (listen_and_play_kwargs,) = parser.parse_args_into_dataclasses()

    listen_and_play(**vars(listen_and_play_kwargs))
