class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

# Calls the init function for all Singleton classes
def initSingletons():
    for key in Singleton._instances: # pylint: disable=W0212
        inst = Singleton._instances[key] # pylint: disable=W0212
        if 'init' in dir(inst):
            inst.init()
