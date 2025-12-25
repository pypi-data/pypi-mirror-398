from typing import Union, Dict, List, Tuple


def format_chat(
    prompts: Union[str, List[str]] = [],
    responses: Union[str, List[str]] = [],
    system: Union[str, None] = None,
) -> List[Dict[str, str]]:
    """
    Format list of prompts, responses and system messages into a chat.

    Args:
        prompts: a single prompt or a list of prompts provided by a user in a dialog.
        responses: a single response or a list of responses producrd by a model in a dialog.
        system: system prompt used for this chat.

    Returns:
        a list of messages of form `[{"role": "...", "content": "..."}, ...]`.
    """
    # Convert to unified form
    if isinstance(prompts, str):
        prompts = [prompts]
    if isinstance(responses, str):
        responses = [responses]
    # Check input data
    assert len(prompts) == len(responses), "each prompt should have a response"
    # Convert to chat array
    chat = []
    if system:
        chat.append({"role": "system", "content": system})
    for i in range(len(prompts)):
        chat.append({"role": "user", "content": prompts[i]})
        chat.append({"role": "assistant", "content": responses[i]})
    return chat


def generate_chat_template(
    last_only: bool = False,
    wrapper: str = "{{template}}",
    system_tags: Tuple[str, str] = ("<|system|>", "<|end|>"),
    user_tags: Tuple[str, str] = ("<|user|>", "<|end|>"),
    assistant_tags: Tuple[str, str] = ("<|assistant|>", "<|end|>"),
) -> str:
    """
    Generate chat template for instruction tuning.

    Args:
        last_only: only enable generation for last response. If true, assistant_masks ignores previous responses. Default: False.
        wrapper: a wrapper for adding text before and after the template. Should contain `{{template}}`.
        system_tags: a pair of tags to mark the beginning and the end of a system role in a dialog.
        user_tags: see `system_tags`.
        assistant_tags: see `system_tags`.

    Returns:
        a jinja2 template string.
    """
    assert "{{template}}" in wrapper, "wrapper should contain `{{template}}` substring"
    template = """
{% for message in messages %}
{% if message['role'] == 'system' -%}
system_start{{message['content']}}system_end
{% elif message['role'] == 'user' -%}
user_start{{message['content']}}user_end
{% elif message['role'] == 'assistant' -%}
assistant_message
{% endif -%}
{% endfor -%}
""".strip()
    # Insert correct assistant message template
    if last_only:
        template = template.replace(
            "assistant_message",
            "assistant_start{% if loop.last %}{% generation %}{{message['content']}}{% endgeneration %}{% else %}{{message['content']}}{% endif %}assistant_end",
        )
    else:
        template = template.replace(
            "assistant_message",
            "assistant_start{% generation %}{{message['content']}}{% endgeneration %}assistant_end",
        )
    # Insert message tags
    for i, x in enumerate(["start", "end"]):
        template = template.replace(f"system_{x}", system_tags[i])
        template = template.replace(f"user_{x}", user_tags[i])
        template = template.replace(f"assistant_{x}", assistant_tags[i])
    # Wrap template
    template = wrapper.replace("{{template}}", template)
    return template
