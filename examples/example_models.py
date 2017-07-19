from pyro.model import Model


class User(Model):
    pass


class Article(Model):
    pass


# Define a has_many relationship.
User.has_many(Article)
