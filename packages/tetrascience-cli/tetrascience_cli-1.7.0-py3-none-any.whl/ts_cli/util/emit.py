import sys
from typing import Callable

from ts_cli.util.colour import blue, green, magenta, red, yellow


def make_emitter(colorizer: Callable[[str], str], prefix: str, file):
    """
    Creates a function which emits a message to the console with the provided colour
    :param colorizer:
    :param prefix:
    :param file:
    :return:
    """

    def applicator(message: str) -> None:
        print(
            colorizer(f"{prefix}{message}"),
            file=file,
            flush=True,
        )

    return applicator


emit_critical = make_emitter(magenta, "", sys.stderr)
emit_error = make_emitter(red, "", sys.stderr)
emit_warning = make_emitter(yellow, "warning: ", sys.stdout)
emit_info = make_emitter(blue, "", sys.stdout)
emit_success = make_emitter(green, "", sys.stdout)
