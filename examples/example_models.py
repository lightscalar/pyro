from pyro.basics import *


class Author(Pyro):
    '''A simple user class.'''

    @staticmethod
    def before_index(params):
        print(params)

    @staticmethod
    def after_show(params):
        print (params['user'].name)


class Book(Pyro):
    '''An article class.'''
    pass


'''Define a has-many relationship between these guys.'''
Author.has_many(Book)
