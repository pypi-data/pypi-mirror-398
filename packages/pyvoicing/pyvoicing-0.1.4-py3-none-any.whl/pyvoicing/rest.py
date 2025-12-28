class Rest(int):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls, 0)
        return cls._instance

    def __init__(self):
        pass

    def __repr__(self):
        return 'Rest()'

    def __str__(self):
        return ''

    def __add__(self, other):
        return self

    def __radd__(self, other):
        return self

    def __sub__(self, other):
        return self

    def __rsub__(self, other):
        return self

    def __mul__(self, other):
        return self

    def __rmul__(self, other):
        return self

    def __truediv__(self, other):
        return self

    def __rtruediv__(self, other):
        return self

    def __floordiv__(self, other):
        return self

    def __rfloordiv__(self, other):
        return self

    def __mod__(self, other):
        return self

    def __rmod__(self, other):
        return self

    def __pow__(self, other, modulo=None):
        return self

    def __rpow__(self, other):
        return self

    def __and__(self, other):
        return self

    def __or__(self, other):
        return self

    def __xor__(self, other):
        return self

    def __lshift__(self, other):
        return self

    def __rshift__(self, other):
        return self

    def __eq__(self, other):
        return isinstance(other, Rest)

    def __ne__(self, other):
        return not isinstance(other, Rest)

    def __lt__(self, other):
        return False

    def __le__(self, other):
        return False

    def __gt__(self, other):
        return False

    def __ge__(self, other):
        return False

    def __neg__(self):
        return self

    def __pos__(self):
        return self

    def __abs__(self):
        return self

    def __invert__(self):
        return self

    def __hash__(self):
        return 9999
