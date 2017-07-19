from nose.tools import assert_equals, assert_almost_equals, assert_raises
from nose import with_setup
import numpy as np
from numpy.testing import assert_array_almost_equal_nulp, assert_array_equal
from pyro.database import *
from pyro.model import *

DB_NAME = 'mjl'
db = connect_to_database(DB_NAME)
db.widgets.delete_many({})
db.workers.delete_many({})
Model.set_db(db)


# SETUP -----------------------------------------------------

def setup():
    pass

def teardown():
    pass


# BEGIN TESTS ------------------------------------------------------
def model_name_test():
    class Widget(Model): pass
    assert_equals(Widget._name(), 'widget')


def db_name_config_test():
    class Widget(Model): pass
    assert_equals(Widget._db.name, 'mjl')


def widget_count_test():
    class Widget(Model): pass
    assert_equals(Widget.count(), 0)


def new_widget_test():
    class Widget(Model): pass
    data = {'name': 'My Widget', 'age': 43, 'feet': False}
    widget = Widget.new(data)
    assert_equals(widget.name, 'My Widget')
    assert_equals(widget.age, 43)
    assert_equals(widget.feet, False)
    assert_equals(widget._model_name, 'widget')
    assert_equals(widget._collection_name, 'widgets')
    assert '_id' not in widget.__dict__
    widget.save()
    assert '_id' in widget.__dict__
    widget.delete()
    assert_equals(Widget.count(), 0)


def create_widget_test():
    class Widget(Model): pass
    data = {'name': 'My Widget', 'age': 43, 'feet': False}
    widget = Widget.create(data)
    assert_equals(Widget.count(), 1)
    assert ('_id' in widget.__dict__)
    assert ('_doc' in widget.__dict__)
    widget.delete()


def delete_widget_test():
    class Widget(Model): pass
    data = {'name': 'My Widget', 'age': 43, 'feet': False}
    widget = Widget.create(data)
    assert_equals(Widget.count(), 1)
    widget.delete()
    assert_equals(Widget.count(), 0)


def find_by_id_test():
    class Worker(Model): pass
    data = {'firstName': 'Matthew', 'lastName': 'Lewis'}
    worker = Worker.create(data)
    _id = worker._id
    worker_found = Worker.find_by_id(_id)
    assert_equals(worker_found.first_name, worker.first_name)
    worker_found.delete()


def delete_all_test():
    class Worker(Model): pass
    data = {'firstName': 'Matthew', 'lastName': 'Lewis'}
    worker = Worker.create(data)
    worker = Worker.create(data)
    worker = Worker.create(data)
    assert_equals(Worker.count(), 3)
    Worker.delete_all()
    assert_equals(Worker.count(), 0)


def serialize_test():
    class Worker(Model): pass
    data = {'firstName': 'Matthew', 'lastName': 'Lewis'}
    worker = Worker.create(data)
    doc = worker.serialize_doc()
    assert 'firstName' in doc
    assert 'lastName' in doc
    assert type(doc['_id']) is str


def update_test():
    class Worker(Model): pass
    data = {'firstName': 'Matthew', 'age': 28}
    worker = Worker.create(data)
    worker.age = 41
    worker.update()
    updated_worker = Worker.find_by_id(worker._id)
    assert_equals(updated_worker.age, 41)


def has_many_test():
    class Author(Model): pass
    class Book(Model): pass
    Author.delete_all()
    Book.delete_all()
    Author.has_many(Book)
    shakespeare = Author.create({'name': 'William Shakespeare'})
    hamlet = Book.create({'title': 'Hamlet', 'length': 145}, shakespeare)
    macbeth = Book.create({'title': 'Macbeth', 'length': 125}, shakespeare)
    assert_equals(Author.count(), 1)
    assert_equals(Book.count(), 2)
    assert_equals(macbeth.author.name, 'William Shakespeare')
    assert_equals(len(shakespeare.books()), 2)
    assert_equals(list(shakespeare.books())[0].title, 'Hamlet')


def multiple_children_tests():
    class Author(Model): pass
    class Book(Model): pass
    class SuperFan(Model): pass
    Author.delete_all()
    Book.delete_all()
    SuperFan.delete_all()
    Author.has_many(Book)
    Author.has_many(SuperFan)
    shakespeare = Author.create({'name': 'William Shakespeare'})
    hamlet = Book.create({'title': 'Hamlet', 'length': 145}, shakespeare)
    macbeth = Book.create({'title': 'Macbeth', 'length': 125}, shakespeare)
    harold = SuperFan.create({'name': 'Harold Bloom'}, shakespeare)
    assert_equals(shakespeare.super_fans()[0].name, 'Harold Bloom')
    assert_equals(len(shakespeare.books()), 2)


