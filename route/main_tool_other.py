from .tool.func import *

def main_tool_other():
    with get_db_connect() as conn:
        return easy_minify(flask.render_template(skin_check(),
            imp = [load_lang('other_tool'), wiki_set(), wiki_custom(), wiki_css([0, 0])],
            data = render_simple_set('''
                <h2>''' + load_lang('record') + '''</h2>
                <ul class="opennamu_ul">
                    <li><a href="/manager/6">''' + load_lang('edit_record') + '''</a></li>
                    <li><a href="/manager/7">''' + load_lang('discussion_record') + '''</a></li>
                </ul>
                <h2>''' + load_lang('list') + '''</h2>
                <h3>''' + load_lang('admin') + '''</h3>
                <ul class="opennamu_ul">               
                    <li><a href="/admin_list">''' + load_lang('admin_list') + '''</a></li>
                    <li><a href="/list/admin/auth_use">''' + load_lang('authority_use_list') + '''</a></li>
                </ul>
                <h3>''' + load_lang('discussion') + '''</h3>
                <ul class="opennamu_ul">
                    <li><a href="/recent_discuss">''' + load_lang('recent_discussion') + '''</a></li>
                </ul>
                <h3>''' + load_lang('document') + '''</h3>
                <ul class="opennamu_ul">
                    <li><a href="/recent_change">''' + load_lang('recent_change') + '''</a></li>
                    <li><a href="/list/document/all">''' + load_lang('all_document_list') + '''</a></li>
                    <li><a href="/acl_list">''' + load_lang('acl_document_list') + '''</a></li>
                    <li><a href="/please">''' + load_lang('need_document') + '''</a></li>
                    <li><a href="/long_page">''' + load_lang('long_page') + '''</a></li>
                    <li><a href="/short_page">''' + load_lang('short_page') + '''</a></li>
                    <li><a href="/list/document/old">''' + load_lang('old_page') + '''</a></li>
                </ul>
                <h3>''' + load_lang('user') + '''</h3>
                <ul class="opennamu_ul">
                    <li><a href="/block_log">''' + load_lang('recent_ban') + '''</a></li>
                    <li><a href="/user_log">''' + load_lang('member_list') + '''</a></li>
                </ul>
                <h3>''' + load_lang('other') + '''</h3>
                <ul class="opennamu_ul">
                    <li><a href="/image_file_list">''' + load_lang('image_file_list') + '''</a></li>
                    <li><a href="/vote">''' + load_lang('vote_list') + '''</a></li>
                </ul>
                <h2>''' + load_lang('other') + '''</h2>
                <ul class="opennamu_ul">
                    <li><a href="/upload">''' + load_lang('upload') + '''</a></li>
                    <li><a href="/manager/10">''' + load_lang('search') + '''</a></li>
                </ul>
                <h2>''' + load_lang('admin') + '''</h2>
                <ul class="opennamu_ul">
                    <li><a href="/manager/1">''' + load_lang('admin_tool') + '''</a></li>
                </ul>
            '''),
            menu = 0
        ))