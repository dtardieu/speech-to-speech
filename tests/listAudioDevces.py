import sounddevice as sd

# List all available audio devices
devices = sd.query_devices()
for device in devices:
    print(device['name'])
