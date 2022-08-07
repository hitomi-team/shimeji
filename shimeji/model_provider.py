import aiohttp
from typing import Optional, List, Any
from pydantic import BaseModel
from .util import tokenizer
import requests
import json
import copy


class ModelGenArgs(BaseModel):
    max_length: int
    max_time: Optional[float] = None
    min_length: Optional[int] = None
    eos_token_id: Optional[int] = None
    logprobs: Optional[int] = None
    best_of: Optional[int] = None

    def toJSON(self):
        return json.dumps(self.dict())

class ModelLogitBiasArgs(BaseModel):
    id: int
    bias: float

    def toJSON(self):
        return json.dumps(self.dict())

class ModelPhraseBiasArgs(BaseModel):
    sequences: List[str]
    bias: float
    ensure_sequence_finish: bool
    generate_once: bool

    def toJSON(self):
        return json.dumps(self.dict())

class ModelSampleArgs(BaseModel):
    temp: Optional[float] = None
    top_p: Optional[float] = None
    top_a: Optional[float] = None
    top_k: Optional[int] = None
    typical_p: Optional[float] = None
    tfs: Optional[float] = None
    rep_p: Optional[float] = None
    rep_p_range: Optional[int] = None
    rep_p_slope: Optional[float] = None
    bad_words: Optional[List[str]] = None
    logit_biases: Optional[List[ModelLogitBiasArgs]] = None
    phrase_biases: Optional[List[ModelPhraseBiasArgs]] = None

    def toJSON(self):
        return json.dumps(self.dict())

class ModelGenRequest(BaseModel):
    model: str
    prompt: str
    softprompt: Optional[str] = None
    sample_args: ModelSampleArgs
    gen_args: ModelGenArgs

    def __init__(__pydantic_self__, **data: Any) -> None:
        super().__init__(**data)
        if __pydantic_self__.sample_args is None:
            __pydantic_self__.sample_args = ModelSampleArgs()
        if __pydantic_self__.gen_args is None:
            __pydantic_self__.gen_args = ModelGenArgs()

    def to_dict(self):
        return self.dict()
    
    def toJSON(self):
        return json.dumps(self.dict())

class ModelSerializer(json.JSONEncoder):
    """Class to serialize ModelGenRequest to JSON.
    """
    def default(self, o):
        if hasattr(o, 'toJSON'):
            return o.toJSON()
        return json.JSONEncoder.default(self, o)

class ModelProvider:
    """Abstract class for model providers that provide access to generative AI models.
    """
    def __init__(self, endpoint_url: str, **kwargs):
        """Constructor for ModelProvider.

        :param endpoint_url: The URL of the endpoint.
        :type endpoint_url: str
        """
        self.endpoint_url = endpoint_url
        self.kwargs = kwargs
        if 'args' not in kwargs:
            raise Exception('default args is required')
        self.auth()
    
    def auth(self):
        """Authenticate with the ModelProvider's endpoint.

        :raises NotImplementedError: If the authentication method is not implemented.
        """
        raise NotImplementedError('auth method is required')

    def generate(self, args):
        """Generate a response from the ModelProvider's endpoint.
        
        :param args: The arguments to pass to the endpoint.
        :type args: dict
        :raises NotImplementedError: If the generate method is not implemented.
        """
        raise NotImplementedError('generate method is required')
    
    async def generate_async(self, args):
        """Generate a response from the ModelProvider's endpoint asynchronously.
        
        :param args: The arguments to pass to the endpoint.
        :type args: dict
        :raises NotImplementedError: If the generate method is not implemented.
        """
        raise NotImplementedError('generate method is required')
    
    async def hidden_async(self, model, text, layer):
        """Fetch a layer's hidden states from text.
        
        :param model: The model to extract hidden states from.
        :type model: str
        :param text: The text to use.
        :type text: str
        :param layer: The layer to fetch the hidden states from.
        :type layer: int
        """

        raise NotImplementedError('hidden_async method is required')

    async def image_label_async(self, model, url, labels):
        """Classify an image with labels (CLIP).

        :param model: The model to use for classification.
        :type model: str
        :param url: The image URL to use.
        :type url: str
        :param labels: The labels to use.
        :type labels: list
        """

        raise NotImplementedError('image_label_async method is required')

    def should_respond(self, context, name):
        """Determine if the ModelProvider predicts that the name should respond to the given context.

        :param context: The context to use.
        :type context: str
        :param name: The name to check.
        :type name: str
        :raises NotImplementedError: If the should_respond method is not implemented.
        """
        raise NotImplementedError('should_respond method is required')
    
    def should_respond_async(self, context, name):
        """Determine if the ModelProvider predicts that the name should respond to the given context asynchronously.

        :param context: The context to use.
        :type context: str
        :param name: The name to check.
        :type name: str
        :raises NotImplementedError: If the should_respond method is not implemented.
        """
        raise NotImplementedError('should_respond method is required')

    def response(self, context):
        """Generate a response from the ModelProvider's endpoint.
            
        :param context: The context to use.
        :type context: str
        :raises NotImplementedError: If the response method is not implemented.
        """
        raise NotImplementedError('response method is required')
    
    def response_async(self, context):
        """Generate a response from the ModelProvider's endpoint asynchronously.
            
        :param context: The context to use.
        :type context: str
        :raises NotImplementedError: If the response method is not implemented.
        """
        raise NotImplementedError('response method is required')

class Sukima_ModelProvider(ModelProvider):
    def __init__(self, endpoint_url: str, **kwargs):
        """Constructor for Sukima_ModelProvider.

        :param endpoint_url: The URL for the Sukima endpoint.
        :type endpoint_url: str
        """

        super().__init__(endpoint_url, **kwargs)
        self.auth()
    
    def auth(self):
        """Authenticate with the Sukima endpoint.

        :raises Exception: If the authentication fails.
        """

        if 'username' not in self.kwargs and 'password' not in self.kwargs:
            raise Exception('username, password, and or token are not in kwargs')
        
        try:
            r = requests.post(f'{self.endpoint_url}/api/v1/users/token', data={'username': self.kwargs['username'], 'password': self.kwargs['password']})
        except Exception as e:
            raise e
        if r.status_code == 200:
            self.token = r.json()['access_token']
        else:
            raise Exception(f'Could not authenticate with Sukima. Error: {r.text}')
        
    def conv_listobj_to_listdict(self, list_objects): 
        """Convert the elements of a list to a dictionary for JSON compatability.

        :param list_objects: The list. 
        :type list_objects: list
        :return: A list which has it's elements converted to dictionaries.
        :rtype: list
        """

        list_dict = []
        for object in list_objects:
            list_dict.append(vars(object))
        return list_dict 
    
    def generate(self, args: ModelGenRequest):
        """Generate a response from the Sukima endpoint.
        
        :param args: The arguments to pass to the endpoint.
        :type args: dict
        :return: The response from the endpoint.
        :rtype: str
        :raises Exception: If the request fails.
        """

        args = {
            'model': args.model,
            'prompt': args.prompt,
            'sample_args': {
                'temp': args.sample_args.temp,
                'top_p': args.sample_args.top_p,
                'top_a': args.sample_args.top_a,
                'top_k': args.sample_args.top_k,
                'typical_p': args.sample_args.typical_p,
                'tfs': args.sample_args.tfs,
                'rep_p': args.sample_args.rep_p,
                'rep_p_range': args.sample_args.rep_p_range,
                'rep_p_slope': args.sample_args.rep_p_slope,
                'bad_words': args.sample_args.bad_words,
                'logit_biases': self.conv_listobj_to_listdict(args.sample_args.logit_biases)
            },
            'gen_args': {
                'max_length': args.gen_args.max_length,
                'max_time': args.gen_args.max_time,
                'min_length': args.gen_args.min_length,
                'eos_token_id': args.gen_args.eos_token_id,
                'logprobs': args.gen_args.logprobs,
                'best_of': args.gen_args.best_of
            }
        }
        try:
            r = requests.post(f'{self.endpoint_url}/api/v1/models/generate', data=json.dumps(args), headers={'Authorization': f'Bearer {self.token}'})
        except Exception as e:
            raise e
        if r.status_code == 200:
            return r.json()['output'][len(args['prompt']):]
        else:
            raise Exception(f'Could not generate text with Sukima. Error: {r.json()}')
    
    async def generate_async(self, args: ModelGenRequest):
        """Generate a response from the Sukima endpoint asynchronously.
        
        :param args: The arguments to pass to the endpoint.
        :type args: dict
        :return: The response from the endpoint.
        :rtype: str
        :raises Exception: If the request fails.
        """ 
  
        args = {
            'model': args.model,
            'prompt': args.prompt,
            'sample_args': {
                'temp': args.sample_args.temp,
                'top_p': args.sample_args.top_p,
                'top_a': args.sample_args.top_a,
                'top_k': args.sample_args.top_k,
                'typical_p': args.sample_args.typical_p,
                'tfs': args.sample_args.tfs,
                'rep_p': args.sample_args.rep_p,
                'rep_p_range': args.sample_args.rep_p_range,
                'rep_p_slope': args.sample_args.rep_p_slope,
                'bad_words': args.sample_args.bad_words,
                'logit_biases': self.conv_listobj_to_listdict(args.sample_args.logit_biases)  
            },
            'gen_args': {
                'max_length': args.gen_args.max_length,
                'max_time': args.gen_args.max_time,
                'min_length': args.gen_args.min_length,
                'eos_token_id': args.gen_args.eos_token_id,
                'logprobs': args.gen_args.logprobs,
                'best_of': args.gen_args.best_of
            }
        }
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(f'{self.endpoint_url}/api/v1/models/generate', json=args, headers={'Authorization': f'Bearer {self.token}'}) as resp:
                    if resp.status == 200:
                        js = await resp.json()
                        return js['output'][len(args['prompt']):]
                    else:
                        raise Exception(f'Could not generate response. Error: {await resp.text()}')
            except Exception as e:
                raise e

    async def hidden_async(self, model, text, layer):
        """Fetch a layer's hidden states from text.

        :param model: The model to extract hidden states from.
        :type model: str
        :param text: The text to use.
        :type text: str
        :param layer: The layer to fetch the hidden states from.
        :type layer: int
        """

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(f'{self.endpoint_url}/api/v1/models/hidden', json={'model': model, 'prompt': text, 'layers': [layer]}, headers={'Authorization': f'Bearer {self.token}'}) as resp:
                    if resp.status == 200:
                        return (await resp.json())[f'{layer}'][0]
                    else:
                        raise Exception(f'Could not fetch hidden states. Error: {await resp.text()}')
            except Exception as e:
                raise e

    async def image_label_async(self, model, url, labels):
        """Classify an image with labels (CLIP).

        :param model: The model to use for classification.
        :type model: str
        :param url: The image URL to use.
        :type url: str
        :param labels: The labels to use.
        :type labels: list
        """

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(f'{self.endpoint_url}/api/v1/models/classify', json={'model': model, 'prompt': url, 'labels': labels}, headers={'Authorization': f'Bearer {self.token}'}) as resp:
                    if resp.status == 200:
                        return (await resp.json())
                    else:
                        raise Exception(f'Could not classify image. Error: {await resp.text()}')
            except Exception as e:
                raise e
            
    def should_respond(self, context, name):
        """Determine if the Sukima endpoint predicts that the name should respond to the given context.

        :param context: The context to use.
        :type context: str
        :param name: The name to check.
        :type name: str
        :return: Whether or not the name should respond to the given context.
        :rtype: bool
        """

        phrase_bias = ModelPhraseBiasArgs
        phrase_bias.sequences = [name]
        phrase_bias.bias = 1.5
        phrase_bias.ensure_sequence_finish = True
        phrase_bias.generate_once = True

        args = copy.deepcopy(self.kwargs['args'])
        args.prompt = context
        args.gen_args.max_length = 10
        args.gen_args.eos_token_id = 25
        args.gen_args.best_of = None
        args.sample_args.temp = 0.25
        args.sample_args.rep_p = None
        args.sample_args.rep_p_range = None
        args.sample_args.rep_p_slope = None
        args.sample_args.phrase_biases = phrase_bias
        response = self.generate(args)
        if name in response:
            return True
        else:
            return False

    async def should_respond_async(self, context, name):
        """Determine if the Sukima endpoint predicts that the name should respond to the given context asynchronously.

        :param context: The context to use.
        :type context: str
        :param name: The name to check.
        :type name: str
        :return: Whether or not the name should respond to the given context.
        :rtype: bool
        """
        phrase_bias = ModelPhraseBiasArgs
        phrase_bias.sequences = [name]
        phrase_bias.bias = 1.5
        phrase_bias.ensure_sequence_finish = True
        phrase_bias.generate_once = True

        args = copy.deepcopy(self.kwargs['args'])
        args.prompt = context
        args.gen_args.max_length = 10
        args.gen_args.eos_token_id = 25
        args.gen_args.best_of = None
        args.sample_args.temp = 0.25
        args.sample_args.rep_p = None
        args.sample_args.rep_p_range = None
        args.sample_args.rep_p_slope = None
        args.sample_args.phrase_biases = phrase_bias
        response = await self.generate_async(args)
        if response.startswith(name):
            return True
        else:
            return False

    def response(self, context):
        """Generate a response from the Sukima endpoint.

        :param context: The context to use.
        :type context: str
        :return: The response from the endpoint.
        :rtype: str
        """
        args = self.kwargs['args']
        args.prompt = context
        args.gen_args.eos_token_id = 198
        args.gen_args.min_length = 1
        response = self.generate(args)
        return response

    async def response_async(self, context):
        """Generate a response from the Sukima endpoint asynchronously.

        :param context: The context to use.
        :type context: str
        :return: The response from the endpoint.
        :rtype: str
        """
        args = self.kwargs['args']
        args.prompt = context
        args.gen_args.eos_token_id = 198
        args.gen_args.min_length = 1
        response = await self.generate_async(args)
        return response

class TextSynth_ModelProvider(ModelProvider):
    def __init__(self, endpoint_url: str = 'https://api.textsynth.com', **kwargs):
        """Constructor for TextSynth_ModelProvider.

        :param endpoint_url: The URL for the TextSynth endpoint.
        :type endpoint_url: str
        :param token: The API token for the TextSynth endpoint.
        :type token: str
        """
        super().__init__(endpoint_url, **kwargs)
        self.auth()
    
    def auth(self):
        """Authenticate with the TextSynth endpoint.

        :raises Exception: If the authentication fails.
        """
        if 'token' not in self.kwargs:
            raise Exception('token is not in kwargs')
        self.token = self.kwargs['token']
    
    async def generate_async(self, args: ModelGenRequest) -> str:
        """Generate a response from the TextSynth endpoint.
        
        :param args: The arguments to pass to the endpoint.
        :type args: dict
        :return: The response from the endpoint.
        :rtype: str
        :raises Exception: If the request fails.
        """
        model = args.model
        args = {
            'prompt': args.prompt,
            'max_tokens': args.gen_args.max_length,
            'temperature': args.sample_args.temp,
            'top_p': args.sample_args.top_p,
            'top_k': args.sample_args.top_k,
            'stop': tokenizer.decode(args.gen_args.eos_token_id)
        }
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(f'{self.endpoint_url}/v1/engines/{model}/completions', json=args, headers={'Authorization': f'Bearer {self.token}'}) as resp:
                    if resp.status == 200:
                        js = await resp.json()
                        return js['text']
                    else:
                        raise Exception(f'Could not generate response. Error: {resp.text()}')
            except Exception as e:
                raise e

    async def should_respond_async(self, context, name):
        """Determine if the TextSynth endpoint predicts that the name should respond to the given context asynchronously.

        :param context: The context to use.
        :type context: str
        :param name:
        :type name: str
        :return: Whether or not the name should respond to the given context.
        :rtype: bool
        """
        args = copy.deepcopy(self.kwargs['args'])
        args.prompt = context
        args.gen_args.max_length = 10
        args.sample_args.temp = 0.25
        response = await self.generate_async(args)
        if response.startswith(name):
            return True
        else:
            return False
    
    async def response_async(self, context):
        """Generate a response from the TextSynth endpoint asynchronously.

        :param context: The context to use.
        :type context: str
        :return: The response from the endpoint.
        :rtype: str
        """
        args = self.kwargs['args']
        args.prompt = context
        args.gen_args.eos_token_id = 198
        args.gen_args.min_length = 1
        response = await self.generate_async(args)
        return response
