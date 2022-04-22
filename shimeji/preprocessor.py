from .util import *
from .memory import memory_context, memory_sort
from .memorystore_provider import MemoryStoreProvider

class Preprocessor:
    """Abstract class for preprocessors.
    """
    def __call__(self, context: str, is_respond: bool, name: str) -> str:
        """Process the given context before the ModelProvider is called.

        :param context: The context to preprocess.
        :type context: str
        :param is_respond: Whether the context is being built for a chatbot response.
        :type is_respond: bool
        :param name: The name of the chatbot.
        :type name: str
        :return: The processed context.
        :rtype: str
        """
        raise NotImplementedError(f'{self.__class__} is an abstract class')

class MemoryPreprocessor(Preprocessor):
    """A Preprocessor that builds the long-term memory context."""
    def __init__(self, memorystore: MemoryStoreProvider, short_term: int, long_term: int):
        """Constructor for MemoryPreprocessor which uses the most recent memory as the present memory to build the long-term memory context.

        :param memorystore: The memory store to use.
        :type memorystore: MemoryStoreProvider
        :param short_term: The number of short-term memories to use which will be left out of the long-term memory context.
        :type short_term: int
        :param long_term: The number of long-term memories to use.
        :type long_term: int
        """
        self.memorystore = memorystore
        self.short_term = short_term
        self.long_term = long_term
    
    def __call__(self, context: str, is_respond: bool, name: str) -> str:
        memories = self.memorystore.get(created_after=0)
        now = memories[-1]
        memories.remove(now)
        long_term_context = memory_context(now, memories, short_term=self.short_term, long_term=self.long_term)
        return long_term_context + context

class ContextPreprocessor(Preprocessor):
    """A Preprocessor that builds a context from a list of ContextEntry objects."""
    def __init__(self, token_budget=1024):
        """Initialize a ContextPreprocessor.

        :param token_budget: The maximum number of tokens that can be used in the context, defaults to 1024.
        :type token_budget: int, optional
        """
        self.token_budget = token_budget
        self.entries = []
    
    def add_entry(self, entry):
        """Add a ContextEntry to the ContextPreprocessor.

        :param entry: The ContextEntry to add.
        :type entry: ContextEntry
        """
        self.entries.append(entry)
    
    def del_entry(self, entry):
        """Delete a ContextEntry from the ContextPreprocessor.

        :param entry: The ContextEntry to delete.
        :type entry: ContextEntry
        """
        self.entries.remove(entry)
    
    # return true if key is found in an entry's text
    def key_lookup(self, entry_a, entry_b):
        """Check if a ContextEntry's key is found in an entry's text.

        :param entry_a: The ContextEntry to check.
        :type entry_a: ContextEntry
        :param entry_b: Another ContextEntry to check.
        :type entry_b: ContextEntry
        :return: Whether the key is found in the text.
        :rtype: bool
        """
        for i in entry_b.keys:
            if i == '':
                continue
            if i.lower() in entry_a.text.lower():
                return True
        return False
    
    # recursive function that searches for other entries that are activated
    def cascade_lookup(self, entry, nest=0):
        """Search for other entries that are activated by a given entry.

        :param entry: The entry to recursively search for other entries in.
        :type entry: ContextEntry
        :param nest: The maximum amount of recursion to perform, defaults to 0.
        :type nest: int, optional
        :return: A list of other entries that are activated by the given entry.
        :rtype: list
        """
        cascaded_entries = []
        if nest > 3:
            return []
        for i in self.entries:
            if self.key_lookup(entry, i):
                # check if i activates entry to prevent infinite loop
                if self.key_lookup(i, entry):
                    cascaded_entries.append(i)
                    continue
                for j in self.cascade_lookup(i, nest+1):
                    cascaded_entries.append(j)
        return cascaded_entries

    # handles cases where elements are added to the end of a list using list.insert
    def ordinal_pos(self, position, length):
        if position < 0:
            return length + 1 + position
        return position
    
    def context(self, budget=1024):
        """Build the context from the ContextPreprocessor's entries.

        :param budget: The maximum number of tokens that can be used in the context, defaults to 1024.
        :type budget: int, optional
        :return: The built context.
        :rtype: str
        """
        # sort self.entries by insertion_order
        self.entries.sort(key=lambda x: x.insertion_order, reverse=True)
        activated_entries = []

        # Get entries activated by default
        for i in self.entries:
            if i.forced_activation:
                if i.cascading_activation:
                    for j in self.cascade_lookup(i):
                        activated_entries.append(j)
                    activated_entries.append(i)
                else:
                    activated_entries.append(i)
            if i.insertion_position > 0 or i.insertion_position < 0:
                if i.reserved_tokens == 0:
                    i.reserved_tokens = len(tokenizer.encode(i.text))
        
        activated_entries = list(set(activated_entries))
        # sort activated_entries by insertion_order
        activated_entries.sort(key=lambda x: x.insertion_order, reverse=True)

        newctx = []
        for i in activated_entries:
            reserved = 0
            if i.reserved_tokens > 0:
                len_tokens = len(tokenizer.encode(i.text))
                if len_tokens < i.reserved_tokens:
                    budget -= len_tokens
                else:
                    budget -= i.reserved_tokens
                if len_tokens > i.reserved_tokens:
                    reserved = i.reserved_tokens
                else:
                    reserved = len_tokens
            
            text = i.get_text(budget + reserved, self.token_budget)
            ctxtext = text.splitlines(keepends=False)
            trimmed_tokenized = tokenizer.encode(text)
            budget -= len(trimmed_tokenized) - reserved
            ctxinsertion = i.insertion_position

            before = []
            after = []

            if i.insertion_position < 0:
                ctxinsertion += 1
                if len(newctx) + ctxinsertion >= 0:
                    before = newctx[0:len(newctx)+ctxinsertion]
                    after = newctx[len(newctx)+ctxinsertion:]
                else:
                    before = []
                    after = newctx[0:]
            else:
                before = newctx[0:ctxinsertion]
                after = newctx[ctxinsertion:]

            newctx = []

            for bIdx in range(len(before)):
                newctx.append(before[bIdx])
            for cIdx in range(len(ctxtext)):
                newctx.append(ctxtext[cIdx])
            for aIdx in range(len(after)):
                newctx.append(after[aIdx])
        return '\n'.join(newctx)

    def __call__(self, context: str, is_respond: bool, name: str) -> str:
        """Build the context from the ContextPreprocessor's entries.

        :param context: The context to build the context from.
        :type context: str
        :param is_respond: Whether the context is being built for a chatbot response.
        :type is_respond: bool
        :param name: The name of the chatbot.
        :type name: str
        :return: The processed context.
        :rtype: str
        """

        if is_respond:
            main_entry = ContextEntry(text=context, suffix=f'\n{name}:', reserved_tokens=512, insertion_order=0, trim_direction=TRIM_DIR_TOP, forced_activation=True, cascading_activation=True, insertion_type=INSERTION_TYPE_NEWLINE, insertion_position=-1)
        else:
            main_entry = ContextEntry(text=context, suffix='\n', reserved_tokens=512, insertion_order=0, trim_direction=TRIM_DIR_TOP, forced_activation=True, cascading_activation=True, insertion_type=INSERTION_TYPE_NEWLINE, insertion_position=-1)
        self.add_entry(main_entry)
        constructed_context = self.context()
        self.del_entry(main_entry)
        return constructed_context