from .tool.func import *

def api_setting(name = 'markup'):
    with get_db_connect() as conn:
        curs = conn.cursor()
        
        ok_list_1 = ['markup']
        ok_list_2 = ['inter_wiki']
        
        if name in ok_list_1:
            curs.execute(db_change('select data from other where name = ?'), [name])
            rep_data = curs.fetchall()
            if rep_data:
                return flask.jsonify({ name : rep_data })
        elif name in ok_list_2:
            curs.execute(db_change("select html, plus, plus_t from html_filter where kind = ?"), [name])
            rep_data = curs.fetchall()
            if rep_data:
                return flask.jsonify({ name : rep_data })

        return flask.jsonify({})