"""Utility functions for the models module."""

import warnings


def deprecated_function(new_name: str):
    """Notify users that a function is deprecated and will be removed in the future.
    Works equally well on functions and methods.

    Usage:
        @deprecated("new_name")
        def old_name():
            pass
    """

    def decorator(func):
        def wrapped(*args, **kwargs):
            warnings.warn(
                f"{func.__name__} is deprecated and will be removed in future "
                f"versions. Please use {new_name} instead.",
                FutureWarning,
                stacklevel=2,
            )
            return func(*args, **kwargs)

        return wrapped

    return decorator


def deprecated_class(new_name):
    """Notify users that a class is deprecated and will be removed in the future.
    Works only on Pydantic models since it relies on the model_post_init method.

    Usage:
        @deprecated_class("new_name")
        class OldName:
            pass
    """

    def class_decorator(cls):
        orig_model_post_init = cls.model_post_init

        def new_model_post_init(self, *args, **kwargs):
            warnings.warn(
                f"{cls.__name__} is deprecated and will be removed in a future "
                f"release. Please use '{new_name}' instead.",
                category=FutureWarning,
                stacklevel=2,
            )
            orig_model_post_init(self, *args, **kwargs)

        cls.model_post_init = new_model_post_init
        return cls

    return class_decorator
