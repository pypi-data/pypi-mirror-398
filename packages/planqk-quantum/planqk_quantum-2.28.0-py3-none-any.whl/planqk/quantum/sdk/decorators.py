def not_implemented(method):
    def wrapper(*args, **kwargs):
        raise NotImplementedError("This function is not implemented. Please contact PLANQK support if you require this functionality.")

    return wrapper


def not_supported(method):
    def wrapper(*args, **kwargs):
        raise NotImplementedError("This function is not supported by the SDK.")

    return wrapper
