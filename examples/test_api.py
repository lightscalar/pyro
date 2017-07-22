import requests as rq
from example_models import *

def url(x):
    base_url = 'http://localhost:5000'
    return '{:s}/{:s}'.format(base_url, x)

data = {'firstName': 'Matthew', 'lastName': 'Lewis', 'age': 41}
resp = rq.post(url('authors'), json=data)
author = resp.json()
author_url = url('author/{:s}'.format(author['_id']))
post_book_url = url('author/{:s}/books'.format(author['_id']))
book = rq.post(post_book_url, json={'title': 'Great Gatsby'})

