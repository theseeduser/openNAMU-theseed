from .tool.func import *

def view_random():
    with get_db_connect() as conn:
        curs = conn.cursor()

        curs.execute(db_change("" + \
            "select title from data " + \
            "where title not like 'user:%' and title not like 'category:%' and title not like 'file:%' " + \
            "order by random() limit 1" + \
        ""))
        data = curs.fetchall()
        return redirect('/w/' + url_pas(data[0][0])) if data else redirect()