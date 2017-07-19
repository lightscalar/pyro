import re
import sys
import time
from bson import ObjectId
import inflect
from ipdb import set_trace as debug
import logging
import numpy as np
from pymongo import MongoClient


# Make an inflection engine.
eng = inflect.engine()


def add_parent_id(parent_class, doc, parent_instance):
    '''Extracts parent ID and adds it to document.'''
    key = '_{:s}_id'.format(parent_class)
    doc[key] = parent_instance._id
    return doc


def plural(noun):
    '''Returns the plural of a noun.'''
    plural = eng.plural_noun(noun)
    return plural if plural else noun


def singular(noun):
    '''Returns the singular form of a noun.'''
    singular = eng.singular_noun(noun)
    return singular if singular else noun


def camel_to_snake(camel):
    '''Convert camelCase to snake_case.'''
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', camel)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def snake_to_camel(snake):
    '''Convert snake_case to camelCase.'''
    return re.sub(r'(?!^)_([a-zA-Z])', lambda m: m.group(1).upper(), snake)


def deserialize(obj, key=None):
    '''Return object if it is simple; otherwise recursively iterate through.'''
    if (type(obj) is list): # loop through elements, if list.
        nlist = []
        for el in obj:
            nlist.append(deserialize(el))
        return nlist
    elif (type(obj) is dict): # loop through key,value pairs, if dict.
        ndict = {}
        for k,v in obj.items():
            nk = camel_to_snake(k)
            ndict[nk] = deserialize(v, key=nk)
        return ndict
    else: # convert string _id to ObjectId, etc.
        if (type(obj) is str) and (re.search(r'(_id)', key)):
            # Convert into an ObjectId so we can search in Mongo!
            return ObjectId(obj)
        else:
            return obj


def serialize(obj, key=None):
    '''Return object if it is simple; otherwise recursively iterate through.'''
    if (type(obj) is list): # loop through elements
        nlist = []
        for el in obj:
            nlist.append(serialize(el))
        return nlist
    elif (type(obj) is dict): # loop through key,value pairs
        ndict = {}
        for k,v in obj.items():
            ndict[snake_to_camel(k)] = serialize(v, key=k)
        return ndict
    else: # Check to see if the bare object needs special processing.
        if (type(obj) is ObjectId) and (re.search(r'(_id)', key)):
            # Convert the ObjectId to a string so we can push through JSON.
            return str(obj)
        else:
            return obj
        if isinstance(obj, np.generic):
            return np.asscalar(obj)


def name_to_id(name):
    '''Convert resource name to foreign key id.'''
    return '_{:s}_id'.format(name)


def name_to_class(class_name, registered_classes):
    '''Returns an instance of a class given its name.'''
    for cls in registered_classes:
        if cls._name() == class_name:
            return cls
    raise ValueError('Specified class does not exist.')


def add_children_to_parent(parent_instance, child_collection_name, database,\
        registered_classes):
    '''Add a helper method to the parent instance that allows access to
       its children.'''
    child_collection = ChildCollection(parent_instance, child_collection_name,\
            database, registered_classes)
    parent_instance.__dict__[child_collection_name] = child_collection
    return parent_instance


def add_parent_to_child(ParentClass, child_instance, database):
    '''Attaches the parent to to a child in has_many relationship.'''
    foreign_key = name_to_id(ParentClass._name())
    parent_instance = ParentClass.find_by_id(child_instance.\
            __dict__[foreign_key])
    child_instance.__dict__[parent_instance._model_name] = parent_instance


class ChildCollection(object):

    def __init__(self, parent_instance, child_collection_name, database,\
            registered_classes):
        '''Create a helper class for holding on to has_many children.'''
        self._db = database
        self.parent_instance = parent_instance
        self._collection_name = child_collection_name
        self._collection = self._db[child_collection_name]
        self.registered_classes = registered_classes

    def __call__(self):
        '''Returns a generator point to the list of children.'''
        ChildClass = name_to_class(singular(self._collection_name),\
                self.registered_classes)
        query = {'_{:s}_id'.format(self.parent_instance._model_name):\
                    self.parent_instance._id}
        # WOW is this code below super inefficient; FIX later.
        return [ChildClass.find_by_id(doc['_id']) for\
                doc in self._collection.find(query)]

