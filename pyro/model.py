from ipdb import set_trace as debug

from pyro.database import *
from pyro.utils import *



class Model(object):

    has_many_registry = {}
    has_one_registry = {}
    belongs_to_registry = {}

    def __init__(self, cls):
        '''The name of the model resource is defined in terms of class name.'''
        self._model_name = singular(cls._name())
        self._collection_name = cls._collection_name()
        self._db = cls._db
        self._cls = cls

    def _attach_associations(self):
        '''Cycle through all registered associations and attach them.'''
        # Belongs to associations.
        if self._model_name in self.belongs_to_registry:
            ParentClass = name_to_class(self.belongs_to_registry[\
                    self._model_name], Model.__subclasses__())
            add_parent_to_child(ParentClass, self, self._db)
        # Has Many associations.
        if self._model_name in self.has_many_registry:
            child_name = self.has_many_registry[self._model_name]
            add_children_to_parent(self, child_name, self._db,\
                    Model.__subclasses__())

    @classmethod
    def all(cls, db=None):
        '''Returns a list of models w.r.t a given database.'''
        return cls._db[cls._collection_name()].find()

    @classmethod
    def create(cls, doc, parent_instance=None):
        '''Creates & saves a new object to the database.'''
        obj = cls.new(doc, parent_instance=parent_instance)
        obj = obj.save()
        return obj

    @classmethod
    def count(cls):
        return cls._db[cls._collection_name()].count()

    @classmethod
    def delete_all(cls):
        try:
            cls._db[cls._collection_name()].delete_many({})
            return True
        except:
            raise IOError('Problem deleting records from database.')

    @classmethod
    def has_many(cls, child_class):
        '''Specify a child class.'''
        cls.has_many_registry[cls._name()] = child_class._collection_name()
        cls.belongs_to_registry[child_class._name()] = cls._name()

    @classmethod
    def _name(cls):
        '''Convenience function for returning the name of the class.'''
        return singular(camel_to_snake(cls.__name__))

    @classmethod
    def _collection_name(cls):
        '''Name of Mongo collection associated with model.'''
        return plural(camel_to_snake(cls._name()))

    @classmethod
    def new(cls, doc, parent_instance=None):
        '''Creates a new object, but does not save it to database.'''
        if cls._name() in cls.belongs_to_registry.keys():
            parent_name = cls.belongs_to_registry[cls._name()]
            parent_key = name_to_id(parent_name)
            if parent_key not in doc:
                if parent_instance is None:
                    raise ValueError('You must pass in a parent instance!')
                doc = add_parent_id(cls.belongs_to_registry[cls._name()],\
                        doc, parent_instance)
        obj = cls(cls)
        obj._doc = deserialize(doc)
        for key, val in obj._doc.items():
            obj.__dict__[key] = val
        obj._attach_associations()
        return obj

    @classmethod
    def find_by_id(cls, _id):
        '''Find a document given its _id.'''
        _id = ObjectId(_id)
        doc = find_document(_id, cls._db[cls._collection_name()])
        if doc is None:
            raise ValueError('Document is not in the database.')
        else:
            return cls.new(doc)

    @classmethod
    def set_db(cls, db):
        '''Set the database to use.'''
        cls._db = db

    def _name_by_id(self):
        '''Name of foreign key name for this object.'''
        return '_{:s}._id'.format(self._model_name)

    def delete(self):
        '''Delete the current object from the database.'''
        self._db[self._collection_name].delete_one(qwrap(self._id))

    def save(self):
        '''Saves new object to the database.'''
        if '_id' in self.__dict__:
            return self.update()
        response = self._db[self._collection_name].insert_one(self._doc)
        if response.acknowledged:
            doc = self._cls.find_by_id(response.inserted_id)
            self.__dict__ = {k:v for k,v in doc.__dict__.items()}
            return doc
        else:
            raise ValueError('Problem writing to the database!')

    def serialize_doc(self):
        '''Serialize. Prep for jsonification of contents.'''
        doc = serialize(self._doc)
        return doc

    def update(self):
        '''Update existing document.'''
        for key in self.__dict__.keys():
            if key in self._doc:
                self._doc[key] = self.__dict__[key]
        try:
            response = update_document(self._doc,\
                    self._db[self._collection_name])
        except:
            raise ValueError('Cannot update the document.')


# HERE IS AN EXAMPLE MODEL DERIVED FROM THE MODEL CLASS ABOVE.
class User(Model):
    pass

class Blog(Model):
    pass


if __name__ == '__main__':
    db = connect_to_database()
    User.set_db(db)
    Blog.set_db(db)

    User.has_many(Blog)

    user = User.create({'name': 'Matthew Lewis'})
    post = Blog.create({'title': 'Magnum Opus'}, user)

