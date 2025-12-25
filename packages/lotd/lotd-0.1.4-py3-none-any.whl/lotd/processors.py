from transformers import PreTrainedTokenizer, PreTrainedTokenizerFast
from .templates import format_chat
from typing import Union, Dict, List, Tuple

class TextTokenizer:
    """
    Applies template and tokenizes texts in a dataset.
    """

    __slots__ = ("tokenizer", "max_length", "prefix", "suffix", "gaps")

    def __init__(
        self,
        tokenizer: Union[PreTrainedTokenizer, PreTrainedTokenizerFast],
        template: str = "[CLS]{{text}}[SEP]",
        max_length: Union[int, None] = None,
    ) -> None:
        """
        Initializes the dataset tokenizer.

        Args:
            tokenizer: pre-trained transformers tokenizer.
            template: jinja2 template containing `{{text}}` keyword.
            max_length(optional): maximum sequence length after truncation.
        """
        assert "{{text}}" in template, "template should contain `{{text}}` substring"
        self.tokenizer: Union[PreTrainedTokenizerFast, PreTrainedTokenizer] = tokenizer
        self.max_length: Union[int, None] = max_length
        template_parts = template.split("{{text}}")
        self.prefix: List[int] = tokenizer(template_parts[0], add_special_tokens=False)["input_ids"]  # type: ignore
        self.suffix: List[int] = tokenizer(template_parts[1], add_special_tokens=False)["input_ids"]  # type: ignore
        self.gaps: Tuple = (len(self.prefix), len(self.suffix))
        if self.max_length != None:
            self.max_length -= len(self.prefix) + len(self.suffix)
            assert self.max_length > 0, "Max length should be larger than prompt length"

    def __call__(self, texts: List[str]) -> Dict[str, List[List[int]]]:
        """
        Tokenizes a batch of text samples.

        Args:
            texts: list of strings.

        Returns:
            dict with input_ids and prompt_mask for all text in a batch.
        """
        text_ids = self.tokenizer(
            texts,
            add_special_tokens=False,
            truncation=self.max_length != None,
            max_length=self.max_length,
        )["input_ids"]
        input_ids = [self.prefix + x + self.suffix for x in text_ids]  # type: ignore
        prompt_mask = [
            [1] * self.gaps[0] + [0] * len(x) + [1] * self.gaps[1] for x in text_ids  # type: ignore
        ]
        return {"input_ids": input_ids, "prompt_mask": prompt_mask}


class ChatTokenizer:
    """
    Applies chat template and tokenizes messages in a dataset.
    """

    __slots__ = ("tokenizer", "max_length")

    def __init__(
        self,
        tokenizer: Union[PreTrainedTokenizer, PreTrainedTokenizerFast],
        max_length: Union[int, None] = None,
    ) -> None:
        """
        Initializes the dataset chat tokenizer.

        Args:
            tokenizer: pre-trained transformers tokenizer.
            max_length(optional): maximum sequence length after truncation.
        """
        self.tokenizer: Union[PreTrainedTokenizerFast, PreTrainedTokenizer] = tokenizer
        self.max_length: Union[int, None] = max_length

    def __call__(
        self,
        prompts: Union[List[str], List[List[str]]],
        responses: Union[List[str], List[List[str]]] = [],
        system: Union[List[str], None] = None,
    ) -> Dict[str, List[List[int]]]:
        """
        Tokenizes chats.

        Args:
            prompts: a list where each item is either a single prompt or multiple prompts in a dialog.
            responses: a list where each item is either a single response or multiple responses in a dialog.

        Returns:
            dict with input_ids and prompt_mask for all text in a batch.
        """
        batch_size = len(prompts)
        chats = [
            format_chat(prompts[i], responses[i], system[i] if system else None)
            for i in range(batch_size)
        ]
        inputs = self.tokenizer.apply_chat_template(
            chats,
            return_assistant_tokens_mask=True,
            tokenize=True,
            return_dict=True,
            truncation=self.max_length != None,
            max_length=self.max_length,
        )
        prompt_mask = [
            [0 if x == 1 else 1 for x in tokens] for tokens in inputs["assistant_masks"]  # type: ignore
        ]
        input_ids = inputs["input_ids"]  # type: ignore
        return {"input_ids": input_ids, "prompt_mask": prompt_mask}  # type: ignore
