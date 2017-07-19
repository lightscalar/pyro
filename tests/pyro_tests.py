from nose.tools import assert_equals, assert_almost_equals, assert_raises
from nose import with_setup
import numpy as np
from numpy.testing import assert_array_almost_equal_nulp, assert_array_equal
from pyro.database import *
from pyro.core import *

DB_NAME = 'mjl'
db = connect_to_database(DB_NAME)


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
def new_widget_test():
    class Widget(Pyro): pass
    data = {'name': 'My Widget', 'age': 43, 'feet': False}
    widget = Widget.new(data)
    assert_equals(widget.name, 'My Widget')


@with_setup(setup, teardown)
def new_widget_test():
    class Widget(Pyro): pass




