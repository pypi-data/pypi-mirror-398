class Borg:
    __shared_state = {}
    # init internal state variables here
    __register = {}

    def __init__(self):
        self.__dict__ = self.__shared_state
        if not self.__register:
            self._init_default_register()


def singleton(class_):
    instances = {}

    def wrapper(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]

    return wrapper
