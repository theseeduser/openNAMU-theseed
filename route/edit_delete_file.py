from .tool.func import *

def edit_delete_file(name = 'test.jpg'):
    with get_db_connect() as conn:
        curs = conn.cursor()

        ip = ip_check()
        if admin_check() == 0:
            return re_error('/ban')

        mime_type = re.search(r'([^.]+)$', name)
        if mime_type:
            mime_type = mime_type.group(1).lower()
        else:
            mime_type = 'jpg'

        file_name = re.sub(r'\.([^.]+)$', '', name)
        file_name = re.sub(r'^file:', '', file_name)

        file_all_name = sha224_replace(file_name) + '.' + mime_type
        file_directory = os.path.join(load_image_url(), file_all_name)

        if not os.path.exists(file_directory):
            return redirect('/w/' + url_pas(name))

        if flask.request.method == 'POST':
            admin_check(None, 'file del (' + name + ')')
            os.remove(file_directory)

            return redirect('/w/' + url_pas(name))
        else:
            return easy_minify(flask.render_template(skin_check(),
                imp = [name, wiki_set(), wiki_custom(), wiki_css(['(' + load_lang('file_delete') + ')', 0])],
                data = '''
                    <form method="post">
                        <img src="/image/''' + url_pas(file_all_name) + '''">
                        <hr class="main_hr">
                        <a href="/image/''' + url_pas(file_all_name) + '''">/image/''' + url_pas(file_all_name) + '''</a>
                        <hr class="main_hr">
                        <button type="submit">''' + load_lang('file_delete') + '''</button>
                    </form>
                ''',
                menu = [['w/' + url_pas(name), load_lang('return')]]
            ))