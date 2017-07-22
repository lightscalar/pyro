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


def snake_to_class(string):
    '''Turn snake_case into ClassCase.'''
    cameled = snake_to_camel(string)
    return cameled[0].upper() + cameled[1:]


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


class ForeignQuery(object):
    '''Returns an object that will make a defined query into the specified
       collection.'''

    def __init__(self, parent_instance, ChildClass):
        self._db = parent_instance._db
        self.parent = parent_instance
        self.ChildClass = ChildClass

    def __call__(self, return_objects=False):
        foreign_key = self.parent._foreign_key()
        parent_id = self.parent._id
        collection = self._db[self.ChildClass._plural_name]
        children_docs = collection.find({foreign_key: parent_id})
        if return_objects:
            return self.ChildClass.to_objects(children_docs)
        else:
            return list(children_docs)


def assemble_params(Class, action, resource_id, request):
    '''Create a convenient parameter dict for hook methods.'''
    params = {}
    if resource_id is not None:
        if action in ['index', 'create'] and resource_id:
            resource_name = Class._parent._foreign_key()
        else:
            resource_name = Class._foreign_key()
        params[resource_name] = resource_id
    params['action'] = action
    params['request_data'] = request.json
    params['request'] = request
    params['class'] = Class
    return params


def clean_document(doc):
    '''Eliminate query classes from the documents. (HACK!)'''
    eliminables = []
    for k,v in doc.items():
        if str(type(v)) == "<class 'pyro.utils.ForeignQuery'>":
            eliminables.append(k)
    for k in eliminables:
        del doc[k]
    return doc


def create_model_params(cls=None, obj=None,  doc=None, parent=None):
    '''Create params dict for model hooks.'''
    params = {}
    params['Class'] = cls
    params[cls._singular_name] = doc
    if obj:
        params[obj._singular_name] = obj
    if parent is not None:
        params[parent_instance._singular_name] = parent_instance
    return params
