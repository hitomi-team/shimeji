import logging
from shimeji.model_provider import ModelProvider

# model_provider - provides an API or an interface to inference a GPT model
# preprocessors - used to preprocess the input before inference
# postprocessors - used to postprocess the output after inference

class ChatBot:
    def __init__(self, name, model_provider, **kwargs):
        self.name = name
        self.model_provider = model_provider

        self.preprocessors = kwargs.get('preprocessors', [])
        self.postprocessors = kwargs.get('postprocessors', [])

        self.conversation_chain = []
    
    # go through preprocessor but forgo postprocessing stage
    def should_respond(self, text, push_chain):
        if push_chain:
            self.conversation_chain.append(push_chain)
        if self.conversation_chain:
            text = '\n'.join(self.conversation_chain)
        
        if self.preprocessors:
            for preprocessor in self.preprocessors:
                text = preprocessor(text, is_respond=False, name=self.name)
        
        return self.model_provider.should_respond(text, self.name)

    def respond(self, text, push_chain):
        if push_chain:
            self.conversation_chain.append(text)
        if self.conversation_chain:
            text = '\n'.join(self.conversation_chain)

        if self.preprocessors:
            for preprocessor in self.preprocessors:
                text = preprocessor.__call__(text, is_respond=True, name=self.name)
        
        response = self.model_provider.response(text)

        if self.postprocessors:
            for postprocessor in self.postprocessors:
                response = postprocessor.__call__(response)
        
        if push_chain:
            self.conversation_chain.append(f'{self.name}:{response}')
        
        return response

    def conditional_response(self, text, push_chain=True):
        if self.should_respond(text, push_chain):
            return self.respond(text, False)
        else:
            return None