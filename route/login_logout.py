from .tool.func import *

def login_logout():
    with get_db_connect() as conn:
        flask.session.pop('state', None)
        flask.session.pop('id', None)

        return redirect('/user')