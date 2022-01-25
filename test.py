from shimeji import ChatBot
from shimeji.model_provider import ModelProvider
from shimeji.preprocessor import ContextPreprocessor

class DummyModelProvider(ModelProvider):
    def __init__(self, endpoint_url: str, **kwargs):
        super().__init__(endpoint_url, **kwargs)

    def generate(self, args=None):
        return 'hello'

    def should_respond(self, context=None, name=None):
        return True

    def response(self, context):
        return self.generate()

chatbot = ChatBot('chatbot', DummyModelProvider(endpoint_url=None, args=None), preprocessors=[ContextPreprocessor], postprocessors=None)

if chatbot.should_respond('hello'):
    print(chatbot.respond('hello'))