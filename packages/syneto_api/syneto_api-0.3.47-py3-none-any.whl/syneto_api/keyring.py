class Multiton(type):
    __instances = {}

    def __call__(cls, url: str, *args, **kwds):
        if url not in cls.__instances:
            cls.__instances[url] = super(Multiton, cls).__call__(*args, **kwds)
        return cls.__instances[url]


class KeyRing(metaclass=Multiton):
    __JWT_TOKEN = None

    def set_token(self, token: str):
        self.__JWT_TOKEN = token

    def get_token(self):
        return self.__JWT_TOKEN
