from pythonosc import udp_client

port = 8011
client = udp_client.SimpleUDPClient("127.0.0.1", port)  # Must match your receive port
client.send_message("/pulsochat/reset", [])
print("Sent /pulsochat/reset command on port {port}")
