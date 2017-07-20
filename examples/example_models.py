from pyro.core import Pyro


class User(Pyro):
    '''A simple user class.'''

    @classmethod
    def after_index(cls):
        print(len(cls._docs))

    @classmethod
    def after_show(cls):
        print (cls._obj._singular_name)


class Article(Pyro):
    '''An article class.'''
    pass


'''Define a has-many relationship between these guys.'''
User.has_many(Article)
