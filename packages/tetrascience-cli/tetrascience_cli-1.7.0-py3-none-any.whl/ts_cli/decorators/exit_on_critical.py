import functools
import sys

from ts_cli.errors.critical_error import CriticalError
from ts_cli.util.emit import emit_critical


def exit_on_critical(func):
    @functools.wraps(func)
    def applicator(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except CriticalError as error:
            emit_critical(error.message)
            sys.exit(1)

    return applicator
