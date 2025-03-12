from ConfigManager import ConfigManager
from InteractionLogger import InteractionLogger
from ChatHandler import ChatHandler
import os
from google.cloud import translate_v2 as translate
import time

CONFIG_DIR = '.'
DATA_DIR = '.'
key_file = "/Users/dtardieu/Documents/metamorphy-266a29b4942c.json"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_file


def main():
    # Load configuration
    config_manager = ConfigManager(CONFIG_DIR)
    config = config_manager.load_config('config.json')

    # Set up API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise EnvironmentError("OPENAI_API_KEY environment variable not set.")

    # Initialize logger
    logger = InteractionLogger(DATA_DIR)

    # Initialize chat handler
    chat_handler = ChatHandler(config, api_key, logger)

    translate_client = translate.Client()

    history = []
    interaction=0
    #print(chat_handler.get_initial_chatbot_value())
    while 1:
        chunks = []
        interaction += 1
        user = input()
        print(f"user: {user}")
        print("met: ", end='')
        start = time.time()
        user_en=translate_client.translate(user, target_language="en", format_="text")["translatedText"]
        t1 = time.time()
        print(f"Translation: {t1-start}")
        for chunk in chat_handler.response(user_en, history, stream=True):
            chunks.append(chunk)
            chunk_fr = translate_client.translate(chunk, target_language="fr", format_="text")["translatedText"]
            print(chunk_fr)
        response_en="".join(chunks)
        t2 = time.time()
        print(f"LLM: {t2-t1}")

        end=time.time()
        print(f"Translation 2: {end-t2}")
        history.append({"role": "user", "content": user_en})
        history.append({"role": "assistant", "content": response_en})



if __name__ == "__main__":
    main()
