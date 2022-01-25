class Postprocessor:
    def __call__(self, context: str) -> str:
        raise NotImplementedError(f'{self.__class__} is an abstract class')