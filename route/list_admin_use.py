from .tool.func import *

def list_admin_use(arg_num = 1, arg_search = 'normal'):
    with get_db_connect() as conn:
        curs = conn.cursor()

        sql_num = (arg_num * 50 - 50) if arg_num * 50 > 0 else 0

        if flask.request.method == 'POST':
            return redirect('/list/admin/auth_use/' + url_pas(flask.request.form.get('search', 'normal')) + '/1')
        else:
            if arg_search == 'normal':
                curs.execute(db_change("select who, what, time from re_admin order by time desc limit ?, 50"), [sql_num])
            else:
                curs.execute(
                    db_change("select who, what, time from re_admin where what like ? order by time desc limit ?, 50"),
                    [arg_search + "%", sql_num]
                )

            list_data = '<ul class="opennamu_ul">'

            get_list = curs.fetchall()
            for data in get_list:
                do_data = data[1]

                if ip_pas('127.0.0.1', 1) != '127.0.0.1': 
                    do_data = do_data.split(' ')
                    if do_data[0] in ('ban'):
                        do_data = do_data[0]
                    else:
                        do_data = data[1]

                list_data += '<li>' + ip_pas(data[0]) + ' | ' + html.escape(do_data) + ' | ' + data[2] + '</li>'

            list_data += '</ul>'
            list_data += next_fix('/list/admin/auth_use/' + url_pas(arg_search) + '/', arg_num, get_list)

            return easy_minify(flask.render_template(skin_check(),
                imp = [load_lang('authority_use_list'), wiki_set(), wiki_custom(), wiki_css([0, 0])],
                data = '''
                    <form method="post">
                        <input name="search">
                        <hr class="main_hr">
                        <button type="submit">''' + load_lang('search') + '''</button>
                    </form>
                    <hr class="main_hr">
                ''' + list_data,
                menu = [['other', load_lang('return')]]
            ))