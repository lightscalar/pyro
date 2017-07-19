from example_models import *
from pyro.application import *
from pyro.database import connect_to_database


if __name__ == '__main__':

    db = connect_to_database()
    Model.register_db(db)
    user = User.create({'name': 'Matthew J. Lewis'})
    article = Article.create({'title': 'My Blog Post'}, user)
    article = Article.create({'title': 'My Other Post'}, user)
    article = Article.create({'title': 'And Yet Another'}, user)
    print(str(user._id))

    app = Application(Model)
    app.run()
