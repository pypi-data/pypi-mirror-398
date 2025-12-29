import builtins
from functools import wraps
from logging import Logger
from typing import Generic, Set, TypeVar

T = TypeVar("T")


class Sensitive(Generic[T]):
    sensitive_data: Set[str] = set()

    def __init__(self, value: T):
        Sensitive.sensitive_data.add(str(value))
        self._value = value

    def __str__(self):
        return "Sensitive(****)"

    def __repr__(self):
        return "Sensitive(****)"

    def __getattr__(self, name):
        if name == "get_value":
            return lambda: self._value
        return getattr(self._value, name)

    def __eq__(self, other):
        if isinstance(other, Sensitive):
            return self._value == other._value
        return self._value == other

    def __hash__(self):
        return hash(self._value)

    def __add__(self, other):
        return self._value + other

    def __radd__(self, other):
        return other + self._value

    def get_value(self):
        # NOTE: This won't be accessible from the outside, as __getattr__ will
        # take precedence over anything, but will show up as a method in the class
        # definition.
        return self._value


unwrapped_log_method = Logger._log
unwrapped_print_function = builtins.print


def scrub_filter(data: str):
    for sensitive in sorted(list(Sensitive.sensitive_data), reverse=True):
        data = str(data).replace(sensitive, "Sensitive(****)")
    return data


@wraps(unwrapped_log_method)
def scrub_sensitive_data_from_logger(self, level, msg, args, exc_info=None, extra=None, stack_info=False, stacklevel=1):
    scrubbed_msg = scrub_filter(msg)
    return unwrapped_log_method(self, level, scrubbed_msg, args, exc_info=exc_info, extra=extra, stack_info=stack_info, stacklevel=stacklevel)


@wraps(builtins.print)
def scrub_sensitive_data_from_print(*args, sep=" ", end="\n", file=None):
    scrubbed_args = (scrub_filter(arg) for arg in args)
    return unwrapped_print_function(*scrubbed_args, sep=sep, end=end, file=file)


# NOTE: These will wrap the builtin print and the log function, so that there is no way around
#       to log any sensitive data, even if the source of the logging message does not come from
#       a Sensitive object in itself.

Logger._log = scrub_sensitive_data_from_logger
builtins.print = scrub_sensitive_data_from_print
print = scrub_sensitive_data_from_print  # pylint: disable=redefined-builtin
