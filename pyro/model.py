from ipdb import set_trace as debug

from pyro.database import *
from pyro.utils import *



class Model(object):

    def __init__(self, cls):
        '''The name of the model resource is defined in terms of class name.'''
        self._model_name = singular(cls._name())
        self._collection_name = cls._collection_name()
        self._db = cls._db
        self._cls = cls

    @classmethod
    def all(cls, db=None):
        '''Returns a list of models w.r.t a given database.'''
        return cls._db[cls._collection_name()].find()

    @classmethod
    def create(cls, doc):
        '''Creates & saves a new object to the database.'''
        obj = cls.new(doc)
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
    def _name(cls):
        '''Convenience function for returning the name of the class.'''
        name = cls.__name__.lower()
        return singular(name)

    @classmethod
    def _collection_name(cls):
        '''Name of Mongo collection associated with model.'''
        return plural(cls._name())

    @classmethod
    def new(cls, doc):
        '''Creates a new object, but does not save it to database.'''
        obj = cls(cls)
        obj._doc = deserialize(doc)
        for key, val in obj._doc.items():
            obj.__dict__[key] = val
        return obj

    @classmethod
    def find_by_id(cls, _id):
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

    def delete(self):
        '''Delete the current object from the database.'''
        self._db[self._collection_name].delete_one(qwrap(self._id))

    def save(self):
        '''Saves new object to the database.'''
        if '_id' in self.__dict__:
            raise ValueError('Please use update to update an\
                    existing document.')
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
class Session(Model):
    pass


if __name__ == '__main__':
    db = connect_to_database()
    Session.set_db(db)
