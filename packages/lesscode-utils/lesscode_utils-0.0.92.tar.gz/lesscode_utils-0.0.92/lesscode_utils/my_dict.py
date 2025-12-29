class MyDict(dict):

    def get(self, key, default=None):
        value = super().get(key, default)
        value = value if value is not None else default
        return self._process_value(value)

    def _process_value(self, value):
        if isinstance(value, dict):
            for k, v in value.items():
                value[k] = self._process_value(v)
            return MyDict(value)
        elif isinstance(value, list):
            return [self._process_value(v) for v in value]
        elif isinstance(value, set):
            return {self._process_value(v) for v in value}
        elif isinstance(value, tuple):
            return (self._process_value(v) for v in value)
        else:
            return value
