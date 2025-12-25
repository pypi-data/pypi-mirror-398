"""Sample module demonstrating best practices."""


def greet(name: str, enthusiastic: bool = False) -> str:
    """Generate a greeting message.

    Args:
        name: The name of the person to greet.
        enthusiastic: If True, add extra enthusiasm.

    Returns:
        A greeting message.

    Examples:
        >>> greet("World")
        'Hello, World!'
        >>> greet("Python", enthusiastic=True)
        'Hello, Python!!!'
    """
    greeting = f"Hello, {name}!"
    if enthusiastic:
        greeting += "!!"
    return greeting
