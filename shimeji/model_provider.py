import requests
import json

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

    def should_respond(self, context, name):
        """Determine if the ModelProvider predicts that the name should respond to the given context.

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
            r = requests.post(f'{self.endpoint_url}/api/v1/users/token', data={'username': self.kwargs['username'], 'password': self.kwargs['password']}, timeout=2.0)
        except Exception as e:
            raise e
        if r.status_code == 200:
            self.token = r.json()['access_token']
        else:
            raise Exception(f'Could not authenticate with Sukima. Error: {r.text}')
        
    def generate(self, args):
        """Generate a response from the Sukima endpoint.
        
        :param args: The arguments to pass to the endpoint.
        :type args: dict
        :return: The response from the endpoint.
        :rtype: str
        :raises Exception: If the request fails.
        """
        try:
            r = requests.post(f'{self.endpoint_url}/api/v1/models/generate', data=json.dumps(args), headers={'Authorization': f'Bearer {self.token}'}, timeout=30.0)
        except Exception as e:
            raise e
        if r.status_code == 200:
            return r.json()['output'][len(args['prompt']):]
        else:
            raise Exception(f'Could not generate text with Sukima. Error: {r.json()}')
    
    def should_respond(self, context, name):
        """Determine if the Sukima endpoint predicts that the name should respond to the given context.

        :param context: The context to use.
        :type context: str
        :param name: The name to check.
        :type name: str
        :return: Whether or not the name should respond to the given context.
        :rtype: bool
        """
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
        """Generate a response from the Sukima endpoint.

        :param context: The context to use.
        :type context: str
        :return: The response from the endpoint.
        :rtype: str
        """
        args = self.kwargs['args']
        args['prompt'] = context
        args['gen_args']['eos_token_id'] = 198
        args['gen_args']['min_length'] = 1
        response = self.generate(args)
        return response
