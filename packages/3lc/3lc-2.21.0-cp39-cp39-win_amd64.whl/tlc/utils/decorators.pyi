from typing import Callable, TypeVar

T = TypeVar('T', bound=Callable[..., object])

def disallow_positional_arguments(message: str = '') -> Callable[[T], T]:
    """
    Decorator to disallow passing positional arguments to a method with a custom message.

    :param message: The custom message to display when the method is called with positional arguments. Usually a
        suggestion on what to do instead.
    :return: The decorator.
    """
