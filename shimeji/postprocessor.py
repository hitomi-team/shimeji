class Postprocessor:
    """Abstract class for postprocessors.
    """
    def __call__(self, context: str) -> str:
        """Process the given context before the ModelProvider is called.

        :param context: The context to preprocess.
        :type context: str
        :raises NotImplementedError: If the postprocessor is not implemented.
        :return: The processed context.
        :rtype: str
        """
        raise NotImplementedError(f'{self.__class__} is an abstract class')

class NewlinePrunerPostprocessor:
    """Postprocessor that removes newlines.
    """
    def __call__(self, context: str) -> str:
        """Process the given context.

        :param context: The context to process.
        :type context: str
        :return: The processed context which has no trailing newlines.
        :rtype: str
        """
        return context.rstrip('\n')