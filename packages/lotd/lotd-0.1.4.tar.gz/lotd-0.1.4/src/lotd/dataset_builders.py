from typing import Union, Callable, Tuple
from torch import batch_norm
from transformers import PreTrainedTokenizer, PreTrainedTokenizerFast
from datasets import load_dataset, concatenate_datasets
from torch.utils.data import DataLoader
from .processors import ChatTokenizer, TextTokenizer
from .filters import LengthFilter
from .utils import load_cached, get_loaders, strip_features
from .collators import PadCollator

"""
Pre-processing functions for some standard datasets
"""


def build_dataset(preprocess_func):
    """
    Decorator for building dataloaders. Processes or tries loading the dataset if `cache_path` is specified, creates new PadCollator, and returns dataloaders.
    """

    def wrapper(*args, **kwargs):
        cache_path = kwargs.get("cache_path", None)
        # Load from cache
        if cache_path != None:
            ds = load_cached(cache_path, lambda: preprocess_func(*args, **kwargs))
        else:
            ds = preprocess_func(*args, **kwargs)

        # Split and create dataloaders
        tokenizer = kwargs.get("tokenizer", None)
        tokenizer = args[0] if tokenizer == None and len(args) > 0 else None
        assert tokenizer != None
        pre = kwargs.get("pre", None)
        post = kwargs.get("post", None)
        collate_fn = PadCollator(pad_id=tokenizer.pad_token_id, pre=pre, post=post)  # type: ignore

        # Return dataloaders
        batch_size = kwargs.get("batch_size", 16)
        seed = kwargs.get("seed", 42)
        return get_loaders(dataset=ds, collate_fn=collate_fn, batch_size=batch_size, seed=seed)  # type: ignore

    return wrapper


@build_dataset
def alpaca(
    tokenizer: Union[PreTrainedTokenizer, PreTrainedTokenizerFast],
    cache_path: Union[str, None] = None,
    max_length: int = 512,
    batch_size: int = 16,
    seed: int = 42,
    pre: Union[Callable, None] = None,
    post: Union[Callable, None] = None,
) -> Tuple[DataLoader, DataLoader, DataLoader]:
    """
    Downloads and Pre-processes [Alpaca](https://huggingface.co/datasets/tatsu-lab/alpaca) dataset for instruction fine-tuning.

    Args:
        tokenizer: transformers tokenizer with `chat_template` parameter set.
        cache_path: path to load/save dataset.
        max_length: maximum sequence length for filter.
        batch_size: dataloaders batch size.
        seed: splitting and shuffling seed.
        pre: see `PadCollator`.
        post: see `PadCollator`.

    Returns:
        a tuple of train, validation and test dataloaders.
    """

    dataset_name = "tatsu-lab/alpaca"
    print(f"Loading {dataset_name} dataset (train split)...")
    ds = load_dataset(dataset_name, split="train")
    print("Shuffling dataset...")
    ds = ds.shuffle(seed=seed)
    print("Processing prompts...")
    ds = ds.map(
        lambda instructions, inputs: {
            "prompt": [
                f"{instructions[i]}\n{inputs[i]}" if inputs[i] else instructions[i]
                for i in range(len(instructions))
            ]
        },
        input_columns=["instruction", "input"],
        batched=True,
        batch_size=512,
    )
    print("Tokenization...")
    ds = ds.map(
        ChatTokenizer(tokenizer),
        input_columns=["prompt", "output"],
        batched=True,
        batch_size=512,
    )
    print("Removing features...")
    ds = strip_features(ds)  # type: ignore
    print("Filtering...")
    old_size = len(ds)  # type: ignore
    ds = ds.filter(
        LengthFilter(min_length=0, max_length=max_length),
        input_columns=["input_ids"],
        batched=True,
        batch_size=512,
    )
    new_size = len(ds)  # type: ignore
    print(
        f"{old_size - new_size} samples were removed ({(1.0-new_size/old_size)*100:.2f}%)"
    )
    return ds # type: ignore


@build_dataset
def tinystories(
    tokenizer: Union[PreTrainedTokenizer, PreTrainedTokenizerFast],
    template: str = "[CLS]{{tex}}[SEP]",
    cache_path: Union[str, None] = None,
    max_length: int = 512,
    batch_size: int = 16,
    seed: int = 42,
    pre: Union[Callable, None] = None,
    post: Union[Callable, None] = None,
) -> Tuple[DataLoader, DataLoader, DataLoader]:
    """
    Downloads and Pre-processes [TinyStories](https://huggingface.co/datasets/roneneldan/TinyStories) dataset for language modeling. `train` and `validation` are merged, shuffled and re-split with 80%/10%/10% ratio.

    Args:
        tokenizer: transformers tokenizer.
        template: prompt template with `{{text}}` placeholder.
        cache_path: path to load/save dataset.
        max_length: maximum sequence length for truncation.
        batch_size: dataloaders batch size.
        seed: splitting and shuffling seed.
        pre: see `PadCollator`.
        post: see `PadCollator`.

    Returns:
        a tuple of train, validation and test dataloaders.
    """

    dataset_name = "roneneldan/TinyStories"
    print(f"Loading {dataset_name} dataset (all splits)...")
    ds = load_dataset(dataset_name)
    print("Merging train and validation splits...")
    ds = concatenate_datasets([ds["train"], ds["validation"]])  # type:ignore
    print("Shuffling dataset...")
    ds = ds.shuffle(seed=seed)
    print("Tokenization...")
    ds = ds.map(
        TextTokenizer(tokenizer, template=template, max_length=max_length),
        input_columns=["text"],
        batched=True,
        batch_size=512,
    )
    print("Removing features...")
    ds = strip_features(ds)  # type: ignore
    print("Filtering...")
    old_size = len(ds)  # type: ignore
    ds = ds.filter(
        LengthFilter(min_length=0, max_length=max_length),
        input_columns=["input_ids"],
        batched=True,
        batch_size=512,
    )
    new_size = len(ds)  # type: ignore
    print(
        f"{old_size - new_size} samples were removed ({(1.0-new_size/old_size)*100:.2f}%)"
    )
    return ds # type: ignore
