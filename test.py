from shimeji import ChatBot
from shimeji.model_provider import ModelProvider, Sukima_ModelProvider, ModelGenRequest, ModelGenArgs, ModelSampleArgs
from shimeji.preprocessor import ContextPreprocessor
from shimeji.postprocessor import NewlinePrunerPostprocessor

gen_args = ModelGenArgs(max_length=100, min_length=1, eos_token_id=198)
sample_args = ModelSampleArgs(temp=0.75, top_p=0.725, typical_p=0.95, rep_p=1.125)
model_args = ModelGenRequest(model='c1-6B-8bit', prompt='', sample_args=sample_args, gen_args=gen_args)

model_provider = Sukima_ModelProvider(
    'http://192.168.0.147:8000',
    username='username',
    password='password',
    args=model_args
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
