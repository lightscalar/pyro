from pyro.basics import *


# Define our data models.
class Author(Pyro):
    pass


class Book(Pyro):
    pass


def url(x):
    base_url = 'http://localhost:5000'
    return '{:s}/{:s}'.format(base_url, x)


if __name__ == '__main__':

    Pyro.attach_db()
    Author.has_many(Book)
    Author.delete_all()
    Book.delete_all()
    app = Application(Pyro)
    app.run()
