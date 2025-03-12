from ConfigManager import ConfigManager
from InteractionLogger import InteractionLogger
from ChatHandler import ChatHandler
import json


def main():
    config_file = "config-new.json"
    with open(config_file) as f:
        config = json.load(f)

    logger = InteractionLogger('.')
    client = ChatHandler(config, '', logger)




    response_generator = client.response(message='Hello', history=[])

    # Iterate over the generator to print each chunk
    for chunk in response_generator:
        print(chunk, end='')

    response_generator = client.response(message='Hello', history=[])

    # Iterate over the generator to print each chunk
    for chunk in response_generator:
        print(chunk, end='')


if __name__ == "__main__":
    main()
