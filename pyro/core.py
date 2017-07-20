from ipdb import set_trace as debug
from flask import jsonify
from pyro.database import *
from pyro.utils import *


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
        # Are there any nested routes? Let's check.
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
        cls.before_index() # before hook
        cls._docs = cls.all()
        cls.after_index() # after hook
        return cls._to_response(resources)

    @classmethod
    def _create(cls):
        '''Create a new resource.'''
        cls._request = request
        cls.before_create() # before hook
        cls._obj = cls.create(request.json)
        cls.after_create() # after hook
        return cls._to_response(cls._obj._doc)

    @classmethod
    def _show(cls, resource_id):
        '''Find the specified resource'''
        cls._resource_id = resource_id
        cls.before_show() # before hook
        cls._obj = cls.find_by_id(cls._resource_id)
        cls.after_show() # after hook
        return cls._to_response(cls._obj._doc)

    @classmethod
    def _destroy(cls, resource_id):
        '''Delete the specified resource.'''
        cls._resource_id = resource_id
        cls.before_destroy() # before hook
        cls.after_destroy() # after hook

    @classmethod
    def _update(cls, resource_id):
        '''Update the specified resource.'''
        cls._resource_id = resource_id
        cls.before_update() # before hook
        cls.after_update() # after hook
    # -------------- END CONTROLLER METHODS --------------------------

    # -------------- HOOK METHODS ------------------------------------
    @classmethod
    def before_index(cls):
        pass

    @classmethod
    def after_index(cls):
        pass

    @classmethod
    def before_create(cls):
        pass

    @classmethod
    def after_create(cls):
        pass

    @classmethod
    def before_show(cls):
        pass

    @classmethod
    def after_show(cls):
        pass

    @classmethod
    def before_update(cls):
        pass

    @classmethod
    def after_update(cls):
        pass

    @classmethod
    def before_destroy(cls):
        pass

    @classmethod
    def after_destroy(cls):
    # -------------- END HOOK METHODS--------------------------------

    @classmethod
    def new(cls, doc, parent_instance=None):
        '''Create a new object, but do not save to database.'''
        cls._doc = deserialize(doc)
        obj = cls(cls._doc)
        obj.before_new()
        cls.validate_associations(cls._doc, parent_instance)
        obj.after_new()
        return obj

    @classmethod
    def create(cls, doc, parent_instance=None):
        '''Create an instance and save to database.'''
        obj = cls.new(doc, parent_instance=parent_instance)
        obj.save()
        return obj

    @classmethod
    def validate_associations(cls, doc, parent_instance):
        '''Ensure that has_many relationships are working.'''
        if not (len(cls._parents)>0): # no parents
            return doc
        if not parent_instance:
            if cls._parents[0]._foreign_key() in doc: # already assigned
                return doc
        elif parent_instance.__class__ in cls._parents: # assign now
            doc[parent_instance._foreign_key()] = parent_instance._id
            return doc
        error = ('This class must belong to an instance of the {:s} class').\
                format(snake_to_class(cls._parents[0]._singular_name))
        raise ValueError(error)

    @classmethod
    def all(cls):
        '''Return a list of all documents associated with this object.'''
        collection = cls._db[cls._plural_name]
        return list(collection.find())

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
    def _to_response(cls, package):
        '''Convert the output of a data package into a JSON object.'''
        return jsonify(serialize(package))

    @classmethod
    def find_by_id(cls, _id):
        _id = ObjectId(_id)
        doc = find_document(_id, cls._db[cls._plural_name])
        if doc is None:
            raise ValueError('Document is not in the database')
        else:
            obj = cls.new(doc)
            obj._finally()
            return obj

    @classmethod
    def _foreign_key(cls):
        '''Returns the foreign key associated with this class.'''
        return '_{:s}_id'.format(cls._singular_name)

    @classmethod
    def has_many(cls, child_class):
        '''Specify a one-to-many relationship between data models.'''
        child_class._parents.append(cls)
        cls._children.append(child_class)

    def __init__(self, doc):
        '''Consume a document and attach attributes as properties.'''
        self.__dict__.update(doc)

    def _find_parents(self):
        '''Find and attach parent.'''
        if self.has_parent:
            ParentClass = self._parents[0]
            foreign_key = ParentClass._foreign_key()
            parent_obj = ParentClass.find_by_id(self.__dict__[foreign_key])
            self.__dict__[ParentClass._singular_name] = parent_obj

    def _find_children(self):
        '''Find and attach parent.'''
        for ChildClass in self._children:
            self.__dict__[ChildClass._plural_name] = ForeignQuery(self,\
                    ChildClass)

    def _sync_to_doc(self):
        '''Sync object attributes to the document.'''
        self.__dict__.update(self._doc)

    def _sync_to_obj(self):
        '''Sync document to the attributes.'''
        self._doc.__update(self.__dict__)

    @property
    def has_parent(self):
        '''Does this model belong to another model?'''
        return len(self._parents)>0

    def save(self):
        '''Save the current document, if there is one.'''
        collection = self._db[self._plural_name]
        self._doc.update(self.__dict__)
        if self.doc_exists:
            self._update_existing_doc()
        else:
            self._save_new_doc()
        self._finally()

    def _finally(self):
        '''Clean up, sideload parents/children/etc.'''
        self._find_parents()
        self._find_children()

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

    def serialize(self, include_children=False):
        '''Prepare document for transport over HTTP.'''
        doc = self._doc
        if include_children:
            for ChildClass in self._children:
                child_name = ChildClass._plural_name
                doc[child_name] = self.__dict__[child_name]()
        return serialize(doc)

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
        macbeth = Book.create({'title': 'Macbeth', 'pages': 432}, mjl)
        hamlet = Book.create({'title': 'Hamlet', 'pages': 432}, mjl)
        thesun = Book.create({'title': 'The Sun Also Rises', 'pages': 432}, mjl)

