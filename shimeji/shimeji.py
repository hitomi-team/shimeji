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
    
    # go through preprocessor but forgo postprocessing stage
    def should_respond(self, text):
        for preprocessor in self.preprocessors:
            text = preprocessor(text)
        
        return self.model_provider.should_respond(text, self.name)

    def respond(self, text):
        for preprocessor in self.preprocessors:
            text = preprocessor(text)
        
        response = self.model_provider.response(text)

        for postprocessor in self.postprocessors:
            response = postprocessor(response)
        
        return response