import sys
from typing import List, Union

class LengthFilter:
    """
    Filters datasets by max and min length of input_ids.
    """

    __slots__ = ("max_length", "min_length")

    def __init__(self, min_length: int = 0, max_length: Union[int, None] = None) -> None:
        """
        Initializes the collator.

        Args:
            min_length: lowest number of tokens.
            max_length: highest number of tokens.
        """
        self.max_length = sys.maxsize if max_length == None else max_length
        self.min_length = min_length


    def __call__(self, input_ids: List[List[int]]) -> List[bool]:
        """
        Processes a batch of input_ids.
        """
        return [len(x) <= self.max_length and len(x) > self.min_length for x in input_ids]

