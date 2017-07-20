from nose.tools import assert_equals, assert_almost_equals, assert_raises
from nose import with_setup
import numpy as np
from numpy.testing import assert_array_almost_equal_nulp, assert_array_equal
from pyro.database import *
from pyro.core import *

DB_NAME = 'mjl'
db = connect_to_database(DB_NAME)
Pyro._attach_db(db)


# SETUP -----------------------------------------------------

def setup():
    pass

def teardown():
    Pyro._registry.clear()

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
        def before_new(self):
            self._doc['sekret'] = 12345
    w = Widget.new({'name': 'Sexy New Auto'})
    assert_equals(w.sekret, 12345)


@with_setup(setup, teardown)
def attached_db_test():
    assert_equals(Pyro._db.name, 'mjl')


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

