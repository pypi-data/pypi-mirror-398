basec = None
"""

__all__ = ["createException", "setBaseError"]
toastCE: Custom Exception Factory

Usage:
    import toastCE
    toastCE.createException("MyError")
    raise MyError("message")
"""

def setBaseClass(base):
    """
    This allows for the toastCE error to not start in toastCE, but rather whatever you want.
    Args:
        base (str): the exception starting name.
    """
    global basec
    basec = base


def createException(name, base=Exception, doc=None, module_globals=None):
    """
    Dynamically create a new Exception class and inject it into the caller's globals.
    Args:
        name (str): Name of the exception class.
        base (Exception): Base exception class (default: Exception).
        doc (str): Optional docstring for the exception class.
        module_globals (dict): The globals() of the caller. If None, will try to inject into caller's module.
    Returns:
        type: The new Exception class.
    """
    import inspect
    dct = {'__doc__': doc} if doc else {}
    if basec == None:
        dct['__module__'] = 'toastCE'  # Ensures exception displays as just the class name
    else:
        dct['__module__'] = basec  # Ensures exception displays as just the class name
    exc = type(name, (base,), dct)
    if module_globals is None:
        # Get caller's globals
        frame = inspect.currentframe()
        try:
            if frame is not None and frame.f_back is not None:
                caller_globals = frame.f_back.f_globals
            else:
                raise RuntimeError("Cannot determine caller's globals.")
        finally:
            del frame
        module_globals = caller_globals
    module_globals[name] = exc

    # Also set as attribute of this module (toastCE)
    import sys
    thismod = sys.modules[__name__]
    setattr(thismod, name, exc)
    return exc
