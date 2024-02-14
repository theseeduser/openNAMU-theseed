from .tool.func import *

def view_xref(name = 'Test', xref_type = 1):
    with get_db_connect() as conn:
        curs = conn.cursor()

        if acl_check(name, 'render') == 1:
            return re_error('/ban')

        num = int(number_check(flask.request.args.get('num', '1')))
        sql_num = (num * 50 - 50) if num * 50 > 0 else 0

        if xref_type == 1:
            div = '<a href="/xref_this/' + url_pas(name) + '">(' + load_lang('link_in_this') + ')</a><hr class="main_hr">'

            data_sub = '(' + load_lang('backlink') + ')'
        else:
            div = '<a href="/xref/' + url_pas(name) + '">(' + load_lang('normal') + ')</a><hr class="main_hr">'

            data_sub = '(' + load_lang('link_in_this') + ')'

        div += '<ul class="opennamu_ul">'

        sql_insert = ['link', 'title'] if xref_type == 1 else ['title', 'link']
        curs.execute(db_change("" + \
            "select distinct " + sql_insert[0] + ", type from back " + \
            "where " + sql_insert[1] + " = ? and not type = 'no' and not type = 'nothing'" + \
            "order by type asc, " + sql_insert[0] + " asc limit ?, 50" + \
        ""), [
            name,
            sql_num
        ])

        data_list = curs.fetchall()
        for data in data_list:
            div += '<li><a href="/w/' + url_pas(data[0]) + '">' + html.escape(data[0]) + '</a>'

            if data[1]:
                div += ' (' + data[1] + ')'

            curs.execute(db_change("select title from back where title = ? and type = 'include'"), [data[0]])
            db_data = curs.fetchall()
            if db_data:
                div += ' <a class="opennamu_link_inter" href="/xref/' + url_pas(data[0]) + '">(' + load_lang('backlink') + ')</a>'

            div += '</li>'

        div += '</ul>' + next_fix('/xref/' + url_pas(name) + '?change=' + str(xref_type) + '&num=', num, data_list)

        return easy_minify(flask.render_template(skin_check(),
            imp = [name, wiki_set(), wiki_custom(), wiki_css([data_sub, 0])],
            data = div,
            menu = [['w/' + url_pas(name), load_lang('return')], ['xref_reset/' + url_pas(name), load_lang('reset_backlink')]]
        ))