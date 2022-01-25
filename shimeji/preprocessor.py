from .util import *

class Preprocessor:
    def __call__(self, context: str) -> str:
        raise NotImplementedError(f'{self.__class__} is an abstract class')

class ContextPreprocessor(Preprocessor):
    def __init__(self, token_budget=1024):
        self.token_budget = token_budget
        self.entries = []
    
    def add_entry(self, entry):
        self.entries.append(entry)
    
    def del_entry(self, entry):
        self.entries.remove(entry)
    
    # return true if key is found in an entry's text
    def key_lookup(self, entry_a, entry_b):
        for i in entry_b.keys:
            if i == '':
                continue
            if i.lower() in entry_a.text.lower():
                return True
        return False
    
    # recursive function that searches for other entries that are activated
    def cascade_lookup(self, entry, nest=0):
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

    def __call__(self, context: str) -> str:
        self.add_entry(ContextEntry(text=context, suffix='\n', reserved_tokens=512, insertion_order=0, trim_direction=TRIM_DIR_TOP, forced_activation=True, cascading_activation=True, insertion_type=INSERTION_TYPE_NEWLINE, insertion_position=-1))
        return self.context()