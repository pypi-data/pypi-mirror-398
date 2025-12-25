from SOLIDserverRest.Exception import SDSError


class INTValidator:
    min_val: int
    max_val: int

    def __init__(self, min_val: int, max_val: int):
        """An Int Validator"""
        if min_val > max_val:
            raise SDSError("Min val must be lower than max val")
        self.min_val = min_val
        self.max_val = max_val

    def validate(self, other, name):
        try:
            other_int = int(other)
        except Exception:
            raise SDSError(f"{name} must be of type int")

        _range = range(self.min_val, self.max_val)

        if other_int not in _range:
            raise SDSError(
                f"{name} must be between"
                f" {self.min_val} and {self.max_val},"
                f" provided value {other_int} out of range"
            )


class STRValidator:
    max_len: int

    def __init__(self, max_len: int):
        """A Str Validator"""
        self.max_len = max_len

    def validate(self, other, name):
        is_string = isinstance(other, str)
        if not is_string:
            raise SDSError(f"{name} must be of type string")

        _len = len(other)

        if _len > self.max_len:
            raise SDSError(
                f"{name} must be a string with a max"
                f" length of {self.max_len}, provided string"
                f" is of length {_len}"
            )
