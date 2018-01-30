#!/usr/bin/env python

import types
import functools

# Inspired by: http://www.valuedlessons.com/2008/01/monads-in-python-with-nice-syntax.html
# Original Author: Peter Thatcher
# Collected By: Michael-Keith Bernard
# Collected On: 2018-01-14
# Modified By: Michael-Keith Bernard

def decorator(dec, *dec_args, **dec_kwargs):
    """Convert a function into a decorator"""

    @functools.wraps(dec)
    def real_decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return dec(func, args, kwargs, *dec_args, **dec_kwargs)
        return wrapper
    return real_decorator

def decorator_with_args(real_dec):
    """Convert a function into a decorator that receives arguments at
    decoration-time
    """

    @functools.wraps(real_dec)
    def decorator_wrapper(*args, **kwargs):
        return decorator(real_dec, *args, **kwargs)
    return decorator_wrapper

@decorator_with_args
def do(func, func_args, func_kwargs, Monad):
    """Simple do-notation style decorator"""

    def wrapped():
        it = func(Monad, *func_args, **func_kwargs)
        if not isinstance(it, types.GeneratorType):
            return it

        def continuation(val):
            try:
                next_val = it.send(val)
                return Monad.bind(next_val, continuation)
            except StopIteration as i:
                if hasattr(i, "value"):
                    return i.value
                else:
                    return None

        return continuation(None)
    return wrapped()

if __name__ == "__main__":
    import os
    import yaml
    import either

    @do(either)
    def check_path(M, path):
        if os.path.isfile(path):
            return M.succeed(path)
        else:
            return M.fail("not a valid path")

    @do(either)
    def read_content(M, path):
        return M.succeed(open(path).read())

    @do(either)
    def parse_yaml(M, content):
        try:
            return M.succeed(yaml.safe_load(content))
        except Exception as e:
            return M.fail("invalid yaml: {}".format(e))

    @do(either)
    def load_yaml(M, path):
        valid_path = yield check_path(path)
        content = yield read_content(path)
        data = yield parse_yaml(content)
        return M.pure(data)

    print(load_yaml("valid.yaml"))

