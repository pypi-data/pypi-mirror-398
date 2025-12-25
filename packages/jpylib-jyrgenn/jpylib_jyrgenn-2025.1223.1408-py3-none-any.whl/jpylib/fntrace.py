#!/usr/bin/env python3

from jpylib import is_trace, trace

trace_len = 31                            # max. width of obj. trace
trace_ellipsis = "[…]"

def set_trace_len(length):
    """Set max. length of call argument representation in trace.

    If `length` is None, call argument representation will not be cropped.
    """
    global trace_len
    trace_len = length

def set_trace_ellipsis(ellipsis):
    """Set string to indicate a call argument in the trace has been cropped.
    """
    global trace_ellipsis
    trace_ellipsis = ellipsis


def crop(s):
    l = len(s)
    if trace_len is None or l <= trace_len:
        return s
    return s[:trace_len - len(trace_ellipsis)] + trace_ellipsis


def tracefn(func):
    """Decorator: trace function's calls if alert level is `L_TRACE` or higher.

    When printing the function call arguments, their representation is cropped
    to `trace_len` (default 31), including `trace_ellipsis` (default '[…]').
    Both are module variables that can be changed. If `trace_len` is None, the
    representation will not be cropped.

    """
    def wrapper(*args, **kwargs):
        if is_trace():
            s = "call {}({}".format(func.__name__,
                                    ', '.join(map(crop, map(repr, args))))
            if kwargs:
                for k, v in kwargs.items():
                    s += ", {}={}".format(k, crop(repr(v)))
            trace(s + ")")
        return func(*args, **kwargs)
    return wrapper

