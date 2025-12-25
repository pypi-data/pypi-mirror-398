import warnings

def emit_warning(name, baseline, current, warn_only):
    msg = (
        f"[pytimebudget] Performance regression detected\n"
        f"  Name:     {name}\n"
        f"  Baseline: {baseline:.2f} ms\n"
        f"  Current:  {current:.2f} ms\n"
        f"  Slowdown: {current / baseline:.2f}x"
    )

    if warn_only:
        warnings.warn(msg, RuntimeWarning)
    else:
        print(msg)
