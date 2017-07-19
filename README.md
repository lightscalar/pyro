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
Create/Read/Update/Delete functionality that you might need, and more.

Before we start modeling our data, however, we need to make contact with a
database. We assume you have a MongoDB server running somewhere. If that is not
the case, get [MongoDB](https://goo.gl/pbiPSB) installed and running on your
system. Then, create a database object and attach it to the `Model` class like
this:

```python
from pyro.database import connect_to_database
from pyro.model import Model

db = connect_to_database(database_name='my_database')
Model.attach_db(db)
```

This will ensure that all of our data objects have access to the common Mongo
database. Now, to model some data, we simply create a new class that inherits
from the Model class, like this:

```python
class User(Model):
    pass
```

Et voila! Now we have a `User` class. Think of this class a factory for
creating new users, storing them in the database, retrieving them, etc. Now
let's create a `User` instance. We can do this by calling the `new` method on
the `User` class:

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
user.save() # -> saves it to the attached MongoDB
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
`delete_all`:

```python
User.delete_all()  # well, there goes our user base
```

Since we live in an imperfect world in a Universe hurtling towards its
inevitable heat death, it may be the case that we'll make a mistake and find
the user instance needs updating. In that case, we can update the offending
properties on the user instance, and then call its `update` method:

```python
user = User.find_by_id(_id)
user.age = 41   # slightly more accurate
user.save()     # saved to database
```

### Relationships

We frequently store data objects that are somehow related to one another, and
we may want to preserve this relationship in our database. A user produces many
blog posts, a company has many employees, and so on.

We can explicitly model this relationship in our database using the `Model`'s
association helper methods.

```python
class User(Model):
    pass

class BlogPost(Model):
    pass

User.has_many(BlogPost)

user = User.create({'fullName': 'William Shakespeare'})
blog_post_one = BlogPost.create({'title': 'Hamlet'}, user)
blog_post_two = BlogPost.create({'title': 'Macbeth'}, user)
```

By declaring `User.has_many(BlogPost)` we require that a user instance be
passed into the `new` or `create` method when we are creating a `BlogPost`.
That declaration sets into motion a bunch of machinery, however, that let's us
access related objects just as you'd expect:

```python
blog_post_one.user      # returns the parent user object!
user.blog_posts()       # returns a list of blog posts!
```

The associated blog posts are available by calling the `blog_posts` method
on the user object; note that this is derived from the name of the class by
converting it to snake case and rendering it plural. At the moment, only
`has_many` relationships are implemented.

A given data model can have many has_many relationships, but a model can only
belong to one parent; in other words, many-to-many relationships are not
(yet) possible.


### Serializing/Deserializing

Since we anticipate using these model objects as part of a Web API of some
sort, we may eventually want to translate these objects to JSON for transport
across an http connection. We can call the `serialize_doc` method to grab a
`dict` containing all of our data. By default, serialization does not include
any children associated with a has_many relationship; these may be included by
specifying `include_children=True`.


# API Application

Okay, so we've got our data modeled. Now how do we create an API from these
`Model` classes? We create a `pyro` `Application`.
