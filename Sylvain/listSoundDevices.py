import sounddevice as sd

# Liste tous les périphériques disponibles
devices = sd.query_devices()

# Affiche les informations pour chaque périphérique d'entrée et de sortie
for idx, device in enumerate(devices):
    # Affiche les périphériques d'entrée
    if device['max_input_channels'] > 0:
        print(f"Device {idx}: {device['name']} - Input Channels: {device['max_input_channels']}")
    
    # Affiche les périphériques de sortie
    if device['max_output_channels'] > 0:
        print(f"Device {idx}: {device['name']} - Output Channels: {device['max_output_channels']}")
