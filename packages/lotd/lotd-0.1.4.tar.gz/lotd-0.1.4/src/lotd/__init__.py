"""
LOTD - Lord of the Datasets
Efficient NLP dataset preprocessing library.
"""

import importlib.metadata
from . import dataset_builders as datasets
from .collators import PadCollator
from .processors import TextTokenizer, ChatTokenizer
from .filters import LengthFilter
from .utils import split_dataset, load_cached, get_loaders, strip_features
from .templates import generate_chat_template, format_chat

try:
    __version__ = importlib.metadata.version("lotd")
except importlib.metadata.PackageNotFoundError:
    # Fallback for development/editable installs
    __version__ = "0.0.0"

__all__ = [
    "datasets",
    "PadCollator",
    "TextTokenizer",
    "ChatTokenizer",
    "LengthFilter",
    "split_dataset",
    "load_cached",
    "get_loaders",
    "strip_features",
    "generate_chat_template",
    "format_chat",
]
