from nose.tools import assert_equals, assert_almost_equals, assert_raises
from nose import with_setup
import numpy as np
from numpy.testing import assert_array_almost_equal_nulp, assert_array_equal
import requests
from pyro.database import *
from pyro.core import *
from test_server import *

DB_NAME = 'mjl'
Pyro.attach_db()


# SETUP -----------------------------------------------------
def setup():
    pass


def teardown():
    Pyro._registry.clear()
    Author.delete_all()
    Book.delete_all()


# BEGIN TESTS ------------------------------------------------------
@with_setup(setup, teardown)
def model_name_test():
    class Widget(Pyro): pass
    assert_equals(Widget._singular_name, 'widget')


@with_setup(setup, teardown)
def registry_test():
    class Widget(Pyro): pass
    class User(Pyro): pass
    class Machine(Pyro): pass
    registered_classes = [x._singular_name for x in list(Pyro)]
    registered_classes.sort()
    assert_equals(registered_classes, ['machine', 'user', 'widget'])


@with_setup(setup, teardown)
def empty_doc_test():
    class Widget(Pyro): pass
    assert Widget._doc is None


@with_setup(setup, teardown)
def new_widget_test():
    class Widget(Pyro): pass
    data = {'name': 'My Widget', 'age': 43, 'feet': False}
    widget = Widget.new(data)
    assert_equals(widget.name, 'My Widget')


@with_setup(setup, teardown)
def before_new_hook_test():
    class Widget(Pyro):
        def before_new_model(self):
            self.sekret = 12345
    w = Widget.new({'name': 'Sexy New Auto'})
    assert_equals(w.sekret, 12345)


@with_setup(setup, teardown)
def update_object():
    class User(Pyro): pass
    User.delete_all()
    u = User.new({'firstName': 'Matthew', 'age': 34})
    u.save()
    assert_equals(User.to_objects(User.all())[0].age, 34)
    u.age = 41
    u.save()
    assert_equals(User.to_objects(User.all())[0].age, 41)
    u.delete()
    assert_equals(list(User.all()), [])


@with_setup(setup, teardown)
def has_many_test():
    class Author(Pyro): pass
    class Book(Pyro): pass
    Author.delete_all()
    Book.delete_all()
    Author.has_many(Book)
    mjl = Author.create({'firstName': 'Matthew J. Lewis', 'age': 37})
    macbeth = Book.create({'title': 'Macbeth', 'pages': 432}, mjl)
    hamlet = Book.create({'title': 'Hamlet', 'pages': 432}, mjl)
    thesun = Book.create({'title': 'The Sun Also Rises', 'pages': 432}, mjl)
    assert_equals(len(mjl.books()), 3)
    Author.delete_all()
    Book.delete_all()


# THESE TESTS REQUIRE THE TEST SERVER TO BE RUNNING.
author_data = {'firstName': 'Matthew', 'lastName': 'Lewis', 'age': 41}
book_data = [{'title': 'Moby-Dick', 'rating': 4.8},
             {'title': 'Ulysses', 'rating': 4.9}]
def add_author(data):
    resp = requests.post(url('authors'), json=data)
    return resp.json()

@with_setup(setup, teardown)
def api_index_test():
    # NOTE: Assumes test server is running!!!
    index_resp = requests.get(url('authors'))
    assert_equals(index_resp.json(), [])


@with_setup(setup, teardown)
def create_resource_test():
    # NOTE: Assumes test server is running!!!
    author = add_author(author_data)
    index_resp = requests.get(url('authors'))
    assert_equals(len(index_resp.json()), 1)
    assert_equals(index_resp.json()[0]['firstName'], 'Matthew')


@with_setup(setup, teardown)
def show_resource_test():
    # NOTE: Assumes test server is running!!!
    author = add_author(author_data)
    show_url = url('author/{:s}'.format(author['_id']))
    show_resp = requests.get(show_url)
    assert_equals(show_resp.json()['lastName'], author_data['lastName'])


@with_setup(setup, teardown)
def show_absent_resource_test():
    # NOTE: Assumes test server is running!!!
    bad_id = '59723b49378acd98d2c4910b'
    show_url = url('author/{:s}'.format(bad_id))
    show_resp = requests.get(show_url)
    assert_equals(show_resp.status_code, 404)
    # assert_equals(show_resp.json()['lastName'], author_data['lastName'])


@with_setup(setup, teardown)
def update_resource_test():
    # NOTE: Assumes test server is running!!!
    author = add_author(author_data)
    fixed_author_data = {'age': 28, 'favoriteAnimal': 'amoeba'}
    update_url = url('author/{:s}'.format(author['_id']))
    update_resp = requests.put(update_url, json=fixed_author_data)
    assert_equals(update_resp.json()['age'], 28)
    show_url = url('author/{:s}'.format(author['_id']))
    get_resp = requests.get(update_url)
    assert_equals(update_resp.json()['age'], 28)
    assert_equals(update_resp.json()['favoriteAnimal'], 'amoeba')


@with_setup(setup, teardown)
def delete_resource_test():
    # NOTE: Assumes test server is running!!!
    author = add_author(author_data)
    del_url = url('author/{:s}'.format(author['_id']))
    del_resp = requests.delete(del_url)
    assert_equals(del_resp.status_code, 200)
    index_resp = requests.get(url('authors'))
    assert_equals(index_resp.json(), [])
    del_resp = requests.delete(del_url)
    assert_equals(del_resp.status_code, 404)


@with_setup(setup, teardown)
def nested_resource_test():
    # NOTE: Assumes test server is running!!!
    author = add_author(author_data)
    create_book_url = url('author/{:s}/books'.format(author['_id']))
    book_resps = []
    for book in book_data:
        resp = requests.post(create_book_url, json=book)
        book_resps.append(resp.json())
    assert_equals(book_resps[0]['title'], 'Moby-Dick')
    assert_equals(book_resps[1]['title'], 'Ulysses')


