'''Routines for dealing with Mongo databases.'''
import numpy as np
from bson import ObjectId
import numpy as np
import time
from pymongo import MongoClient
import logging
from ipdb import set_trace as debug


def connect_to_database(database_name='dev'):
    '''Establish a connection with the specified database.'''
    try:
        client = MongoClient()
        database = client[database_name]
    except:
        raise IOError('Cannot connect to Mongo DB. Is it running?')
    return database


def created_at():
    '''Return a nice date/time string.'''
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())


def unix_time_in_microseconds():
    '''Return current POSIX epoch in microseconds, as a 64-bit integer.'''
    return np.int64(time.time() * 1e6)


def q(record):
    return record['_id']


def qry(record):
    '''Return a query object for the specified record.'''
    return {'_id': q(record)}


def qwrap(_id):
    '''Wrap an _id object in a query dict.'''
    return {'_id': _id}


def get_latest(record, collection):
    '''Get the latest version of the record.'''
    return collection.find_one(qry(record))


def find_unique_resource(collection):
    '''Returns the single object present in the collection.'''
    the_object = collection.find_one()


def update_document(document, collection):
    '''Update the given document in the collection.'''
    query = {'_id': document['_id']}
    return collection.update_one(query, {'$set': document}, upsert=False)


def find_document(document_id, collection):
    ''' Find a document in a collection given a document_id.'''
    query = {'_id': string_to_obj(document_id)}
    return collection.find_one(query)


def find_inserted_document(insertion_response, collection):
    '''Grab the recently inserted document (now with _id, etc.)'''
    if (insertion_response) and (insertion_response.acknowledged):
        doc = collection.find_one({'_id': insertion_response.inserted_id})
    else:
        doc = None
    return doc


def string_to_obj(string):
    return ObjectId(string)


def goodify(obj):
    '''Loop through a mongo object and convert '_id' field to string.'''
    if '_id' in obj:
        obj['_id'] = str(obj['_id'])
    return obj


def serialize_mongo(result):

    # If it is a list, iterate over it.
    if type(result) == list:
        out = []
        for obj in result:
            out.append(goodify(obj))
        return out
    else:
        out = goodify(result)
    return out


