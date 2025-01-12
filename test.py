from pulsochat.ChatHandler import ChatHandler
from pulsochat.ConfigManager import ConfigManager
from pulsochat.InteractionLogger import InteractionLogger
from LLM.chat import Chat
import os
import json

def main():
    api_key = os.getenv('OPENAI_KEY')
    logger = InteractionLogger('.')
    with open('/Users/damientardieu/src/speech-to-speech/pulsochat/config.json') as f:
        config = json.load(f)
    chat = Chat(100)
    pulsochat = ChatHandler(config, api_key, logger)


    print(pulsochat.response("Hello !"))

    user_resps = ['Me ?','Ryo','Yes','hello']

    chat.append({"role": "assistant", "content": pulsochat.get_initial_chatbot_value()})
    print(chat.to_list()[-1])

    for user_resp in user_resps:
        resp = pulsochat.response(user_resp, chat.to_list())
        chat.append({"role": "user", "content": user_resp})
        print(chat.to_list()[-1])
        chat.append({"role": "assistant", "content": resp})
        print(chat.to_list()[-1])

    print("----------------")
    print("----------------")
    for line in chat.to_list():
        print(line)



if __name__ == "__main__":
    main()
