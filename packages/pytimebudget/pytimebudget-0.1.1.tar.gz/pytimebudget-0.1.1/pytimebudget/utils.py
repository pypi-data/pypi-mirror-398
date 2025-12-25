import inspect

def resolve_name():
    frame = inspect.stack()[2]
    module = frame.frame.f_globals.get("__name__", "<unknown>")
    lineno = frame.lineno
    return f"{module}:line{lineno}"
