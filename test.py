from shimeji import ChatBot
from shimeji.model_provider import ModelProvider, Sukima_ModelProvider
from shimeji.preprocessor import ContextPreprocessor
from shimeji.postprocessor import NewlinePrunerPostprocessor

model_provider = Sukima_ModelProvider(
    'http://c1.shitposts.club:8000',
    username='test2',
    password='test2',
    args={
        'model': 'c1-6b',
        'softprompt': '014669ba-fd58-4b97-bb76-35da2ff438ea',
        'prompt': '',
        'sample_args': {
            'temp': 0.5,
            'tfs': 0.993
        },
        'gen_args': {
            'max_length': 100
        }
    }
)

bot_name = input('Enter a bot name:')

chatbot = ChatBot(
    name=bot_name,
    model_provider=model_provider,
    preprocessors=[ContextPreprocessor()],
    postprocessors=[NewlinePrunerPostprocessor()]
)

while True:
    try:
        user_input = input('User: ')
        response = chatbot.respond('User: ' + user_input, push_chain=True)
        print(f'{bot_name}:{response}')
    except KeyboardInterrupt:
        print('\n==Conversation Chain==\n', '\n'.join(chatbot.conversation_chain))
        break
