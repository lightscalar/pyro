# PYRO — A Lightweight Framework for Quickly Developing Web APIs with Flask

## Introduction

PYRO is an opinionated framework for quickly building Web APIs using Flask. It
requires a [Mongo](https://www.mongodb.com/) database, a
[Flask](http://flask.pocoo.org/), and that's about it. The goal is to provide a
clean API for basic CRUD functionality, while serving up RESTFUL routes with
minimal configuration. YMMV.

Let's see how you might create a simple RESTFUL API.

```python
from pyro.basics import *

# Let's create some data models.
class User(Pyro):
    pass

class BlogPost(Pyro):
    pass

# Specify a has_many relationship between data objects.
User.has_many(BlogPost)

# Connect a database.
Pyro.attach_db()        # defaults to locally running Mongo server...

# Launch a web server.
app = Application(Pyro)
app.run()               # -> Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
```

That's it. Now we have access to all the usual RESTFUL routes needed to create,
update, delete, and list data objects:

```unix
GET     http://127.0.0.1:5000/users                         # return list of users
POST    http://127.0.0.1:5000/users                         # creates a new user
GET     http://127.0.0.1:5000/user/<user_id>                # retrieves user <user_id>
DELETE  http://127.0.0.1:5000/user/<user_id>                # deletes user <user_id>
GET     http://127.0.0.1:5000/user/<user_id>/blog_posts     # lists user's articles
...
```

We'll talk about the details below, but that's basically it. To add your own
application logic, you can override class methods on the `User` and `Article`
classes to process data, call external libraries, or whatever you need.

## Requirements

Pyro requires `flask`, `inflect`, and `pymongo`, all of which can be easily
installed using the `pip` utility, *vel sim*. You'll also need to have a
MongoDB server running somewhere. Instructions for installing that are
available [here](https://goo.gl/pbiPSB).

## Models

### Fundamentals

The `Pyro` class is at the core of `pyro`. It handles the creation of data
models, provides a transparent interface to the database, and even handles the
routing of web API calls to avoid superfluous Create/Read/Update/Delete
boilerplate.

Before we start modeling our data, however, we need to make contact with a
database. We assume you have a MongoDB server running somewhere. If that is not
the case, get [MongoDB](https://goo.gl/pbiPSB) installed and running on your
system. Then, create a database object and attach it to the `Pyro` class like
this:

```python
from pyro.basics import Pyro

Pyro.attach_db() # without arguments, we connect to local Mongo server.
```

This will ensure that all of our data objects have access to the common Mongo
database. Now, to model some data, we simply create a new class that inherits
from the Model class, like this:

```python
class User(Pyro):
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

We can explicitly model this relationship in our database using `Pyro`'s
association helper methods.

```python
class User(Pyro):
    pass

class BlogPost(Pyro):
    pass

User.has_many(BlogPost)

user = User.create({'fullName': 'William Shakespeare'})
blog_post_one = BlogPost.create({'title': 'Hamlet'}, user)
blog_post_two = BlogPost.create({'title': 'Macbeth'}, user)
```

By declaring `User.has_many(BlogPost)` we require that a user instance be
passed into the `new` or `create` method when we are creating a `BlogPost`.
That declaration sets into motion a bunch of machinery that let's us access
related objects just as you'd expect:

```python
blog_post_one.user      # returns the parent user object!
user.blog_posts()       # returns a list of blog posts!
```

The associated blog posts are available by calling the `blog_posts` method
on the user object; note that this is derived from the name of the class by
converting it to snake case and rendering it plural. At the moment, only
`has_many` relationships are implemented.

A given data model can have several has_many relationships, but a model can
only belong to one parent. Future work will extend available association
options.

### Serializing/Deserializing

Since we anticipate using these model objects as part of a Web API of some
sort, we may eventually want to translate these objects to JSON for transport
across an http connection. We can call the `serialize` method to grab a
`dict` containing all of our data. By default, serialization does not include
any children associated with a has_many relationship; these may be included by
specifying `include_children=True`.

Pyro's serialization/deserialization protocols will automatically convert
between [Python](https://www.python.org/dev/peps/pep-0008/#naming-conventions)
and [JavaScript](http://www.j-io.org/Javascript-Naming_Conventions) naming
conventions. For the most part, you won't have to worry about serializing and
deserializing data, as Pyro handles all this. You'll only have to be concerned
about what is going on there if you need to diverge from the default behavior,
and the default behavior is exceedingly good behavior, so it is not clear why
you would do that.

## The Application

Okay, so we've got our data modeled. Now how do we create an API from these
`Pyro`-based classes? We create a Pyro `Application` instance, as we did above.
Let's reproduce that example here, and discuss in greater detail what is
going on:

```python
from pyro.basics import *

# Let's create some data models.
class User(Pyro):
    pass

class BlogPost(Pyro):
    pass

# Specify a has_many relationship between data objects.
User.has_many(BlogPost)

# Connect a database.
Pyro.attach_db()        # defaults to locally running Mongo server...

# Launch a web server.
app = Application(Pyro)
app.run()               # -> Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
```

When we create those data objects, `User` and `BlogPost`, Pyro automatically
generates the typical RESTFUL routes that allow you to create, read, update and
delete those resources, creates appropriate collections in the Mongo database,
and wires up the model relationships, if any are declared. When we create a
Pyro `Application` instance and run it, we boot up a webserver that serves up
these RESTFUL routes — all with zero boilerplate!

For the example above, the following routes are generated:

| HTTP Verb | Path | API Action | What Does It Do? |
| :-------  | :--- | :------------ | :--------------- |
| GET | /users | index  | Returns list of all users |
| POST | /users | create | Create a new user
| GET | /user/<user_id> | show | Return the user with id <user_id>|
| DELETE | /user/<user_id> | destroy | Delete the user with id <user_id>|
| GET | /user/<user_id>/blog_posts | index | Return list of <user_id>'s blog posts|
| POST | /user/<user_id>/blog_posts | create | Create a new blog post belonging to <user_id>|
| GET | /blog_posts | index  | Returns list of all users |
| POST | /blog_posts | create | Create a new blog post |
| GET | /blog_post/<blog_id> | show | Return the blog post with id <blog_id>|
| DELETE | /blog_post/<blog_id> | destroy | Delete the user with id <blog_id>|

These routes are similar to the default routes you'd get using a RESTFUL, full
stack web application framework like [Ruby on
Rails](http://guides.rubyonrails.org/routing.html). Note that Pyro supports
nested routing, but only one level deep. That is, if we created a `Comment`
data model that was a child of a `BlogPost` via `BlogPost.has_many(Comment)`,
you'd be able to access something like `/blog_post/<blog_id>/comments`, but not
`/user/<user_id>/blog_post/<blog_id>/comments` because, well, such things are
unwieldy and ultimately not very useful. So one levels of nested routing;
that's all you get.

As a concrete example, let's create a `User` instance via our API. To do this,
we simply `POST` some data to the server running at `http://localhost:5000`. We
can do this in Python using the excellent Python library
[requests](http://docs.python-requests.org/en/master/):

```python
import requests
requests.post('http://localhost:5000/users', json={'name': 'Matthew', 'age': 41})
```

Pyro routes this request to the appropriate action, creates a new `User`
object, saves it to the Mongo database, and returns a JSON version of the
object, augmented with a new primary key, `_id`. Making API requests to the
other routes work as expected. To see the list of `User`s now available:

```python
requests.get('http://localhost:5000/users') 
# [
#   {
#     "_id": "5972105e378acd73a73a1d62", 
#     "name": "Matthew"
#     "age": 41
#   }, 
# ]
```

### Oh, But I Want to Do Other Stuff

Of course you do. CRUD is necessary but not sufficient. And that is where
*hooks* come in. Before and after each API action is taken, and before and
after any model action is taken, Pyro calls a **hook method**. By default,
these hook methods do nothing at all. But by declaring your own hooks, you may
intercept data as it flows through the Pyro API to the database, process it,
augment it with more data from external APIs or libraries or — well, whatever,
really, since we're working with Python — and then let Pyro carry on with its
boilerplate business. There are two distinct types of hooks in Pyro: Model
Hooks, and Action Hooks. Let's start with model hooks.

### Model Hooks

Model hooks allow you to jump inside an instance of your data object whenever
something interesting is about to happen, or has just happened. For example,
suppose you wanted to add a timestamp to every user that is created. This can
be accomplished by overriding the `User` model's `before_save_model` method:

```python
from datetime import datetime
from pyro.basics import *

class User(Pyro):
    def before_save_model(self):
        self.current_time = str(datetime.now())
```

Et voila! Now your model has the `current_time` attribute. Since we intercepted 
the Pyro object before it was saved, this new attribute will be saved to the
database. If you'd like to work with the data after it has been saved to the
database, simply override the `after_model_save` method. The following table
summarizes the available model hooks.

| Hook Method | Description |
|-------------|-------------|
| `before_create_model` | Called after the model has been instantiated, but before it's committed to the database.|
| `after_create_model` | Called after the model has been committed to the database.|
| `before_update_model` | Called before an existing  model is updated.|
| `after_update_model` | Called after an existing model is updated.|
| `before_save_model` | Called before the model is saved — either via creation or update.|
| `after_save_model` | Called after the model is saved — either via creation or update.|
| `before_delete_model` | Called before the model is deleted.|
| `after_delete_model` | Called after the model is deleted.|

Inside a model hook you have access to the `self` instance, which allows you
access to all of the usual model capabilities, database access, *etc*.

### Action Hooks

The other type of hook available are *action hooks*. These allow you to hook 
into API actions like `index`, `show`,  and `create`. As with the model hooks,
you can hook into the actions either before or after they do their job. This 
allows you to easily implement things like server side validations. You declare
action hooks a little differently, as static methods on the corresponding 
Model class. For example, support we wanted to hook into the create action
to validate the presence of an email field before we commit the object to the
database. Such a task could be done in a model hook, but here we can 
modify the http response, the response codes, and send a sensible error
message back to the user.

```python
User(Pyro):

@staticmethod
def before_create(params):
    if 'email' not in params:
        params['status_code'] = 406
        params['resp'] = {'errors' = ['Must supply a valid email address.']}
```

        
