from typing import List
import numpy as np
import base64
import random
import copy

from shimeji.memorystore_provider import Memory, MemoryStoreProvider

def numpybin_to_str(arr: np.array) -> str:
    return base64.a85encode(arr.tobytes()).decode()

def array_to_str(arr: list) -> str:
    return base64.a85encode(np.array(arr, dtype=np.float32).tobytes()).decode()

def str_to_numpybin(string: str) -> np.array:
    return np.frombuffer(base64.a85decode(string), dtype=np.float32)

def cosine_distance(a: np.array, b: np.array, factor=1000.0, epsilon=1e-6) -> float:
    return np.sum(np.sqrt((np.abs(b - a) / factor) + epsilon))

def memory_sort(now: Memory, then: List[Memory], top_k: int = 256, cutoff_idx: int = 128, max_samples: int = 512) -> List[Memory]:
    """
    Sort memories based on their cosine distance to the current memory.
    """

    # get most recent memories
    if (cutoff_idx is not None and max_samples is not None) and (len(memories) > cutoff_idx + max_samples):
        memories = then[-cutoff_idx:]
        memories.extend(random.sample(then[:len(then)-cutoff_idx], max_samples))
    else:
        memories = then

    return sorted(memories, key=lambda x: cosine_distance(str_to_numpybin(now.encoding), str_to_numpybin(x.encoding)))[:top_k]

def memory_context(now: Memory, then: List[Memory], short_term=20, long_term=10) -> str:
    """
    Generate a context based on the current memory and the memories that are similar to it.

    :param now: The current memory.
    :type now: Memory
    :param then: The past memories.
    :type then: List[Memory]
    :param short_term: The number of recent memories to exclude from the context.
    :type short_term: int
    :param long_term: The number of memories to include in the context.
    :type long_term: int
    """
    if short_term is not None:
        memories = memory_sort(now, then[:-short_term], long_term)
    else:
        memories = memory_sort(now, then, long_term)
    memories.reverse()

    text = ""
    for memory in memories:
        # check if memory.text starts with a space, if so, remove it
        if memory.text.startswith(" "):
            memory.text = memory.text[1:]
        text += f'{memory.author}: {memory.text}\n'

    return text
