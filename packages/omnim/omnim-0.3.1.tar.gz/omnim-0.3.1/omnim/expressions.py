from inspect import isfunction, isclass, ismethod, currentframe


def nameof(obj) -> str:
    if isfunction(obj) or isclass(obj) or ismethod(obj):
        return obj.__name__
    elif hasattr(obj, "__call__") and hasattr(obj, "__name__"):
        return obj.__name__
    else:
        frame = currentframe()
        if frame is None:
            return ""
        try:
            caller_frame = frame.f_back
            if caller_frame is None:
                return ""

            for name, value in caller_frame.f_locals.items():
                if value is obj:
                    return name
            for name, value in caller_frame.f_globals.items():
                if value is obj:
                    return name
        finally:
            del frame
        return ""


if __name__ == "__main__":

    def add(a, b) -> int:
        return a + b

    a = 2
    b = -3
    print(f"{nameof(add)}({nameof(a)}, {nameof(b)}): {add(a, b)}")
