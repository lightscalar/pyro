from pyro.database import *
from pyro.utils import *
from ipdb import set_trace as debug


class PyroMeta(type):
    '''Metaclass for Pyro.'''

    def __new__(cls, name, parents, dct):
        dct['_singular_name'] = camel_to_snake(name)
        dct['_plural_name'] = plural(camel_to_snake(name))
        dct['_parents'] = []
        dct['_children'] = []
        dct['_doc'] = None
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

    @classmethod
    def _attach_db(cls, db):
        '''Attaches a database to the Pyro environment.'''
        cls._db = db

    @classmethod
    def _routes(cls):
        '''Create the routes associated with this data resource.'''
        routes = {}

        # index
        route_name = '{:s}.index'.format(cls._plural_name)
        route = '/{:s}'.format(cls._plural_name)
        methods = ['GET']
        callback = cls._index
        routes[route_name] = {'route': route, 'methods': methods,\
                              'callback': callback}
        # show
        route_name = '{:s}.show'.format(cls._singular_name)
        route = '/{:s}/<resource_id>'.format(cls._singular_name)
        methods = ['GET']
        callback = cls._show
        routes[route_name] = {'route': route, 'methods': methods,\
                              'callback': callback}
        # create
        route_name = '{:s}.create'.format(cls._plural_name)
        route = '/{:s}'.format(cls._plural_name)
        methods = ['POST']
        callback = cls._create
        routes[route_name] = {'route': route, 'methods': methods,\
                              'callback': callback}
        # update
        route_name = '{:s}.update'.format(cls._singular_name)
        route = '/{:s}/<resource_id>'.format(cls._singular_name)
        methods = ['PUT']
        callback = cls._update
        routes[route_name] = {'route': route, 'methods': methods,\
                              'callback': callback}
        # destroy
        route_name = '{:s}.destroy'.format(cls._singular_name)
        route = '/{:s}/<resource_id>'.format(cls._singular_name)
        methods = ['DELETE']
        callback = cls._destroy
        routes[route_name] = {'route': route, 'methods': methods,\
                              'callback': callback}
        # Are there any nested routes?
        for child in cls._children:
            # index - only two levels of nesting allowed!
            route_name = '{:s}.{:s}.index'.format(cls._singular_name,\
                    child._plural_name)
            route = '/{:s}/<resource_id>/{:s}'.format(cls._singular_name,\
                    child._plural_name)
            methods = ['GET']
            callback = cls._index
            routes[route_name] = {'route': route, 'methods': methods,\
                                  'callback': callback}
        return routes

    # -------------- CONTROLLER METHODS -----------------------------
    @classmethod
    def _index(cls):
        '''List all resources.'''
        pass

    @classmethod
    def _create(cls):
        '''Create a new resource.'''
        pass

    @classmethod
    def _show(cls):
        '''Find the specified resource'''
        pass

    @classmethod
    def _destroy(cls):
        '''Delete the specified resource.'''
        pass

    @classmethod
    def _update(cls):
        '''Update the specified resource.'''
        pass
    # -------------- END CONTROLLER METHODS --------------------------

    @classmethod
    def new(cls, doc, parent_instance=None):
        '''Create a new object, but do not save to database.'''
        cls._doc = deserialize(doc)
        obj = cls()
        obj.before_new()
        cls.validate_associations(cls._doc, parent_instance)
        obj.__dict__.update(cls._doc)
        obj.after_new()
        return obj

    @classmethod
    def create(cls, doc, parent_instance=None):
        '''Create an instance and save to database.'''
        obj = cls.new(doc)
        obj.save()
        return obj

    @classmethod
    def validate_associations(cls, doc, parent_instance):
        '''Ensure that has_many relationships are working.'''
        if (parent_instance is not None) and parent_instance.__class__\
                in cls._parents:
            doc[name_to_id(parent_instance._singular_name)] =\
                    parent_instance._id
        elif len(cls._parents) > 0:
            raise ValueError(('This class must belong to an instance of '
                  'the {:s} class.').format(class_case(cls._parents[0].\
                          _singular_name)))
        return doc

    @classmethod
    def all(cls):
        '''Return a list of all documents associated with this object.'''
        collection = cls._db[cls._plural_name]
        return collection.find()

    @classmethod
    def delete_all(cls):
        '''Return a list of all documents associated with this object.'''
        collection = cls._db[cls._plural_name]
        return collection.delete_many({})

    @classmethod
    def to_objects(cls, cursor):
        '''Convert the output of a query into a list of objects.'''
        return [cls.new(doc) for doc in cursor]

    @classmethod
    def has_many(cls, child_class):
        '''Specify a one-to-many relationship between data models.'''
        child_class._parents.append(cls)
        cls._children.append(child_class)

    def save(self):
        '''Save the current document, if there is one.'''
        collection = self._db[self._plural_name]
        self._doc.update(self.__dict__)
        if self.doc_exists:
            self._update_existing_doc()
        else:
            self._save_new_doc()

    def _save_new_doc(self):
        '''Save new document to the database.'''
        self.before_save() # before hook
        response = self._db[self._plural_name].insert_one(self._doc)
        self._doc['_id'] = response.inserted_id
        self.__dict__.update(self._doc)
        self.after_save() # after hook

    def _update_existing_doc(self):
        '''Update an existing document.'''
        self.before_update() # before hook
        self._doc.update(self.__dict__)
        update_document(self._doc, self._db[self._plural_name])
        self.after_update() # after hook

    def delete(self):
        '''Delete the current document.'''
        self.before_delete() # before hook
        collection = self._db[self._plural_name]
        collection.delete_one(qwrap(self._id))
        self.after_delete() # after hook

    @property
    def doc_exists(self):
        '''Does the document exist in the database?'''
        return '_id' in self._doc # if it has an ID, it has been saved

    def before_new(self):
        '''Override to add functionality.'''
        pass

    def after_new(self):
        '''Override to add functionality.'''
        pass

    def before_update(self):
        '''Override to add functionality.'''
        pass

    def after_update(self):
        '''Override to add functionality.'''
        pass

    def before_delete(self):
        '''Override to add functionality.'''
        pass

    def after_delete(self):
        '''Override to add functionality.'''
        pass

    def before_save(self):
        '''Override to add functionality.'''
        pass

    def after_save(self):
        '''Override to add functionality.'''
        pass


if __name__ == '__main__':

        db = connect_to_database()
        Pyro._attach_db(db)

        class Author(Pyro):
            pass

        class Book(Pyro):
                pass

        Author.has_many(Book)

        mjl = Author.create({'firstName': 'Matthew J. Lewis', 'age': 37})

