import requests as rq
from example_models import *

# Clean up the database.
Pyro.attach_db()
User.delete_all()
Article.delete_all()

user = User.create({'firstName': 'Hugo', 'lastName': 'Lewis'})
article = Article.create({'title': 'Bus'}, user)

def url(x):
    base_url = 'http://localhost:5000'
    return '{:s}/{:s}'.format(base_url, x)

data = {'firstName': 'Matthew J. Lewis', 'age': 41}
rq.post(url('users'), data=data)
