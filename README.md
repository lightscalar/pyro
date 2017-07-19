# PYRO — A Lightweight Framework for Quickly Developing Web APIs in Flask

## Introduction

PYRO is an opinionated framework for quickly building Web APIs using Flask. It
requries a Mongo database, a Flask web server, and that's about it. The goal is
to provide a clean API for basic CRUD functionality, while serving up RESTFUL
routes with minimal configuration. YMMV.

## Requirements

Pyro requires `flask`, `inflect`, and `pymongo`, all of which can be easily
installed using the `pip` utility, *vel sim*. You'll also need to have a
MongoDB server running somewhere. Instructions for installing that are
available [here](https://goo.gl/pbiPSB).

## Models

### Fundamentals

The `Model` class is at the core of `pyro`. It provides all the
Create/Read/Update/Delete functionality that you might need, and more. To use
it, simply create a new class that inherits from Model, like this:


```python
from pyro.models import Model

class User(Model):
    pass
```

Now you have a `User` class. Before we do anything else, however, we'll need to
connect a database. We assume you have a MongoDB server running somewhere. If
that is not the case, get [MongoDB](https://goo.gl/pbiPSB) installed and
running on your system. Then, create a database object and attach it to the
`User` class like this:

```python
from pyro.database import connect_to_database

db = connect_to_database(database_name='my_database')
User.set_db(db)
```

Now let's create a `User` instance. We can do this by calling the `new`
method on the `User` class:

```python
user_data = {'firstName': 'Matthew', 'lastName': Lewis, 'age': 28}
user = User.new(user_data)
```

Attributes in that dictionary have now been assigned as properties on the
`user` instance. That is,

```python
user.first_name # Matthew
user.last_name  # Lewis
user.age        # 28
```

*Nota Bene*: although our dictionary used camelCase for attribute names, once
we've ingested the dictionary, everything is converted to snake_case. This
anticipates the interfacing of this elegant python code to an ugly JavaScript
front-end, where camelCase is *de rigueur*.

It is important to note that this user has not yet been saved to the database.
To do that, we need to `save` the object, like this,

```python
user.save() # -> saves it to the specified MongoDB
```

The user is now safely saved in a document in the `users` collection of the
MongoDB database. By convention, the collection name is the plural of the name
of the class name. So the `User` class is saved in the `users` collection; the
`Box` class is saved in the `boxes` collection, and so on.

We can see how many users are in the database by looking at
the *class* method `count`:

```python
User.count() # 1
```

Alternatively, we can do this all in one fell-swoop with the `create` method:

```python
user = User.create(user_data)   # this guy is instantiated AND saved to DB
```

So far, so good. Once we've saved the user to the database, we'll find a new
property on our object, `_id`:

```python
user._id # ObjectId('596e99c7378acd2ea8357ea4')
```

This is the unique `_id` that is used internally by MongoDB to identify
individual documents. If we have this `_id`, we can load a document from the
database like this:

```python
user = User.find_by_id(_id)
```

And if we find we've made a mistake in letting this user into our system, well
then, we have access to the `delete` method on the user object:

```python
user.delete() # goodbye cruel world
```

This deletes that user from the MongoDB. If we're feeling particularly
misanthropic, however, we can destroy all the users at once by calling
`delete_all()`:

```python
User.delete_all()  # well, there goes our user base
```

Since we live in an imperfect world in a Universe hurtling towards its
inevitable heat death, it may be the case that we've made a mistake and the
user instance needs updating. In that case, we can update the attributes on the
user instance, and then call its `update` method:

```python
user = User.find_by_id(_id)
user.age = 41 # slightly more accurate
user.update() # saved to database
```

### Relationships
