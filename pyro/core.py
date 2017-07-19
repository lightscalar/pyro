from pyro.utils import *


class PyroMeta(type):
    '''Metaclass for Pyro.'''

    def __new__(cls, name, parents, dct):
        dct['_singular_name'] = camel_to_snake(name)
        dct['_plural_name'] = plural(camel_to_snake(name))
        dct['_parents'] = []
        dct['_children'] = []
        return super(PyroMeta, cls).__new__(cls, name, parents, dct)

    def __init__(cls, name, bases, nmspc):
        '''Set up subclass registry.'''
        super(PyroMeta, cls).__init__(name, bases, nmspc)
        if not hasattr(cls, '_registry'):
            cls._registry = set()
        cls._registry.add(cls)
        cls._registry -= set(bases)
        pass

    def __iter__(cls):
        return iter(cls._registry)


class Pyro(object, metaclass=PyroMeta):
    '''Main Pyro class for creating flexible data objects.'''
    pass
    _routes = []
    _db = None

    def _attach_db(cls, db):
        '''Attaches a database to the Pyro environment.'''
        cls._db = db

    @classmethod
    def new(cls, doc):
        '''Create a new object, but do not save to database.'''
        cls._doc = doc
        cls.before_new() # before hook
        obj = cls()
        obj.__dict__.update(cls._doc)
        cls.after_new() # after hook
        return obj

    @classmethod
    def before_new(cls):
        pass

    @classmethod
    def after_new(cls):
        '''Override to add functionality.'''
        pass

    @classmethod
    def before_update(cls):
        '''Override to add functionality.'''
        pass

    @classmethod
    def after_update(cls):
        '''Override to add functionality.'''
        pass

    @classmethod
    def before_delete(cls):
        '''Override to add functionality.'''
        pass

    @classmethod
    def after_delete(cls):
        '''Override to add functionality.'''
        pass
