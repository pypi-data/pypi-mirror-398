import copy
import pprint

class KDict(dict):
    '''
    A dict subclass that allows attribute access (obj.key)
    and recursively converts nested dicts, lists, tuples, and sets.
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._convert_nested()

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"`KDict` object has no attribute '{name}'")

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        try:
            del self[name]
        except KeyError:
            raise AttributeError(f"`KDict` object has no attribute '{name}'")

    @staticmethod
    def _wrap(value):
        '''Recursively wrap any dicts inside nested structures.'''
        if isinstance(value, dict) and not isinstance(value, KDict):
            return KDict(value)
        elif isinstance(value, list):
            return [KDict._wrap(v) for v in value]
        elif isinstance(value, tuple):
            return tuple(KDict._wrap(v) for v in value)
        elif isinstance(value, set):
            return {KDict._wrap(v) for v in value}
        else:
            return value

    def _convert_nested(self):
        '''Convert all nested dicts/lists/tuples/sets in self.'''
        for k, v in list(self.items()):
            super().__setitem__(k, self._wrap(v))

    def copy(self):
        return KDict(copy.deepcopy(self))

    def update(self, *args, **kwargs):
        result = super().update(*args, **kwargs)
        self._convert_nested()
        return result

    @classmethod
    def fromkeys(cls, seq, value=None):
        return cls({k: value for k in seq})

    def __getitem__(self, key):
        value = super().__getitem__(key)
        wrapped = self._wrap(value)
        if wrapped is not value:
            super().__setitem__(key, wrapped)
        return wrapped

    def toDict(self):
        '''
        convert KDict to dict
        '''
        def unwrap(v):
            if isinstance(v, KDict):
                return {k: unwrap(x) for k, x in v.items()}
            if isinstance(v, list):
                return [unwrap(x) for x in v]
            if isinstance(v, tuple):
                return tuple(unwrap(x) for x in v)
            if isinstance(v, set):
                return {unwrap(x) for x in v}
            return v
        return unwrap(self)

    def __repr__(self):
        return repr(dict(self))

# map the KDict type to pprint's dict pretty-printer
try:
    pprint.PrettyPrinter._dispatch[KDict.__repr__] = pprint.PrettyPrinter._pprint_dict
except Exception: pass
