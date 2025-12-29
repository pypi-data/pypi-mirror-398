import inspect


def promise(resolver: str):
    def decorator(fn):
        if not inspect.isfunction(fn):
            raise TypeError("The promise decorator can only be applied to functions.")

        fn.__promise_resolver_function_name__ = resolver
        fn.__is_async__ = True

        return fn

    return decorator
