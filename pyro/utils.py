import re
import time
from bson import ObjectId
import inflect
from ipdb import set_trace as debug
import logging
import numpy as np
from pymongo import MongoClient


# Make an inflection engine.
eng = inflect.engine()


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
