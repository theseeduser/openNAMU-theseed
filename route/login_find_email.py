from .tool.func import *

# 개편 필요
def login_find_email(tool):
    with get_db_connect() as conn:
        curs = conn.cursor()
        
        if flask.request.method == 'POST':
            re_set_list = ['c_id', 'c_pw', 'c_ans', 'c_que', 'c_key', 'c_type']
        
            if tool == 'email_change':
                flask.session['c_key'] = load_random_key(32)
                flask.session['c_id'] = ip_check()
                flask.session['c_type'] = 'email_change'
            elif tool == 'pass_find':
                user_id = flask.request.form.get('id', '')
                user_email = flask.request.form.get('email', '')
        
                flask.session['c_key'] = load_random_key(32)
                flask.session['c_id'] = user_id
                flask.session['c_type'] = 'pass_find'
            else:
                if not 'c_type' in flask.session:
                    return redirect('/register')
        
            if tool != 'pass_find':
                user_email = flask.request.form.get('email', '')
                email_data = re.search(r'@([^@]+)$', user_email)
                if email_data:
                    curs.execute(db_change("select html from html_filter where html = ? and kind = 'email'"), [email_data.group(1)])
                    if not curs.fetchall():
                        for i in re_set_list:
                            flask.session.pop(i, None)
                        
                        return redirect('/email_filter')
                else:
                    for i in re_set_list:
                        flask.session.pop(i, None)
                    
                    return re_error('/error/36')
        
            curs.execute(db_change('select data from other where name = "email_title"'))
            sql_d = curs.fetchall()
            t_text = html.escape(sql_d[0][0]) if sql_d and sql_d[0][0] != '' else (wiki_set()[0] + ' key')
        
            curs.execute(db_change('select data from other where name = "email_text"'))
            sql_d = curs.fetchall()
            i_text = (html.escape(sql_d[0][0]) + '\n\nKey : ' + flask.session['c_key']) if sql_d and sql_d[0][0] != '' else ('Key : ' + flask.session['c_key'])
            
            if tool == 'pass_find':
                curs.execute(db_change("select id from user_set where id = ? and name = 'email' and data = ?"), [user_id, user_email])
                if not curs.fetchall():
                    return re_error('/error/12')
                    
                if send_email(user_email, t_text, i_text) == 0:
                    return re_error('/error/18')
        
                return redirect('/pass_find/email')
            else:
                curs.execute(db_change('select id from user_set where name = "email" and data = ?'), [user_email])
                if curs.fetchall():
                    for i in re_set_list:
                        flask.session.pop(i, None)
        
                    return re_error('/error/35')
                
                if send_email(user_email, t_text, i_text) == 0:
                    for i in re_set_list:
                        flask.session.pop(i, None)
        
                    return re_error('/error/18')
        
                flask.session['c_email'] = user_email
        
                return redirect('/pass_find/email')
        else:
            if tool == 'pass_find':
                curs.execute(db_change('select data from other where name = "password_search_text"'))
                sql_d = curs.fetchall()
                b_text = (sql_d[0][0] + '<hr class="main_hr">') if sql_d and sql_d[0][0] != '' else ''
        
                return easy_minify(flask.render_template(skin_check(),
                    imp = [load_lang('password_search'), wiki_set(), wiki_custom(), wiki_css(['(' + load_lang('email') + ')', 0])],
                    data = b_text + '''
                        <form method="post">
                            <input placeholder="''' + load_lang('id') + '''" name="id" type="text">
                            <hr class="main_hr">
                            <input placeholder="''' + load_lang('email') + '''" name="email" type="text">
                            <hr class="main_hr">
                            <button type="submit">''' + load_lang('save') + '''</button>
                        </form>
                    ''',
                    menu = [['user', load_lang('return')]]
                ))
            else:
                if tool == 'need_email' and not 'c_type' in flask.session:
                    return redirect('/register')
        
                curs.execute(db_change('select data from other where name = "email_insert_text"'))
                sql_d = curs.fetchall()
                b_text = (sql_d[0][0] + '<hr class="main_hr">') if sql_d and sql_d[0][0] != '' else ''
        
                return easy_minify(flask.render_template(skin_check(),
                    imp = [load_lang('email'), wiki_set(), wiki_custom(), wiki_css([0, 0])],
                    data = '''
                        <a href="/email_filter">(''' + load_lang('email_filter_list') + ''')</a>
                        <hr class="main_hr">
                        ''' + b_text + '''
                        <form method="post">
                            <input placeholder="''' + load_lang('email') + '''" name="email" type="text">
                            <hr class="main_hr">
                            <button type="submit">''' + load_lang('save') + '''</button>
                        </form>
                    ''',
                    menu = [['user', load_lang('return')]]
                ))