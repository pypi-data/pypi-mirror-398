from functools import update_wrapper


def combo_wraps(func, rename_rule=None):
    def decorator(wrapper):
        # copy all except __name__
        attrs = ('__module__', '__qualname__', '__annotations__', '__doc__')
        update_wrapper(wrapper, func, assigned=attrs)

        outter_wrapper_name = wrapper.__name__

        # custom rule
        if rename_rule is None:
            wrapper.__name__ = f"{outter_wrapper_name}({func.__name__})"
        else:
            wrapper.__name__ = rename_rule(outter_wrapper_name, func.__name__)

        return wrapper

    return decorator


def call_with(*args, **kwargs):
    def fmt_args_kwargs():
        parts = []
        if args:
            parts.append(", ".join(map(repr, args)))
        if kwargs:
            kw = ", ".join(f"{k}={v!r}" for k, v in kwargs.items())
            parts.append(kw)
        return ", ".join(parts)

    argstr = fmt_args_kwargs()

    def decorator(func):
        @combo_wraps(
            func,
            rename_rule=lambda wrapname, funcname: f"{wrapname}({argstr}).{funcname}"
        )
        def callwith():
            return func(*args, **kwargs)

        return callwith

    return decorator
