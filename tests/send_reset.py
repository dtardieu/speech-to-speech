from pythonosc import udp_client

client = udp_client.SimpleUDPClient("127.0.0.1", 9000)  # Must match your receive port
client.send_message("/pulsochat/reset", [])
print("Sent /pulsochat/reset command.")
