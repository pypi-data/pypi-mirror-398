class Memton:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.data = {}
        return cls._instance

    def set_value(self, key, value):
        self.data[key] = value

    def get_value(self, key):
        return self.data.get(key)