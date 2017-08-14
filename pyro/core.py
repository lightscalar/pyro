from ipdb import set_trace as debug
from flask import jsonify, request
from datetime import datetime
from pyro.database import *
from pyro.utils import *


class PyroMeta(type):
    '''Metaclass for Pyro.'''

    def __new__(cls, name, parents, dct):
        dct['_singular_name'] = camel_to_snake(name)
        dct['_plural_name'] = plural(camel_to_snake(name))
        dct['_parent'] = None
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
    def attach_db(cls, db=None):
        '''Attaches a database to the Pyro environment.'''
        if db is None:
            cls._db = connect_to_database()
        else:
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
            # index - only one level of nesting allowed!
            route_name = '{:s}.{:s}.index'.format(cls._singular_name,\
                child._plural_name)
            route = '/{:s}/<resource_id>/{:s}'.format(cls._singular_name,\
                child._plural_name)
            methods = ['GET']
            callback = child._index
            routes[route_name] = {'route': route, 'methods': methods,\
                'callback': callback}
            # create
            route_name = '{:s}.{:s}.create'.format(cls._singular_name,\
                child._plural_name)
            route = '/{:s}/<resource_id>/{:s}'.format(cls._singular_name,\
                child._plural_name)
            methods = ['POST']
            callback = child._create
            routes[route_name] = {'route': route, 'methods': methods,\
                'callback': callback}
        return routes

    # -------------- CONTROLLER METHODS -----------------------------
    @classmethod
    def _index(cls, resource_id=None):
        '''List all resources.'''
        params = assemble_params(cls, 'index', resource_id, request)
        cls.before_index(params) # before hook
        if params['status_code'] > 399:
            # Error detected. EJECT! EJECT!
            return (jsonify(params['response']), params[status_code], {})
        if resource_id: # a nested resource!
            query = dict([(cls._parent._foreign_key(), ObjectId(resource_id))])
            cls._docs = cls.find_where(query)
        else:
            cls._docs = cls.all()
        params[cls._plural_name] = cls._docs
        cls.after_index(params) # after hook
        return cls._to_response(cls._docs)

    @classmethod
    def _create(cls, resource_id=None):
        '''Create a new resource.'''
        params = assemble_params(cls, 'create', resource_id, request)
        cls.before_create(params) # before hook
        if resource_id is not None: # nested create!
            parent = cls._parent.find_by_id(resource_id)
            cls._obj = cls.create(request.json, parent)
            params['resp'] = cls._to_response(cls._obj._doc)
        else:
            cls._obj = cls.create(request.json)
            params['resp'] = cls._to_response(cls._obj._doc)
        params[cls._singular_name] = cls._obj
        cls.after_create(params) # after hook
        return (params['resp'], params['status_code'], {})

    @classmethod
    def _show(cls, resource_id):
        '''Find the specified resource'''
        params = assemble_params(cls, 'show', resource_id, request)
        cls.before_show(params) # before hook
        cls._obj = cls.find_by_id(resource_id)
        if cls._obj:
            params['resp'] = cls._to_response(cls._obj._doc)
            params[cls._singular_name] = cls._obj
            params['status_code'] = 200
        else:
            resp = jsonify({})
            params['status_code'] = 404
            params['resp'] = resp
        cls.after_show(params) # after hook
        return (params['resp'], params['status_code'], {})

    @classmethod
    def _destroy(cls, resource_id):
        '''Delete the specified resource.'''
        params = assemble_params(cls, 'destroy', resource_id, request)
        cls.before_destroy(params) # before hook
        cls._obj = cls.find_by_id(resource_id)
        if cls._obj:
            params['resp'] = jsonify({})
            params[cls._obj._singular_name] = cls._obj
            cls._obj.delete()
            params['status_code'] = 200
        else:
            params['resp'] = jsonify({})
            params['status_code'] = 404
        cls.after_destroy(params) # after hook
        return (params['resp'], params['status_code'], {})

    @classmethod
    def _update(cls, resource_id):
        '''Update the specified resource.'''
        params = assemble_params(cls, 'update', resource_id, request)
        cls.before_update(params) # before hook
        cls._obj = cls.find_by_id(resource_id)
        if cls._obj:
            cls._obj.__dict__.update(request.json)
            cls._obj.save()
            params['resp'] = cls._to_response(cls._doc)
            params[cls._obj._singular_name] = cls._obj
            params['status_code'] = status_code = 200
        else:
            params['resp'] = jsonify({})
            params['status_code'] = status_code = 404
        cls.after_update(params) # after hook
        return (params['resp'], params['status_code'], {})
    # -------------- END CONTROLLER METHODS --------------------------

    # -------------- HOOK METHODS ------------------------------------
    @staticmethod
    def before_index(params):
        pass

    @staticmethod
    def after_index(params):
        pass

    @staticmethod
    def before_create(params):
        pass

    @staticmethod
    def after_create(params):
        pass

    @staticmethod
    def before_show(params):
        pass

    @staticmethod
    def after_show(params):
        pass

    @staticmethod
    def before_update(params):
        pass

    @staticmethod
    def after_update(params):
        pass

    @staticmethod
    def before_destroy(params):
        pass

    @staticmethod
    def after_destroy(params):
        pass
    # -------------- END HOOK METHODS--------------------------------

    @classmethod
    def new(cls, doc, parent_instance=None):
        '''Create a new object, but do not save to database.'''
        cls._doc = deserialize(doc)
        obj = cls(cls._doc)
        obj.before_new_model()
        cls.validate_associations(cls._doc, parent_instance)
        obj.after_new_model()
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
        if cls._parent is None: # no parent exists
            return doc
        if not parent_instance:
            if cls._parent._foreign_key() in doc: # already assigned
                return doc
        elif parent_instance.__class__ is cls._parent: # assign now
            doc[parent_instance._foreign_key()] = parent_instance._id
            return doc
        error = ('This class must belong to an instance of the {:s} class').\
                format(snake_to_class(cls._parent._singular_name))
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
    def find_where(cls, query):
        '''Find docs in collection satisfying query.'''
        collection = cls._db[cls._plural_name]
        return list(collection.find(query))

    @classmethod
    def find_by_id(cls, _id):
        _id = ObjectId(_id)
        doc = find_document(_id, cls._db[cls._plural_name])
        if doc is None:
            return False
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
        child_class._parent = cls
        cls._children.append(child_class)

    def __init__(self, doc):
        '''Consume a document and attach attributes as properties.'''
        self.__dict__.update(doc)

    def _find_parent(self):
        '''Find and attach parent.'''
        if self.has_parent:
            ParentClass = self._parent
            foreign_key = ParentClass._foreign_key()
            parent_obj = ParentClass.find_by_id(self.__dict__[foreign_key])
            self.__dict__[ParentClass._singular_name] = parent_obj

    def _find_children(self):
        '''Find and attach parent.'''
        for ChildClass in self._children:
            self.__dict__[ChildClass._plural_name] = ForeignQuery(self,\
                    ChildClass)

    @property
    def has_parent(self):
        '''Does this model belong to another model?'''
        return self._parent is not None

    def save(self):
        '''Save the current document, if there is one.'''
        self._doc.update(self.__dict__)
        if self.doc_exists:
            self._update_existing_doc()
        else:
            self._save_new_doc()
        self._finally()

    def _finally(self):
        '''Clean up, sideload parents/children/etc.'''
        self._find_parent()
        self._find_children()

    def _save_new_doc(self):
        '''Save new document to the database.'''
        self.before_save_model() # before hook
        self._doc['createdAt'] = str(datetime.now())
        self._doc['updatedAt'] = str(datetime.now())
        response = self._db[self._plural_name].insert_one(self._doc)
        self._doc['_id'] = response.inserted_id
        self.__dict__.update(self._doc)
        self.after_save_model() # after hook

    def _update_existing_doc(self):
        '''Update an existing document.'''
        self.before_update_model() # before hook
        self._doc['updatedAt'] = str(datetime.now())
        self._doc.update(self.__dict__)
        self._doc = clean_document(self._doc)
        update_document(self._doc, self._db[self._plural_name])
        self.after_update_model() # after hook

    def delete(self):
        '''Delete the current document.'''
        self.before_delete_model() # before hook
        collection = self._db[self._plural_name]
        collection.delete_one(qwrap(self._id))
        self.after_delete_model() # after hook

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

    def before_new_model(self):
        '''Override to add functionality.'''
        pass

    def after_new_model(self):
        '''Override to add functionality.'''
        pass

    def before_update_model(self):
        '''Override to add functionality.'''
        pass

    def after_update_model(self):
        '''Override to add functionality.'''
        pass

    def before_delete_model(self):
        '''Override to add functionality.'''
        pass

    def after_delete_model(self):
        '''Override to add functionality.'''
        pass

    def before_save_model(self):
        '''Override to add functionality.'''
        pass

    def after_save_model(self):
        '''Override to add functionality.'''
        pass
