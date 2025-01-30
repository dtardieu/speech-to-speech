from pythonosc import dispatcher, osc_server

def handle_state(address, *args):
    print(f"Received state on {address}: {args}")

def handle_speech_detected(address, *args):
    print(f"User speaks {address}: {args}")

def handle_bot_speaks(address, *args):
    print(f"Bot speaks {address}: {args}")


disp = dispatcher.Dispatcher()
disp.map("/pulsochat/state", handle_state)
disp.map("/vad_handler/speech_detected", handle_speech_detected)
disp.map("/listen_and_play/bot_speaks", handle_bot_speaks)


server = osc_server.ThreadingOSCUDPServer(("127.0.0.1", 8000), disp)

print("Starting test OSC receiver on port 8000...")
try:
    server.serve_forever()
except KeyboardInterrupt:
    pass
