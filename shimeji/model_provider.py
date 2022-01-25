import requests
import json

class ModelProvider:
    def __init__(self, endpoint_url: str, **kwargs):
        self.endpoint_url = endpoint_url
        self.kwargs = kwargs
        if 'args' not in kwargs:
            raise Exception('default args is required')
        self.auth()
    
    def auth(self):
        pass

    def generate(self, args):
        pass

    def should_respond(self, context, name):
        pass

    def response(self, context):
        pass

class Sukima_ModelProvider(ModelProvider):
    def __init__(self, endpoint_url: str, **kwargs):
        super().__init__(endpoint_url, **kwargs)
        self.auth()
    
    def auth(self):
        # check if username and password are not in kwargs, raise exception if token is not in kwargs too
        if 'username' not in self.kwargs and 'password' not in self.kwargs:
            raise Exception('username, password, and or token are not in kwargs')
        
        try:
            r = requests.post(f'{self.endpoint_url}/api/v1/users/token', data={'username': self.kwargs['username'], 'password': self.kwargs['password']}, timeout=2.0)
        except Exception as e:
            raise e
        if r.status_code == 200:
            self.token = r.json()['access_token']
        else:
            raise Exception(f'Could not authenticate with Sukima. Error: {r.text}')
        
    def generate(self, args):
        try:
            r = requests.post(f'{self.endpoint_url}/api/v1/models/generate', data=json.dumps(args), headers={'Authorization': f'Bearer {self.token}'}, timeout=30.0)
        except Exception as e:
            raise e
        if r.status_code == 200:
            return r.json()['output'][len(args['prompt']):]
        else:
            raise Exception(f'Could not generate text with Sukima. Error: {r.json()}')
    
    def should_respond(self, context, name):
        args = self.kwargs['args'] # get default args
        args['prompt'] = context
        args['gen_args']['eos_token_id'] = 25
        args['sample_args']['temp'] = 0.25
        args['sample_args']['phrase_biases'] = [{'sequences': [name], 'bias': 1.5, 'ensure_sequence_finish': True, 'generate_once': True}]
        response = self.generate(args)
        if response.startswith(name):
            return True
        else:
            return False

    def response(self, context):
        args = self.kwargs['args']
        args['prompt'] = context
        args['gen_args']['eos_token_id'] = 198
        args['gen_args']['min_length'] = 1
        response = self.generate(args)
        return response
