class NoModifyMeta(type):
    def __setattr__(cls, key, value):
        raise AttributeError(f"Cannot modify class attribute '{key}'")


class ConstDict(metaclass=NoModifyMeta):

    def __setattr__(self, key, value):
        raise AttributeError(f"Cannot modify class attribute '{key}'")
