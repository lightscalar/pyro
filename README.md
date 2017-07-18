# PYRO — A Lightweight Framework for Developing Quick Web APIs in Flask


## Introduction

PYRO is an opinionated framework for building quick Web APIs using Flask. It
works with a Mongo database, a Flask web server, and that's about it. The goal
is to provide a clean API for basic CRUD functionality, and serving up RESTFUL
routes to an API with minimal configuration. YMMV.


## Requirements

We require `flask`, `inflect`, `pymongo`, all of which can be easily installed
using the `pip` utility, *vel sim*.

## Models

The `Model` class is at the core of `pyro`. It provides all the
Create/Read/Update/Delete functionality that you might need, and more. To use
it, simply create a new class that inherits from Model, like this:


```python
from pyro.models import Model

class User(Model):
    pass
```

Now you have a User class.

And that's it. Now you can create an instance of a user by passing in a 
dictionary object to the `new` method.

And are back to normal here?



