from example_models import *
from pyro.application import *
from pyro.database import connect_to_database


if __name__ == '__main__':

    # Attach the default database.
    Pyro.attach_db()

    # Insert some data into the database.
    user = User.create({'name': 'Matthew J. Lewis'})
    article = Article.create({'title': 'My Blog Post'}, user)
    article = Article.create({'title': 'My Other Post'}, user)
    article = Article.create({'title': 'My Magnum Opus'}, user)
    print(str(user._id))

    # Launch the app!
    app = Application(Pyro)
    app.run()
