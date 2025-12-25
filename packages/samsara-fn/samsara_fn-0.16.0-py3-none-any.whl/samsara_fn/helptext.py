import textwrap


def description(raw: str) -> str:
    return textwrap.dedent(raw).strip()


ANSI_CODES = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "italic": "\033[3m",
    "underline": "\033[4m",
    "black": "\033[30m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[37m",
    "bright_black": "\033[90m",
    "bright_red": "\033[91m",
    "bright_green": "\033[92m",
    "bright_yellow": "\033[93m",
    "bright_blue": "\033[94m",
    "bright_magenta": "\033[95m",
    "bright_cyan": "\033[96m",
    "bright_white": "\033[97m",
}


def f(text: str, style: str = "bold") -> str:
    """
    Applies ANSI formatting to the given text.

    Args:
        text: The string to format.
        style: The style to apply (e.g., "bold", "underline", "red").
               Defaults to "bold".

    Returns:
        The formatted string with ANSI escape codes.
    """
    style_code = ANSI_CODES.get(style.lower())
    reset_code = ANSI_CODES["reset"]
    if style_code:
        return f"{style_code}{text}{reset_code}"
    return text
