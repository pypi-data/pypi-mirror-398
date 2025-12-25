"""Message parsing utilities."""

from urllib.parse import parse_qs

from .types import InputType, ProcessedInput


def parse_prompt_arguments(prompt_string: str) -> tuple[str, dict[str, str]]:
    """Parse prompt name and arguments from a prompt command string.

    Supports syntax: prompt_name?arg1=value1&arg2=value2

    Args:
        prompt_string: The prompt string after "/prompt/" prefix

    Returns:
        Tuple of (prompt_name, arguments_dict)
    """
    if "?" not in prompt_string:
        return prompt_string, {}

    # Split on first "?" to get name and query string
    name_part, query_part = prompt_string.split("?", 1)

    # Parse query string arguments
    parsed = parse_qs(query_part, keep_blank_values=True)

    # Convert from {key: [value]} to {key: value} (take first value for each key)
    arguments = {key: values[0] if values else "" for key, values in parsed.items()}

    return name_part, arguments


def parse_user_input(user_input: str) -> ProcessedInput:
    """Parse user input and return information about what type of input it is.

    This function only analyzes the input and returns metadata about how it should be handled.
    It does NOT execute any actions or modify any state.
    """

    user_input_lower = user_input.strip().lower()

    if user_input_lower.startswith("/prompt/"):
        # This is a prompt loading command
        # Keep original case for the prompt string (arguments may be case-sensitive paths)
        prompt_string = user_input.strip()[8:]  # Remove "/prompt/" prefix, keep original case
        prompt_name, prompt_arguments = parse_prompt_arguments(prompt_string)
        return ProcessedInput(
            input_type=InputType.COMMAND_PROMPT,
            should_continue=True,
            prompt_name=prompt_name.lower(),  # Prompt names are case-insensitive
            prompt_arguments=prompt_arguments,
            user_message=user_input,
        )

    if user_input_lower.startswith("/resource/"):
        # This is a resource reading command
        resource_uri = user_input[10:]  # Remove "/resource/" prefix, keep original case
        return ProcessedInput(
            input_type=InputType.COMMAND_RESOURCE,
            should_continue=True,
            resource_uri=resource_uri,
            user_message=user_input,
        )

    if user_input_lower == "/quit":
        # This is a termination command
        return ProcessedInput(input_type=InputType.TERMINATE, should_continue=False, user_message=user_input)

    # Check if this is a command starting with "/"
    if user_input_lower.startswith("/"):
        # This is a specific informational command
        if user_input_lower == "/tools":
            input_type = InputType.COMMAND_INFO_TOOLS
        elif user_input_lower == "/resources":
            input_type = InputType.COMMAND_INFO_RESOURCES
        elif user_input_lower == "/prompts":
            input_type = InputType.COMMAND_INFO_PROMPTS
        elif user_input_lower == "/model-thinking-switch":
            input_type = InputType.COMMAND_MODEL_THINKING_SWITCH
        else:
            # Unknown command starting with "/", treat as invalid command
            input_type = InputType.COMMAND_UNKNOWN
    else:
        # Not a command, treat as normal message
        input_type = InputType.NORMAL_MESSAGE

    # Handle normal user messages
    if input_type == InputType.NORMAL_MESSAGE:
        return ProcessedInput(input_type=InputType.NORMAL_MESSAGE, should_continue=True, user_message=user_input)

    return ProcessedInput(input_type=input_type, should_continue=True, user_message=user_input)
