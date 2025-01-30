import time
import logging
import os

from LLM.pulsochat_language_model import PulsochatModelHandler  # Adjust import as needed

logging.basicConfig(level=logging.DEBUG)  # So you see debug/info logs

def main():
    # Instantiate handler

    config_file = "./pulsochat/config.json"
    api_key = os.getenv('OPENAI_KEY')
    handler = PulsochatModelHandler(config_file=config_file, log_dir='.', api_key=api_key)

    # Setup with OSC enabled
    handler.setup(
        config_file="config.json",
        log_dir="logs",
        api_key="YOUR_API_KEY",
        enable_osc=True,                # <--- Key: Enable OSC
        osc_send_address="127.0.0.1",   # local loopback
        osc_send_port=8000,            # or any port you want
        osc_receive_address="127.0.0.1",
        osc_receive_port=9000
    )

    # The server is running in a background thread now.
    # We can do some testing: send a prompt, see if we get a response, etc.
    try:
        while True:
            # You can do some simple prompting to see if the model responds
            test_prompt = "Hello model, how are you?"

            # process() is a generator, so let's iterate over its yield
            for response, lang_code in handler.process(test_prompt):
                print("Model response:", response)

            # Now we might want to send the OSC state
            if handler.osc:
                handler.osc.send_status()

            # Wait a bit before repeating
            time.sleep(10)

    except KeyboardInterrupt:
        pass
    finally:
        handler.shutdown()

if __name__ == "__main__":
    main()
