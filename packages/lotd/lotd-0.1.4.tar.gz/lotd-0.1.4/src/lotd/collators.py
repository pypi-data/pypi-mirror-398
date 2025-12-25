import torch
from torch.nn.utils.rnn import pad_sequence
from typing import Union, Dict, List, Callable, Literal, Any


class PadCollator:
    """
    Collator which converts inputs into pytorch tensors and applies padding.
    """

    __slots__ = ("pad_id", "pre", "post", "pad_fn", "ignore_columns")

    def __init__(
        self,
        pad_id: int,
        pre: Union[Callable, None] = None,
        post: Union[Callable, None] = None,
        padding_side: Literal["right", "left"] = "right",
        ignore_columns: List[str] = [],
    ) -> None:
        """
        Initializes the collator.

        Args:
            pad_id: pad token id used for padding.
            pre: callable that accepts list of dicts where every key is a dataset feature, modifies it and returns it back.
            post: callable that accepts a dict of tensors of a form `{"input_ids": ..., "attention_mask": ..., "prompt_mask": ...}`, modifies it and returns it back.
            padding_side: can be right or left.
            ignore_columns: columns to be excluded.
        """
        self.pad_fn: Callable = lambda batch, column, pad: pad_sequence(
            [torch.tensor(x[column]) for x in batch],
            batch_first=True,
            padding_value=pad,
            padding_side=padding_side,
        )
        self.pre = pre
        self.post = post
        self.pad_id: int = pad_id
        self.ignore_columns = ignore_columns

    def __call__(self, batch: List[Dict[str, Any]]) -> Dict[str, torch.Tensor]:
        """
        Collates inputs.

        Args:
            batch: list of dicts where each key is a feature.

        Returns:
            a dict of padded tensors of form `{"input_ids": ..., "attention_mask": ..., "prompt_mask": ...}`.
        """
        # Apply pre-processing
        if self.pre != None:
            batch = self.pre(batch)
        # Pad inputs
        # Use temp pad ids (-42) to prevent excluding intentional pad tokens
        input_ids = self.pad_fn(batch, "input_ids", -42)
        prompt_mask = self.pad_fn(batch, "prompt_mask", 1)
        # Generate attention_mask
        attention_mask = torch.ones_like(input_ids)
        attention_mask[input_ids == -42] = 0
        # Set proper pad ids
        input_ids[input_ids == -42] = self.pad_id
        # Apply post
        output = {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "prompt_mask": prompt_mask,
        }
        # Add other columns
        processed_columns = output.keys()
        other_columns = batch[0].keys()
        for column in other_columns:
            if column in processed_columns or column in self.ignore_columns:
                continue
            output[column] = []
            for sample in batch:
                output[column].append(sample[column])
        # Apply post-processing
        if self.post != None:
            output = self.post(output)
        return output
