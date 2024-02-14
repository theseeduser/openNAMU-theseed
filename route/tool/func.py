# Init
import os
import sys
import platform
import json
import smtplib
import zipfile
import shutil
import logging
import random
import ipaddress

import email.mime.text
import email.utils
import email.header

import urllib.request

# Init-Version
version_list = json.loads(open('version.json', encoding = 'utf8').read())

print('Version : ' + version_list['beta']['r_ver'])
print('DB set version : ' + version_list['beta']['c_ver'])
print('Skin set version : ' + version_list['beta']['s_ver'])
print('----')

# Init-PIP_Install
data_up_date = 1
if os.path.exists(os.path.join('data', 'version.json')):
    data_load_ver = open(os.path.join('data', 'version.json'), encoding = 'utf8').read()
    if data_load_ver == version_list['beta']['r_ver']:
        data_up_date = 0

if data_up_date == 1:
    with open(os.path.join('data', 'version.json'), 'w', encoding = 'utf8') as f:
        f.write(version_list['beta']['r_ver'])
    
    if platform.system() in ('Linux', 'Windows'):
        if platform.python_implementation() == 'PyPy':
            os.system(
                'pypy' + ('3' if platform.system() != 'Windows' else '') + ' ' + \
                '-m pip install --upgrade --user -r requirements.txt'
            )
        else:
            os.system(
                'python' + ('3' if platform.system() != 'Windows' else '') + ' ' + \
                '-m pip install --upgrade --user -r requirements.txt'
            )
        
        print('----')
        try:
            os.execl(sys.executable, sys.executable, *sys.argv)
        except:
            pass

        try:
            os.execl(sys.executable, '"' + sys.executable + '"', *sys.argv)
        except:
            print('Error : restart failed')
            raise
    else:
        print('Error : automatic installation is not supported.')
        print('Help : try "python3 -m pip install -r requirements.txt"')
else:
    print('PIP check pass')
    
print('----')

# Init-Load
from .func_render import *

from diff_match_patch import diff_match_patch

import waitress

import werkzeug.routing
import werkzeug.debug

import flask

import requests

import pymysql

if sys.version_info < (3, 6):
    import sha3

# Init-Global
global_lang = {}
global_wiki_set = {}

global_db_set = ''

conn = ''

# Func
# Func-main
def load_conn(data):
    global conn

    conn = data
    
def do_db_set(db_set):
    global global_db_set
    
    global_db_set = db_set
    
# Func-init
def get_init_set_list(need = 'all'):
    init_set_list = {
        'host' : {
            'display' : 'Host',
            'require' : 'conv',
            'default' : '0.0.0.0'
        }, 'port' : {
            'display' : 'Port',
            'require' : 'conv',
            'default' : '3000'
        }, 'language' : {
            'display' : 'Language',
            'require' : 'select',
            'default' : 'ko-KR',
            'list' : ['ko-KR', 'en-US']
        }, 'markup' : {
            'display' : 'Markup',
            'require' : 'select',
            'default' : 'namumark',
            'list' : ['namumark', 'markdown', 'custom', 'raw']
        }, 'encode' : {
            'display' : 'Encryption method',
            'require' : 'select',
            'default' : 'sha3',
            'list' : ['sha3', 'sha3-salt', 'sha3-512', 'sha3-512-salt']
        }
    }
    
    if need == 'all':
        return init_set_list
    else:
        return init_set_list[need]

class get_db_connect:
    # 임시 DB 커넥션 동작 구조
    # Init 파트
    # DB 커넥트(get_db_connect_old) -> func.py로 conn 넘겨줌
    # route 파트
    # DB 새로 커넥트 -> func.py에서 쓰던 conn은 conn_sub로 보관 ->
    # func.py로 conn 넘겨줌 -> 모든 라우터 과정이 끝나면 conn_sub를 다시 func.py에 conn으로 넘겨줌 ->
    # DB 커넥트 종료
    def __init__(self):
        global global_db_set
        global conn
        
        self.conn_sub = conn
        self.db_set = global_db_set
        
    def __enter__(self):
        if self.db_set['type'] == 'sqlite':
            self.conn = sqlite3.connect(
                self.db_set['name'] + '.db',
                check_same_thread = False,
                isolation_level = None
            )
            self.conn.execute('pragma journal_mode = wal')
        else:
            self.conn = pymysql.connect(
                host = self.db_set['mysql_host'],
                user = self.db_set['mysql_user'],
                password = self.db_set['mysql_pw'],
                charset = 'utf8mb4',
                port = int(self.db_set['mysql_port']),
                autocommit = True
            )
            curs = self.conn.cursor()

            self.conn.select_db(self.db_set['name'])

        load_conn(self.conn)
        return self.conn
    
    def __exit__(self, exc_type, exc_value, traceback):
        load_conn(self.conn_sub)
        self.conn.close()

class class_check_json:
    def do_check_set_json():
        if os.getenv('NAMU_DB') or os.getenv('NAMU_DB_TYPE'):
            set_data = {}
            set_data['db'] = os.getenv('NAMU_DB') if os.getenv('NAMU_DB') else 'data'
            set_data['db_type'] = os.getenv('NAMU_DB_TYPE') if os.getenv('NAMU_DB_TYPE') else 'sqlite'
        else:
            if os.path.exists(os.path.join('data', 'set.json')):
                db_set_list = ['db', 'db_type']
                set_data = json.loads(open(
                    os.path.join('data', 'set.json'), 
                    encoding = 'utf8'
                ).read())
                for i in db_set_list:
                    if not i in set_data:
                        os.remove(os.path.join('data', 'set.json'))
                        
                        break
            
            if not os.path.exists(os.path.join('data', 'set.json')):
                set_data = {}
                normal_db_type = ['sqlite', 'mysql']

                print('DB type (' + normal_db_type[0] + ') [' + ', '.join(normal_db_type) + '] : ', end = '')
                data_get = str(input())
                if data_get == '' or not data_get in normal_db_type:
                    set_data['db_type'] = 'sqlite'
                else:
                    set_data['db_type'] = data_get

                all_src = []
                if set_data['db_type'] == 'sqlite':
                    for i_data in os.listdir("."):
                        f_src = re.search(r"(.+)\.db$", i_data)
                        if f_src:
                            all_src += [f_src.group(1)]

                print('DB name (data) [' + ', '.join(all_src) + '] : ', end = '')

                data_get = str(input())
                if data_get == '':
                    set_data['db'] = 'data'
                else:
                    set_data['db'] = data_get

                with open(os.path.join('data', 'set.json'), 'w', encoding = 'utf8') as f:
                    f.write(json.dumps(set_data))

        print('DB name : ' + set_data['db'])
        print('DB type : ' + set_data['db_type'])
        
        data_db_set = {}
        data_db_set['name'] = set_data['db']
        data_db_set['type'] = set_data['db_type']

        return data_db_set

    def do_check_mysql_json(data_db_set):
        if os.path.exists(os.path.join('data', 'mysql.json')):
            db_set_list = ['user', 'password', 'host', 'port']
            set_data = json.loads(
                open(
                    os.path.join('data', 'mysql.json'),
                    encoding = 'utf8'
                ).read()
            )
            for i in db_set_list:
                if not i in set_data:
                    os.remove(os.path.join('data', 'mysql.json'))
                    
                    break

            set_data_mysql = set_data

        if not os.path.exists(os.path.join('data', 'mysql.json')):
            set_data_mysql = {}

            print('DB user ID : ', end = '')
            set_data_mysql['user'] = str(input())

            print('DB password : ', end = '')
            set_data_mysql['password'] = str(input())

            print('DB host (localhost) : ', end = '')
            set_data_mysql['host'] = str(input())
            if set_data_mysql['host'] == '':
                set_data_mysql['host'] = 'localhost'

            print('DB port (3306) : ', end = '')
            set_data_mysql['port'] = str(input())
            if set_data_mysql['port'] == '':
                set_data_mysql['port'] = '3306'

            with open(
                os.path.join('data', 'mysql.json'), 
                'w', 
                encoding = 'utf8'
            ) as f:
                f.write(json.dumps(set_data_mysql))

        data_db_set['mysql_user'] = set_data_mysql['user']
        data_db_set['mysql_pw'] = set_data_mysql['password']
        if 'host' in set_data_mysql:
            data_db_set['mysql_host'] = set_data_mysql['host']
        else:
            data_db_set['mysql_host'] = 'localhost'

        if 'port' in set_data_mysql:
            data_db_set['mysql_port'] = set_data_mysql['port']
        else:
            data_db_set['mysql_port'] = '3306'
            
        return data_db_set
    
    def __init__(self):
        self.data_db_set = {}
            
    def __new__(self):
        self.data_db_set = self.do_check_set_json()
        if self.data_db_set['type'] == 'mysql':
            self.data_db_set = self.do_check_mysql_json(self.data_db_set)
        
        return self.data_db_set

def get_db_table_list():
    # Init-Create_DB
    # DB 테이블 구조
    
    # --이거 개편한다더니 도대체 언제?--
    create_data = {}

    # 폐지 예정 (data_set으로 통합)
    create_data['data_set'] = ['doc_name', 'doc_rev', 'set_name', 'set_data']
    
    create_data['data'] = ['title', 'data', 'type']
    create_data['history'] = ['id', 'title', 'data', 'date', 'ip', 'send', 'leng', 'hide', 'type']
    create_data['rc'] = ['id', 'title', 'date', 'type']
    create_data['acl'] = ['title', 'data', 'type']

    # 개편 예정 (data_link로 변경)
    create_data['back'] = ['title', 'link', 'type']

    # 폐지 예정 (topic_set으로 통합) [가장 시급]
    create_data['topic_set'] = ['thread_code', 'set_name', 'set_id', 'set_data']

    create_data['rd'] = ['title', 'sub', 'code', 'date', 'band', 'stop', 'agree', 'acl']
    create_data['topic'] = ['id', 'data', 'date', 'ip', 'block', 'top', 'code']

    # 폐지 예정 (user_set으로 통합)
    create_data['rb'] = ['block', 'end', 'today', 'blocker', 'why', 'band', 'login', 'ongoing']
    create_data['scan'] = ['user', 'title', 'type']

    # 개편 예정 (wiki_set과 wiki_filter과 wiki_vote으로 변경)
    create_data['other'] = ['name', 'data', 'coverage']
    create_data['html_filter'] = ['html', 'kind', 'plus', 'plus_t']
    create_data['vote'] = ['name', 'id', 'subject', 'data', 'user', 'type', 'acl']

    # 개편 예정 (auth_list와 auth_log로 변경)
    create_data['alist'] = ['name', 'acl']
    create_data['re_admin'] = ['who', 'what', 'time']

    # 개편 예정 (user_notice와 user_agent로 변경)
    create_data['alarm'] = ['name', 'data', 'date']
    create_data['ua_d'] = ['name', 'ip', 'ua', 'today', 'sub']

    create_data['user_set'] = ['name', 'id', 'data']

    create_data['bbs_set'] = ['set_name', 'set_code', 'set_id', 'set_data']
    create_data['bbs_data'] = ['set_name', 'set_code', 'set_id', 'set_data']
    
    return create_data

def update(ver_num, set_data):
    curs = conn.cursor()

    print('----')
    # 업데이트 하위 호환 유지 함수

    if ver_num < 3160027:
        print('Add init set')
        set_init()

    if ver_num < 3170002:
        curs.execute(db_change("select html from html_filter where kind = 'extension'"))
        if not curs.fetchall():
            for i in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                curs.execute(db_change(
                    "insert into html_filter (html, kind) values (?, 'extension')"
                ), [i])

    if ver_num < 3170400:
        curs.execute(db_change("select title, sub, code from topic where id = '1'"))
        for i in curs.fetchall():
            curs.execute(db_change(
                "update topic set code = ? where title = ? and sub = ?"
            ), [
                i[2], 
                i[0], 
                i[1]
            ])
            curs.execute(db_change(
                "update rd set code = ? where title = ? and sub = ?"
            ), [
                i[2], 
                i[0], 
                i[1]
            ])

    if ver_num < 3171800:
        curs.execute(db_change("select data from other where name = 'recaptcha'"))
        change_rec = curs.fetchall()
        if change_rec and change_rec[0][0] != '':
            new_rec = re.search(r'data-sitekey="([^"]+)"', change_rec[0][0])
            if new_rec:
                curs.execute(db_change(
                    "update other set data = ? where name = 'recaptcha'"
                ), [new_rec.group(1)])
            else:
                curs.execute(db_change("update other set data = '' where name = 'recaptcha'"))
                curs.execute(db_change("update other set data = '' where name = 'sec_re'"))
    
    if  ver_num < 3172800 and \
        set_data['db_type'] == 'mysql':
        get_data_mysql = json.loads(open('data/mysql.json', encoding = 'utf8').read())
        
        with open('data/mysql.json', 'w') as f:
            f.write('{ "user" : "' + get_data_mysql['user'] + '", "password" : "' + get_data_mysql['password'] + '", "host" : "localhost" }')

    if ver_num < 3183603:
        curs.execute(db_change("select block from ban where band = 'O'"))
        for i in curs.fetchall():
            curs.execute(db_change(
                "update ban set block = ?, band = 'regex' where block = ? and band = 'O'"
            ), [
                '^' + i[0].replace('.', '\\.'),
                i[0]
            ])

        curs.execute(db_change("select block from rb where band = 'O'"))
        for i in curs.fetchall():
            curs.execute(db_change(
                "update rb set block = ?, band = 'regex' where block = ? and band = 'O'"
            ), [
                '^' + i[0].replace('.', '\\.'),
                i[0]
            ])

    if ver_num < 3190201:
        today_time = get_time()

        curs.execute(db_change("select block, end, why, band, login from ban"))
        for i in curs.fetchall():
            curs.execute(db_change(
                "insert into rb (block, end, today, why, band, login, ongoing) " + \
                "values (?, ?, ?, ?, ?, ?, ?)"
            ), [
                i[0],
                i[1],
                today_time,
                i[2],
                i[3],
                i[4],
                '1'
            ])

    if ver_num < 3191301:
        curs.execute(db_change('' + \
            'select id, title, date from history ' + \
            'where not title like "user:%" ' + \
            'order by date desc ' + \
            'limit 50' + \
        ''))
        data_list = curs.fetchall()
        for get_data in data_list:
            curs.execute(db_change(
                "insert into rc (id, title, date, type) values (?, ?, ?, 'normal')"
            ), [
                get_data[0], 
                get_data[1],
                get_data[2]
            ])

    if ver_num < 3202400:
        curs.execute(db_change("select data from other where name = 'update'"))
        get_data = curs.fetchall()
        if get_data and get_data[0][0] == 'master':
            curs.execute(db_change("update other set data = 'beta' where name = 'update'"), [])

    if ver_num < 3202600:
        curs.execute(db_change("select name, regex, sub from filter"))
        for i in curs.fetchall():
            curs.execute(db_change(
                "insert into html_filter (html, kind, plus, plus_t) " + \
                "values (?, 'regex_filter', ?, ?)"
            ), [
                i[0], 
                i[1],
                i[2]
            ])

        curs.execute(db_change("select title, link, icon from inter"))
        for i in curs.fetchall():
            curs.execute(db_change(
                "insert into html_filter (html, kind, plus, plus_t) " + \
                "values (?, 'inter_wiki', ?, ?)"), [
                i[0], 
                i[1],
                i[2]
            ])

    if ver_num < 3203400:
        curs.execute(db_change("select user, css from custom"))
        for i in curs.fetchall():
            curs.execute(db_change(
                "insert into user_set (name, id, data) values ('custom_css', ?, ?)"
            ), [
                re.sub(r' \(head\)$', '', i[0]), 
                i[1]
            ])

    if ver_num < 3205500:
        curs.execute(db_change("select title, decu, dis, view, why from acl"))
        for i in curs.fetchall():
            curs.execute(db_change(
                "insert into acl (title, data, type) values (?, ?, ?)"
            ), [i[0], i[1], 'decu'])
            curs.execute(db_change(
                "insert into acl (title, data, type) values (?, ?, ?)"
            ), [i[0], i[2], 'dis'])
            curs.execute(db_change(
                "insert into acl (title, data, type) values (?, ?, ?)"
            ), [i[0], i[3], 'view'])
            curs.execute(db_change(
                "insert into acl (title, data, type) values (?, ?, ?)"
            ), [i[0], i[4], 'why'])

    if ver_num < 3300101:
        # 캐시 초기화
        curs.execute(db_change('delete from cache_data'))
    
    if ver_num < 3300301:
        # regex_filter 오류 해결
        curs.execute(db_change(
            'delete from html_filter where kind = "regex_filter" and html is null'
        ))
        
    if ver_num < 3302302:
        # user이랑 user_set 테이블의 통합
        curs.execute(db_change('select id, pw, acl, date, encode from user'))
        for i in curs.fetchall():
            curs.execute(db_change(
                "insert into user_set (name, id, data) values (?, ?, ?)"
            ), ['pw', i[0], i[1]])
            curs.execute(db_change(
                "insert into user_set (name, id, data) values (?, ?, ?)"
            ), ['acl', i[0], i[2]])
            curs.execute(db_change(
                "insert into user_set (name, id, data) values (?, ?, ?)"
            ), ['date', i[0], i[3]])
            curs.execute(db_change(
                "insert into user_set (name, id, data) values (?, ?, ?)"
            ), ['encode', i[0], i[4]])
            
    if ver_num < 3400101:
        # user_set이랑 user_application 테이블의 통합
        curs.execute(db_change('' + \
            'select id, pw, date, encode, question, answer, ip, ua, email ' + \
            'from user_application' + \
        ''))
        for i in curs.fetchall():
            sql_data = {}
            sql_data['id'] = i[0]
            sql_data['pw'] = i[1]
            sql_data['date'] = i[2]
            sql_data['encode'] = i[3]
            sql_data['question'] = i[4]
            sql_data['answer'] = i[5]
            sql_data['ip'] = i[6]
            sql_data['ua'] = i[7]
            sql_data['email'] = i[8]
            
            curs.execute(db_change(
                "insert into user_set (name, id, data) values (?, ?, ?)"
            ), ['application', i[0], json.dumps(sql_data)])
    
    if ver_num < 3500105:
        curs.execute(db_change(
            'delete from acl where title like "file:%" and data = "admin" and type like "decu%"'
        ))
        
    if ver_num < 3500106:
        curs.execute(db_change("select data from other where name = 'domain'"))
        db_data = curs.fetchall()
        if db_data and db_data[0][0] != '':
            db_data = db_data[0][0]
            db_data = re.match(r'[^/]+\/\/([^/]+)', db_data)
            if db_data:
                db_data = db_data.group(1)
                curs.execute(db_change(
                    "update other set data = ? where name = 'domain'"
                ), [
                    db_data
                ])
            else:
                curs.execute(db_change(
                    "update other set data = '' where name = 'domain'"
                ))

    if ver_num < 3500107:
        db_table_list = get_db_table_list()
        for for_a in db_table_list:
            for for_b in db_table_list[for_a]:
                curs.execute(db_change("update " + for_a + " set " + for_b + " = '' where " + for_b + " is null"))
                
    if ver_num < 3500112:
        # curs.execute(db_change('select id from user_set where name = "email" and data = ?'), [user_email])
        curs.execute(db_change('select id from user_set where name = "email"'))
        for db_data in curs.fetchall():
            if ip_or_user(db_data[0]) == 1:
                curs.execute(db_change(
                    'delete from user_set where id = ? and name = "email"'
                ), [db_data[0]])
                
    if ver_num < 3500113:
        db_table_list = get_db_table_list()
        for for_a in db_table_list:
            for for_b in db_table_list[for_a]:
                curs.execute(db_change("update " + for_a + " set " + for_b + " = '' where " + for_b + " is null"))

    if ver_num < 3500114:
        curs.execute(db_change('delete from alarm'))

    if ver_num < 3500354:
        curs.execute(db_change("select data from other where name = 'robot'"))
        db_data = curs.fetchall()
        if db_data:
            robot_default = '' + \
                'User-agent: *\n' + \
                'Disallow: /\n' + \
                'Allow: /$\n' + \
                'Allow: /image/\n' + \
                'Allow: /views/\n' + \
                'Allow: /w/' + \
            ''
            if db_data[0][0] == robot_default:
                curs.execute(db_change("insert into other (name, data, coverage) values ('robot_default', 'on', '')"))

    if ver_num < 3500355:
        # other coverage 오류 해결
        curs.execute(db_change(
            "update other set coverage = '' where coverage is null"
        ))

    if ver_num < 3500358:
        curs.execute(db_change("drop index history_index"))
        curs.execute(db_change("create index history_index on history (title, ip)"))

    if ver_num < 3500360:
        # 마지막 편집 따로 기록하도록
        # create_data['data_set'] = ['doc_name', 'doc_rev', 'set_name', 'set_data']
        print("Update 3500360...")

        curs.execute(db_change('delete from data_set where set_name = "last_edit"'))

        curs.execute(db_change("select title from data"))
        db_data = curs.fetchall()
        for for_a in db_data:
            curs.execute(db_change("select date from history where title = ? order by date desc limit 1"), [for_a[0]])
            db_data_2 = curs.fetchall()
            if db_data_2:
                curs.execute(db_change("insert into data_set (doc_name, doc_rev, set_name, set_data) values (?, '', 'last_edit', ?)"), [for_a[0], db_data_2[0][0]])

        curs.execute(db_change(
            'delete from acl where title like "file:%" and data = "admin" and type like "decu%"'
        ))

        print("Update 3500360 complete")

    conn.commit()
    
    # 아이피 상태인 이메일 제거 예정

    print('Update completed')

def set_init_always(ver_num):
    global global_wiki_set
    
    curs = conn.cursor()

    curs.execute(db_change('delete from other where name = "ver"'))
    curs.execute(db_change('insert into other (name, data, coverage) values ("ver", ?, "")'), [ver_num])
    
    curs.execute(db_change('delete from alist where name = "owner"'))
    curs.execute(db_change('insert into alist (name, acl) values ("owner", "owner")'))

    if not os.path.exists(load_image_url()):
        os.makedirs(load_image_url())

    curs.execute(db_change('select data from other where name = "key"'))
    if not curs.fetchall():
        curs.execute(db_change('insert into other (name, data, coverage) values ("key", ?, "")'), [load_random_key()])
        
    curs.execute(db_change('select data from other where name = "salt_key"'))
    if not curs.fetchall():
        curs.execute(db_change('insert into other (name, data, coverage) values ("salt_key", ?, "")'), [load_random_key(4)])

    curs.execute(db_change('select data from other where name = "count_all_title"'))
    if not curs.fetchall():
        curs.execute(db_change('insert into other (name, data, coverage) values ("count_all_title", "0", "")'))
        
    curs.execute(db_change('select data from other where name = "wiki_access_password_need"'))
    db_data = curs.fetchall()
    if db_data and db_data[0][0] != '':
        curs.execute(db_change('select data from other where name = "wiki_access_password"'))
        db_data = curs.fetchall()
        if db_data:
            global_wiki_set['wiki_access_password'] = db_data[0][0]
    
    conn.commit()
    
def set_init():
    curs = conn.cursor()

    # 초기값 설정 함수    
    curs.execute(db_change("select html from html_filter where kind = 'email'"))
    if not curs.fetchall():
        for i in ['naver.com', 'gmail.com', 'daum.net', 'kakao.com']:
            curs.execute(db_change(
                "insert into html_filter (html, kind, plus, plus_t) values (?, 'email', '', '')"
            ), [i])

    curs.execute(db_change("select html from html_filter where kind = 'extension'"))
    if not curs.fetchall():
        for i in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
            curs.execute(db_change(
                "insert into html_filter (html, kind, plus, plus_t) values (?, 'extension', '', '')"
            ), [i])

    curs.execute(db_change(
        'select data from other ' + \
        'where name = "smtp_server" or name = "smtp_port" or name = "smtp_security"'
    ))
    if not curs.fetchall():
        for i in [
            ['smtp_server', 'smtp.gmail.com'],
            ['smtp_port', '587'], 
            ['smtp_security', 'starttls']
        ]:
            curs.execute(db_change("insert into other (name, data, coverage) values (?, ?, '')"), [i[0], i[1]])
        
    conn.commit()

# Func-simple
## Func-simple-without_DB
def get_default_admin_group():
    return ['owner', 'user', 'ban']

def get_default_robots_txt():
    data = '' + \
        'User-agent: *\n' + \
        'Disallow: /\n' + \
        'Allow: /$\n' + \
        'Allow: /w/\n' + \
        'Allow: /sitemap.xml$\n' + \
        'Allow: /sitemap_*.xml$' + \
    ''

    if os.path.exists('sitemap.xml'):
        data += '' + \
            '\n' + \
            'Sitemap: ' + load_domain('full') + '/sitemap.xml' + \
        ''

    return data

def get_user_title_list(ip = ''):
    curs = conn.cursor()

    ip = ip_check() if ip == '' else ip

    # default
    user_title = {
        '' : load_lang('default'),
        '🌳' : '🌳 namu',
    }
    
    # admin
    if admin_check('all', None, ip) == 1:
        user_title['✅'] = '✅ admin'

    curs.execute(db_change('select name from user_set where id = ? and name = ?'), [ip, 'get_🥚'])
    if curs.fetchall():
        user_title['🥚'] = '🥚 easter_egg'
    
    return user_title

def load_random_key(long = 128):
    return ''.join(
        random.choice(
            "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        ) for i in range(long)
    )

def http_warning():
    return '''
        <div id="opennamu_http_warning_text"></div>
        <span style="display: none;" id="opennamu_http_warning_text_lang">''' + load_lang('http_warning') + '''</span>
    '''

def get_next_page_bottom(link, num, page, end = 50):
    list_data = ''

    if num == 1:
        if len(page) == end:
            list_data += '' + \
                '<hr class="main_hr">' + \
                '<a href="' + link.format(str(num + 1)) + '">(' + load_lang('next') + ')</a>' + \
            ''
    elif len(page) != end:
        list_data += '' + \
            '<hr class="main_hr">' + \
            '<a href="' + link.format(str(num - 1)) + '">(' + load_lang('previous') + ')</a>' + \
        ''
    else:
        list_data += '' + \
            '<hr class="main_hr">' + \
            '<a href="' + link.format(str(num - 1)) + '">(' + load_lang('previous') + ')</a> ' + \
            '<a href="' + link.format(str(num + 1)) + '">(' + load_lang('next') + ')</a>' + \
        ''

    return list_data

def next_fix(link, num, page, end = 50):
    list_data = ''

    if num == 1:
        if len(page) == end:
            list_data += '' + \
                '<hr class="main_hr">' + \
                '<a href="' + link + str(num + 1) + '">(' + load_lang('next') + ')</a>' + \
            ''
    elif len(page) != end:
        list_data += '' + \
            '<hr class="main_hr">' + \
            '<a href="' + link + str(num - 1) + '">(' + load_lang('previous') + ')</a>' + \
        ''
    else:
        list_data += '' + \
            '<hr class="main_hr">' + \
            '<a href="' + link + str(num - 1) + '">(' + load_lang('previous') + ')</a> <a href="' + link + str(num + 1) + '">(' + load_lang('next') + ')</a>' + \
        ''

    return list_data

def leng_check(A, B):
    # B -> new
    # A -> old
    return '0' if A == B else (('-' + str(A - B)) if A > B else ('+' + str(B - A)))

def number_check(data):
    try:
        int(data)
        return data
    except:
        return '1'
    
def check_int(data):
    try:
        int(data)
        return data
    except:
        return ''
    
def redirect(data = '/'):
    return flask.redirect(load_domain('full') + data)
    
def get_acl_list(type_d = 'normal'):
    if type_d == 'user':
        return ['', 'user', 'all']
    else:
        return ['', 'all', 'user', 'admin', 'owner', '50_edit', 'email', 'ban', 'before', '30_day', 'ban_admin', 'not_all']

## Func-simple-with_DB
def load_image_url():
    curs = conn.cursor()

    curs.execute(db_change('select data from other where name = "image_where"'))
    image_where = curs.fetchall()
    image_where = image_where[0][0] if image_where else os.path.join('data', 'images')
    
    return image_where

def load_domain(data_type = 'normal'):
    curs = conn.cursor()
    
    domain = ''
    
    if data_type == 'full':
        curs.execute(db_change("select data from other where name = 'http_select'"))
        db_data = curs.fetchall()
        domain += db_data[0][0] if db_data and db_data[0][0] != '' else 'http'
        domain += '://'

        curs.execute(db_change("select data from other where name = 'domain'"))
        db_data = curs.fetchall()
        domain += db_data[0][0] if db_data and db_data[0][0] != '' else flask.request.host
    else:
        curs.execute(db_change("select data from other where name = 'domain'"))
        db_data = curs.fetchall()
        domain += db_data[0][0] if db_data and db_data[0][0] != '' else flask.request.host

    return domain

def edit_button(ob_name = 'opennamu_edit_textarea', monaco_ob_name = 'opennamu_monaco_editor'):
    curs = conn.cursor()

    insert_list = []

    curs.execute(db_change("select html, plus from html_filter where kind = 'edit_top'"))
    db_data = curs.fetchall()
    for get_data in db_data:
        insert_list += [[get_data[1], get_data[0]]]

    data = ''
    for insert_data in insert_list:
        data += '<a href="javascript:do_insert_data(\'' + ob_name + '\', \'' + insert_data[0] + '\', \'' + monaco_ob_name + '\');">(' + insert_data[1] + ')</a> '

    data += (' ' if data != '' else '') + '<a href="/edit_top">(' + load_lang('add') + ')</a>'
    data += '<hr class="main_hr">'
    
    return data

def ip_warning():
    curs = conn.cursor()

    if ip_or_user() != 0:
        curs.execute(db_change('select data from other where name = "no_login_warning"'))
        data = curs.fetchall()
        if data and data[0][0] != '':
            text_data = '' + \
                '<span>' + data[0][0] + '</span>' + \
                '<hr class="main_hr">' + \
            ''
        else:
            text_data = '' + \
                '<span>' + load_lang('no_login_warning') + '</span>' + \
                '<hr class="main_hr">' + \
            ''
    else:
        text_data = ''

    return text_data
    
# Func-login    
def pw_encode(data, db_data_encode = ''):
    curs = conn.cursor()

    if db_data_encode == '':
        curs.execute(db_change('select data from other where name = "encode"'))
        db_data = curs.fetchall()
        db_data_encode = db_data[0][0] if db_data else 'sha3'

    if db_data_encode == 'sha256':
        return hashlib.sha256(bytes(data, 'utf-8')).hexdigest()
    elif db_data_encode == 'sha3':
        return hashlib.sha3_256(bytes(data, 'utf-8')).hexdigest()
    elif db_data_encode == 'sha3-512':
        return hashlib.sha3_512(bytes(data, 'utf-8')).hexdigest()
    else:
        curs.execute(db_change('select data from other where name = "salt_key"'))
        db_data = curs.fetchall()
        db_data_salt = db_data[0][0] if db_data else ''
        
        if db_data_encode == 'sha3-salt':
            return hashlib.sha3_256(bytes(data + db_data_salt, 'utf-8')).hexdigest()
        else:
            return hashlib.sha3_512(bytes(data + db_data_salt, 'utf-8')).hexdigest()

def pw_check(data, data2, type_d = 'no', id_d = ''):
    curs = conn.cursor()

    curs.execute(db_change('select data from other where name = "encode"'))
    db_data = curs.fetchall()

    if type_d != 'no':
        if type_d == '':
            set_data = 'sha3'
        else:
            set_data = type_d
    else:
        set_data = db_data[0][0]

    re_data = 1 if pw_encode(data, set_data) == data2 else 0
    if db_data[0][0] != set_data and re_data == 1 and id_d != '':
        curs.execute(db_change("update user_set set data = ? where id = ? and name = 'pw'"), [
            pw_encode(data), 
            id_d
        ])
        curs.execute(db_change("update user_set set data = ? where id = ? and name = 'encode'"), [
            db_data[0][0], 
            id_d
        ])

    return re_data
        
# Func-skin
def easy_minify(data, tool = None):
    # without_DB
    if 'wiki_access_password' in global_wiki_set:
        access_password = global_wiki_set['wiki_access_password']
        input_password = flask.request.cookies.get('opennamu_wiki_access', ' ')
        if url_pas(access_password) == input_password:
            return data
            
        return '''
            <script src="/views/main_css/js/route/wiki_access_password.js"></script>
            <h2>''' + load_lang('error_password_require_for_wiki_access') + '''</h2>
            <input type="password" id="wiki_access">
            <input type="submit" onclick="opennamu_do_wiki_access();">
        '''
    else:
        return data

def load_lang(data, safe = 0):
    curs = conn.cursor()

    global global_lang

    ip = ip_check()
    if ip_or_user(ip) == 0:
        curs.execute(db_change('select data from user_set where name = "lang" and id = ?'), [ip])
        rep_data = curs.fetchall()                    
    elif 'lang' in flask.session:
        rep_data = [[flask.session['lang']]]
    else:
        curs.execute(db_change("select data from other where name = 'language'"))
        rep_data = curs.fetchall()

    if not rep_data or rep_data[0][0] in ('', 'default'):
        curs.execute(db_change("select data from other where name = 'language'"))
        rep_data = curs.fetchall()

    if rep_data:
        lang_name = rep_data[0][0]
    else:
        lang_name = 'en-US'
        
    if lang_name in global_lang:
        lang = global_lang[lang_name]
    else:
        lang_list = os.listdir('lang')
        if (lang_name + '.json') in lang_list:
            lang = json.loads(open(
                os.path.join('lang', lang_name + '.json'), 
                encoding = 'utf8'
            ).read())
            global_lang[lang_name] = lang
        else:
            lang = {}

    if data in lang:
        if safe == 1:
            return lang[data] 
        else:
            return html.escape(lang[data])

    return html.escape(data + ' (' + lang_name + ')')

def skin_check(set_n = 0):
    curs = conn.cursor()

    # 개편 필요?
    skin_list = load_skin('ringo', 1)
    skin = skin_list[0]
    ip = ip_check()
    
    user_need_skin = ''
    if ip_or_user(ip) == 0:
        curs.execute(db_change('select data from user_set where name = "skin" and id = ?'), [ip])
        skin_exist = curs.fetchall()
        if skin_exist:
            user_need_skin = skin_exist[0][0]            
    else:
        if 'skin' in flask.session:
            user_need_skin = flask.session['skin']

    user_need_skin = '' if user_need_skin == 'default' else user_need_skin

    if user_need_skin == '':
        curs.execute(db_change('select data from other where name = "skin"'))
        skin_exist = curs.fetchall()
        if skin_exist:
            user_need_skin = skin_exist[0][0]
    
    if user_need_skin != '' and user_need_skin in skin_list:
        skin = user_need_skin

    if set_n == 0:
        return './views/' + skin + '/index.html'
    else:
        return skin
    
def wiki_css(data):
    # without_DB
    data += ['' for _ in range(0, 3 - len(data))]
    
    data_css = ''
    data_css_ver = '172'
    
    # Func JS + Defer
    data_css += '<script src="/views/main_css/js/func/func.js?ver=' + data_css_ver + '"></script>'
    
    data_css += '<script defer src="/views/main_css/js/func/insert_version.js?ver=' + data_css_ver + '"></script>'
    data_css += '<script defer src="/views/main_css/js/func/insert_user_info.js?ver=' + data_css_ver + '"></script>'
    data_css += '<script defer src="/views/main_css/js/func/insert_version_skin.js?ver=' + data_css_ver + '"></script>'
    data_css += '<script defer src="/views/main_css/js/func/insert_http_warning_text.js?ver=' + data_css_ver + '"></script>'
    
    data_css += '<script defer src="/views/main_css/js/func/ie_end_of_life.js?ver=' + data_css_ver + '"></script>'
    data_css += '<script defer src="/views/main_css/js/func/shortcut.js?ver=' + data_css_ver + '"></script>'
    
    # Route JS + Defer
    data_css += '<script defer src="/views/main_css/js/route/thread.js?ver=' + data_css_ver + '"></script>'
    
    # 레거시 일반 JS
    data_css += '<script src="/views/main_css/js/load_editor.js?ver=' + data_css_ver + '"></script>'
    
    # Main CSS
    data_css += '<link rel="stylesheet" href="/views/main_css/css/main.css?ver=' + data_css_ver + '">'

    # External
    data_css += '<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.5.0/build/styles/default.min.css">'
    data_css += '<script src="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.5.0/build/highlight.min.js"></script>'
    
    data_css += '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.15.3/dist/katex.min.css" integrity="sha384-KiWOvVjnN8qwAZbuQyWDIbfCLFhLXNETzBQjA/92pIowpC0d2O3nppDGQVgwd2nB" crossorigin="anonymous">'
    data_css += '<script src="https://cdn.jsdelivr.net/npm/katex@0.15.3/dist/katex.min.js" integrity="sha384-0fdwu/T/EQMsQlrHCCHoH10pkPLlKA1jL5dFyUOvB3lfeT2540/2g6YgSi2BL14p" crossorigin="anonymous"></script>'

    data = data[0:2] + ['', data_css] + data[2:]

    return data

def cut_100(data):
    # without_DB
    data = re.sub(r'.*<div class="opennamu_render_complete">', '', data, 1)

    data = data.replace('<br>', ' ')
    data = data.replace('\r', '') 
    data = data.replace('\n', ' ')
    data = re.sub(r'<[^<>]+>', ' ', data)
    data = data.replace('\n', ' ')
    data = re.sub(r' {2,}', ' ', data)
    data = re.sub(r'(^ +| +$)', '', data)

    data_len = len(data)
    if data_len > 100:
        return data[0:100]
    else:
        return data[0:data_len]

def wiki_set(num = 1):
    curs = conn.cursor()

    ip = ip_check()
    skin_name = skin_check(1)
    data_list = []

    curs.execute(db_change('select data from other where name = ?'), ['name'])
    db_data = curs.fetchall()
    data_list += [db_data[0][0]] if db_data and db_data[0][0] != '' else ['Wiki']

    curs.execute(db_change('select data from other where name = "license"'))
    db_data = curs.fetchall()
    data_list += [db_data[0][0]] if db_data and db_data[0][0] != '' else ['ARR']

    data_list += ['', '']

    curs.execute(db_change('select data from other where name = "logo" and coverage = ?'), [skin_name])
    db_data = curs.fetchall()
    if db_data and db_data[0][0] != '':
        data_list += [db_data[0][0]]
    else:
        curs.execute(db_change('select data from other where name = "logo" and coverage = ""'))
        db_data = curs.fetchall()
        data_list += [db_data[0][0]] if db_data and db_data[0][0] != '' else [data_list[0]]

    head_data = ''

    curs.execute(db_change("select data from other where name = 'head' and coverage = ''"))
    db_data = curs.fetchall()
    head_data += db_data[0][0] if db_data and db_data[0][0] != '' else ''

    curs.execute(db_change("select data from other where name = 'head' and coverage = ?"), [skin_name])
    db_data = curs.fetchall()
    head_data += db_data[0][0] if db_data and db_data[0][0] != '' else ''

    data_list += [head_data]

    curs.execute(db_change("select data from other where name = 'top_menu'"))
    db_data = curs.fetchall()
    db_data = db_data[0][0] if db_data else ''
    db_data = db_data.replace('\r', '')
    
    curs.execute(db_change("select data from user_set where name = '' and id = ?"), [ip])
    db_data_2 = curs.fetchall()
    db_data_2 = db_data_2[0][0] if db_data_2 else ''
    db_data += db_data_2.replace('\r', '')
    if db_data != '':
        db_data = db_data.split('\n')
    
        if len(db_data) % 2 != 0:
            db_data += ['']

        db_data = [[db_data[for_a], db_data[for_a + 1]] for for_a in range(0, len(db_data), 2)]

    data_list += [db_data]

    return data_list

def wiki_custom():
    curs = conn.cursor()

    ip = ip_check()
    skin_name = '_' + skin_check(1)

    if ip_or_user(ip) == 0:
        user_icon = 1
        user_name = ip

        if 'head' in flask.session:
            user_head = flask.session['head']
        else:
            curs.execute(db_change("select data from user_set where id = ? and name = 'custom_css'"), [ip])
            db_data = curs.fetchall()
            user_head = db_data[0][0] if db_data else ''

            flask.session['head'] = db_data[0][0] if db_data else ''

        if 'head' + skin_name in flask.session:
            user_head += flask.session['head' + skin_name]
        else:
            curs.execute(db_change("select data from user_set where id = ? and name = ?"), [ip, 'custom_css' + skin_name])
            db_data = curs.fetchall()
            user_head += db_data[0][0] if db_data else ''

            flask.session['head' + skin_name] = db_data[0][0] if db_data else ''
        
        curs.execute(db_change('select data from user_set where name = "email" and id = ?'), [ip])
        email = curs.fetchall()
        email = email[0][0] if email else ''

        if admin_check('all') == 1:
            user_admin = '1'
            user_acl_list = []

            curs.execute(db_change("select data from user_set where id = ? and name = 'acl'"), [ip])
            curs.execute(db_change('select acl from alist where name = ?'), [curs.fetchall()[0][0]])
            user_acl = curs.fetchall()
            for i in user_acl:
                user_acl_list += [i[0]]

            user_acl_list = user_acl_list if user_acl != [] else '0'
        else:
            user_admin = '0'
            user_acl_list = '0'

        curs.execute(db_change("select count(*) from alarm where name = ?"), [ip])
        count = curs.fetchall()
        user_notice = str(count[0][0]) if count else '0'
    else:
        user_icon = 0
        user_name = load_lang('user')
        email = ''
        user_admin = '0'
        user_acl_list = '0'
        user_notice = '0'
        user_head = flask.session['head'] if 'head' in flask.session else ''
        user_head += flask.session['head' + skin_name] if 'head' + skin_name in flask.session else ''

    curs.execute(db_change("select title from rd where title = ? and stop = ''"), ['user:' + ip])
    user_topic = '1' if curs.fetchall() else '0'
    
    split_path = flask.request.path.split('/')
    if len(split_path) > 1:
        split_path = split_path[1]
    else:
        split_path = 0

    return [
        '',
        '',
        user_icon,
        user_head,
        email,
        user_name,
        user_admin,
        str(ban_check()),
        user_notice,
        user_acl_list,
        ip,
        user_topic,
        split_path
    ]

def load_skin(data = '', set_n = 0, default = 0):
    # without_DB

    # data -> 가장 앞에 있을 스킨 이름
    # set_n == 0 -> 스트링으로 반환
    # set_n == 1 -> 리스트로 반환
    # default == 0 -> 디폴트 미포함
    # default == 1 -> 디폴트 포함

    if set_n == 0:
        skin_return_data = ''
    else:
        skin_return_data = []

    skin_list_get = os.listdir('views')
    if default == 1:
        skin_list_get = ['default'] + skin_list_get

    for skin_data in skin_list_get:
        if skin_data != 'default':
            see_data = skin_data
        else:
            see_data = load_lang('default')

        if skin_data != 'main_css':
            if set_n == 0:
                if skin_data == data:
                    skin_return_data = '' + \
                        '<option value="' + skin_data + '">' + \
                            see_data + \
                        '</option>' + \
                    '' + skin_return_data
                else:
                    skin_return_data += '' + \
                        '<option value="' + skin_data + '">' + \
                            see_data + \
                        '</option>' + \
                    ''
            else:
                if skin_data == data:
                    skin_return_data = [skin_data] + skin_return_data
                else:
                    skin_return_data += [skin_data]                    

    return skin_return_data

# Func-markup
def render_set(doc_name = '', doc_data = '', data_type = 'view', data_in = '', doc_acl = ''):
    curs = conn.cursor()

    # data_type in ['view', 'raw', 'api_view', 'backlink']
    doc_acl = acl_check(doc_name, 'render') if doc_acl == '' else doc_acl
    doc_data = 0 if doc_data == None else doc_data
        
    if doc_acl == 1:
        return 'HTTP Request 401.3'
    else:
        if data_type == 'raw':
            return doc_data
        
        if doc_data != 0:
            render_lang_data = {
                'toc' : load_lang('toc'),
                'category' : load_lang('category')
            }

            get_class_render = class_do_render(conn, render_lang_data).do_render(doc_name, doc_data, data_type, data_in)

            if data_type == 'backlink':
                return ''

            if 'include' in get_class_render[2]:
                for_a = 0
                while len(get_class_render[2]['include']) > for_a:
                    include_data = get_class_render[2]['include'][for_a]
                    if acl_check(include_data[1], 'render') == 0:
                        include_regex = re.compile('<div id="' + include_data[0] + '"><\/div>')
                        
                        include_data_render = class_do_render(conn, render_lang_data).do_render(include_data[1], include_data[2], data_type, include_data[0] + data_in)
                        if len(include_data) > 3:
                            include_data_render[0] = '<div id="' + include_data[0] + '" ' + include_data[3] + '>' + include_data_render[0] + '</div>'
                        else:
                            include_data_render[0] = '<div id="' + include_data[0] + '">' + include_data_render[0] + '</div>'

                        get_class_render[0] = re.sub(include_regex, include_data_render[0], get_class_render[0])
                        get_class_render[1] += include_data_render[1]
                        get_class_render[2]['include'] += include_data_render[2]['include']

                    for_a += 1

            get_class_render[0] = '<div class="opennamu_render_complete">' + get_class_render[0] + '</div>'

            curs.execute(db_change("select data from other where name = 'namumark_compatible'"))
            db_data = curs.fetchall()
            if db_data and db_data[0][0] != '':
                get_class_render[0] += '''
                    <style>
                        .opennamu_render_complete {
                            font-size: 14.4px !important;
                        }

                        .opennamu_render_complete td {
                            padding: 5px 10px !important;
                        }

                        .opennamu_render_complete summary {
                            list-style: none !important;
                            font-weight: bold;
                        }
                    </style>
                '''

            if data_type == 'api_view':
                return [
                    get_class_render[0], 
                    get_class_render[1]
                ]
            else:
                return get_class_render[0] + '<script>' + get_class_render[1] + '</script>'
        else:
            return 'HTTP Request 404'
            
def render_simple_set(data):
    toc_data = ''
    toc_regex = r'<h([1-6])>([^<>]+)<\/h[1-6]>'
    toc_search_data = re.findall(toc_regex,  data)
    heading_stack = [0, 0, 0, 0, 0, 0]

    if toc_search_data:
        toc_data += '''
            <div class="opennamu_TOC" id="toc">
                <span class="opennamu_TOC_title">''' + load_lang('toc') + '''</span>
                <br>
        '''
    
    for toc_search_in in toc_search_data:
        heading_level = int(toc_search_in[0])
        heading_level_str = str(heading_level)

        heading_stack[heading_level - 1] += 1
        for for_a in range(heading_level, 6):
            heading_stack[for_a] = 0
        
        heading_stack_str = ''.join([str(for_a) + '.' if for_a != 0 else '' for for_a in heading_stack])
        heading_stack_str = re.sub(r'\.$', '', heading_stack_str)
    
        toc_data += '''
            <br>
            <span class="opennamu_TOC_list">
                ''' + ('<span style="margin-left: 10px;"></span>' * (heading_stack_str.count('.'))) + '''
                <a href="#s-''' + heading_stack_str + '''">''' + heading_stack_str + '''.</a>
                ''' + toc_search_in[1] + '''
            </span>
        '''
        
        data = re.sub(toc_regex, '<h' + toc_search_in[0] + ' id="s-' + heading_stack_str + '"><a href="#toc">' + heading_stack_str + '.</a> ' + toc_search_in[1] + '</h' + toc_search_in[0] + '>', data, 1)
        
    if toc_data != '':
        toc_data += '</div>'
        
    footnote_data = ''
    footnote_regex = r'<sup>((?:(?!<sup>|<\/sup>).)+)<\/sup>'
    footnote_search_data = re.findall(footnote_regex, data)
    footnote_count = 1
    if footnote_search_data:
        footnote_data += '<div class="opennamu_footnote">'
    
    for footnote_search in footnote_search_data:
        footnote_count_str = str(footnote_count)
        
        if footnote_count != 1:
            footnote_data += '<br>'
    
        footnote_data += '<a id="fn-' + footnote_count_str + '" href="#rfn-' + footnote_count_str + '">(' + footnote_count_str + ')</a> ' + footnote_search
        data = re.sub(footnote_regex, '<sup id="rfn-' + footnote_count_str + '"><a href="#fn-' + footnote_count_str + '">(' + footnote_count_str + ')</a></sup>', data, 1)
        
        footnote_count += 1
        
    if footnote_data != '':
        footnote_data += '</div>'
        
    data = toc_data + data + footnote_data

    return data

# Func-request
def send_email(who, title, data):
    curs = conn.cursor()

    try:
        curs.execute(db_change('' + \
            'select name, data from other ' + \
            'where name = "smtp_email" or name = "smtp_pass" or name = "smtp_server" or name = "smtp_port" or name = "smtp_security"' + \
        ''))
        rep_data = curs.fetchall()

        smtp_email = ''
        smtp_pass = ''
        smtp_server = ''
        smtp_security = ''
        smtp_port = ''
        smtp = ''

        for i in rep_data:
            if i[0] == 'smtp_email':
                smtp_email = i[1]
            elif i[0] == 'smtp_pass':
                smtp_pass = i[1]
            elif i[0] == 'smtp_server':
                smtp_server = i[1]
            elif i[0] == 'smtp_security':
                smtp_security = i[1]
            elif i[0] == 'smtp_port':
                smtp_port = i[1]
        
        smtp_port = int(smtp_port)
        if smtp_security == 'plain':
            smtp = smtplib.SMTP(smtp_server, smtp_port)
        elif smtp_security == 'starttls':
            smtp = smtplib.SMTP(smtp_server, smtp_port)
            smtp.starttls()
        else:
            # if smtp_security == 'tls':
            smtp = smtplib.SMTP_SSL(smtp_server, smtp_port)
        
        smtp.login(smtp_email, smtp_pass)

        domain = load_domain()
        wiki_name = wiki_set()[0]
        
        msg = email.mime.text.MIMEText(data)
        msg['Subject'] = title
        msg['From'] = 'openNAMU <noreply@' + domain + '>'
        msg['To'] = who
        
        smtp.sendmail('openNAMU@' + domain, who, msg.as_string())
        smtp.quit()

        return 1
    except Exception as e:
        print('----')
        print('Error : email send error')
        print(e)

        return 0

def captcha_get():
    curs = conn.cursor()

    data = ''
    
    if ip_or_user() != 0:
        curs.execute(db_change('select data from other where name = "recaptcha"'))
        recaptcha = curs.fetchall()
        
        curs.execute(db_change('select data from other where name = "sec_re"'))
        sec_re = curs.fetchall()
        
        curs.execute(db_change('select data from other where name = "recaptcha_ver"'))
        rec_ver = curs.fetchall()
        if recaptcha and recaptcha[0][0] != '' and sec_re and sec_re[0][0] != '':
            if not rec_ver or rec_ver[0][0] == '':
                data += '' + \
                    '<script src="https://www.google.com/recaptcha/api.js" async defer></script>' + \
                    '<div class="g-recaptcha" data-sitekey="' + recaptcha[0][0] + '"></div>' + \
                    '<hr class="main_hr">' + \
                ''
            elif rec_ver[0][0] == 'v3':
                data += '' + \
                    '<script src="https://www.google.com/recaptcha/api.js?render=' + recaptcha[0][0] + '"></script>' + \
                    '<input type="hidden" id="g-recaptcha" name="g-recaptcha">' + \
                    '<script type="text/javascript">' + \
                        'grecaptcha.ready(function() {' + \
                            'grecaptcha.execute(\'' + recaptcha[0][0] + '\', {action: \'homepage\'}).then(function(token) {' + \
                                'document.getElementById(\'g-recaptcha\').value = token;' + \
                            '});' + \
                        '});' + \
                    '</script>' + \
                ''
            else:
                data += '''
                    <script src="https://js.hcaptcha.com/1/api.js" async defer></script>
                    <div class="h-captcha" data-sitekey="''' + recaptcha[0][0] + '''"></div>
                    <hr class="main_hr">
                '''

    return data

def captcha_post(re_data, num = 1):
    curs = conn.cursor()

    if num == 1 and ip_or_user() != 0:
        curs.execute(db_change('select data from other where name = "sec_re"'))
        sec_re = curs.fetchall()
        
        curs.execute(db_change('select data from other where name = "recaptcha_ver"'))
        rec_ver = curs.fetchall()
        if captcha_get() != '':
            if not rec_ver or rec_ver[0][0] in ('', 'v3'):
                data = requests.get(
                    'https://www.google.com/recaptcha/api/siteverify' + \
                    '?secret=' + sec_re[0][0] + '&response=' + re_data
                )
                if data.status_code == 200:
                    json_data = json.loads(data.text)
                    if json_data['success'] != True:
                        return 1
            else:
                data = requests.get(
                    'https://hcaptcha.com/siteverify' + \
                    '?secret=' + sec_re[0][0] + '&response=' + re_data
                )
                if data.status_code == 200:
                    json_data = json.loads(data.text)
                    if json_data['success'] != True:
                        return 1

        return 0

# Func-user
def get_admin_auth_list(num = None):
    check = {
        0 : 'owner',
        1 : 'ban',
        2 : 'nothing',
        3 : 'toron',
        4 : 'check',
        5 : 'acl',
        6 : 'hidel',
        7 : 'give'
    }
    if not num:
        check = check[0]
    elif num == 'all':
        check = [check[i] for i in check]
    else:
        check = check[num]
        
    return check

def get_admin_list(num = None):
    curs = conn.cursor()
    
    if num == 'all':
        curs.execute(db_change(
            "select data from user_set where data != 'user' and name = 'acl'"
        ))
        db_data = curs.fetchall()
        db_data = [db_data_in[0] for db_data_in in db_data] if db_data else []
        
        return db_data
    else:
        check = get_admin_auth_list(num)
        admin_list = []
        
        curs.execute(db_change(
            'select name from alist where acl = ?'
        ), [check])
        db_data = curs.fetchall()
        for db_data_in in db_data:
            curs.execute(db_change(
                "select id from user_set where data = ? and name = 'acl'"
            ), [db_data_in[0]])
            db_data_2 = curs.fetchall()
            admin_list += [db_data_2_in[0] for db_data_2_in in db_data_2] if db_data_2 else []
            
        return admin_list

def admin_check(num = None, what = None, name = ''):
    curs = conn.cursor()

    ip = ip_check() if name == '' else name
    time_data = get_time()
    pass_ok = 0

    if ip_or_user(ip) == 0:
        curs.execute(db_change(
            "select data from user_set where id = ? and name = 'acl'"
        ), [ip])
        user_auth = curs.fetchall()
        if user_auth:
            user_auth = user_auth[0][0]
            check = get_admin_auth_list(num)
            
            curs.execute(db_change(
                'select name from alist where name = ? and acl = "owner"'
            ), [user_auth])
            if curs.fetchall():
                pass_ok = 1
            else:
                if num == 'all':                    
                    curs.execute(db_change(
                        'select name from alist where name = ?'
                    ), [user_auth])
                else:
                    curs.execute(db_change(
                        'select name from alist where name = ? and acl = ?'
                    ), [user_auth, check])
                    
                if curs.fetchall():
                    pass_ok = 1

                
            if pass_ok == 1:
                if what:
                    curs.execute(db_change(
                        "insert into re_admin (who, what, time) values (?, ?, ?)"
                    ), [ip, what, time_data])
                    conn.commit()

                return 1

    return 0

def acl_check(name = 'test', tool = '', topic_num = '1'):
    curs = conn.cursor()

    ip = ip_check()
    get_ban = ban_check()
    
    if tool == '' and name:
        if acl_check(name, 'render') == 1:
            return 1
        
        user_page = re.search(r"^user:((?:(?!\/).)*)", name)
        if user_page:
            user_page = user_page.group(1)
            if admin_check(5) == 1:
                return 0
                
            if get_ban == 1:
                return 1
                
            curs.execute(db_change(
                "select data from acl where title = ? and type = 'decu'"
            ), [name])
            acl_data = curs.fetchall()
            if acl_data:
                if acl_data[0][0] == 'all':
                    return 0
                elif acl_data[0][0] == 'user' and not ip_or_user(ip) == 1:
                    return 0
            
            if ip == user_page and not ip_or_user(ip) == 1:
                return 0
    
            return 1
    elif tool in ['document_edit', 'document_move', 'document_delete']:
        if acl_check(name, '') == 1:
            return 1
    elif tool == 'topic':
        curs.execute(db_change("select title from rd where code = ?"), [topic_num])
        name = curs.fetchall()
        name = name[0][0] if name else 'test'

    if tool in ['topic']:
        end = 3
    elif tool in ['render', 'vote', '', 'document_edit', 'document_move', 'document_delete']:
        end = 2
    else:
        end = 1

    for i in range(0, end):
        if tool == '':
            if i == 0:
                curs.execute(db_change(
                    "select data from acl where title = ? and type = 'decu'"
                ), [name])
                '''
            elif i == 1:
                curs.execute(db_change(
                    "select plus from html_filter where kind = 'document'"
                ))
                '''
            else:
                curs.execute(db_change(
                    'select data from other where name = "edit"'
                ))

            num = 5
        elif tool == 'document_move':
            if i == 0:
                curs.execute(db_change(
                    "select data from acl where title = ? and type = 'document_move_acl'"
                ), [name])
            else:
                curs.execute(db_change(
                    'select data from other where name = "document_move_acl"'
                ))

            num = 5
        elif tool == 'document_edit':
            if i == 0:
                curs.execute(db_change(
                    "select data from acl where title = ? and type = 'document_edit_acl'"
                ), [name])
            else:
                curs.execute(db_change(
                    'select data from other where name = "document_edit_acl"'
                ))

            num = 5
        elif tool == 'document_delete':
            if i == 0:
                curs.execute(db_change(
                    "select data from acl where title = ? and type = 'document_delete_acl'"
                ), [name])
            else:
                curs.execute(db_change(
                    'select data from other where name = "document_delete_acl"'
                ))

            num = 5
        elif tool == 'topic':
            if i == 0:
                curs.execute(db_change(
                    "select acl from rd where code = ?"
                ), [topic_num])
            elif i == 1:
                curs.execute(db_change(
                    "select data from acl where title = ? and type = 'dis'"
                ), [name])
            else:
                curs.execute(db_change(
                    'select data from other where name = "discussion"'
                ))

            num = 3
        elif tool == 'topic_view':
            curs.execute(db_change("select set_data from topic_set where thread_code = ? and set_name = 'thread_view_acl'"), [
                topic_num
            ])
            
            num = 3
        elif tool == 'upload':
            curs.execute(db_change(
                "select data from other where name = 'upload_acl'"
            ))

            num = 5
        elif tool == 'many_upload':
            curs.execute(db_change(
                "select data from other where name = 'many_upload_acl'"
            ))

            num = 5
        elif tool == 'vote':
            if i == 0:
                curs.execute(db_change(
                    'select acl from vote where id = ? and user = ""'
                ), [topic_num])
            else:
                curs.execute(db_change(
                    'select data from other where name = "vote_acl"'
                ))

            num = None
        elif tool == 'slow_edit':
            curs.execute(db_change(
                'select data from other where name = "slow_edit_acl"'
            ))

            num = 'all'
        elif tool == 'edit_bottom_compulsion':
            curs.execute(db_change(
                'select data from other where name = "edit_bottom_compulsion_acl"'
            ))

            num = 'all'
        else:
            # tool == 'render'
            if i == 0:
                curs.execute(db_change(
                    "select data from acl where title = ? and type = 'view'"
                ), [name])
            else:
                curs.execute(db_change("select data from other where name = 'all_view_acl'"))

            num = 5

        acl_data = curs.fetchall()
        if not acl_data or acl_data[0][0] == '':
            if tool == 'slow_edit' or tool == 'edit_bottom_compulsion':
                acl_data = [['not_all']]
            else:
                acl_data = [['normal']]

        except_ban_tool_list = ['render', 'topic_view']
        if acl_data[0][0] != 'normal':
            if not acl_data[0][0] in ['ban', 'ban_admin'] and not tool in except_ban_tool_list:
                if get_ban == 1:
                    return 1
            
            if acl_data[0][0] in ['all', 'ban']:
                return 0
            elif acl_data[0][0] == 'user':
                if ip_or_user(ip) != 1:
                    return 0
            elif acl_data[0][0] == 'admin':
                if ip_or_user(ip) != 1:
                    if admin_check(num) == 1:
                        return 0
            elif acl_data[0][0] == '50_edit':
                if ip_or_user(ip) != 1:
                    if admin_check(num) == 1:
                        return 0
                    else:
                        curs.execute(db_change(
                            "select count(*) from history where ip = ?"
                        ), [ip])
                        count = curs.fetchall()
                        count = count[0][0] if count else 0
                        if count >= 50:
                            return 0
            elif acl_data[0][0] == 'before':
                if ip_or_user(ip) != 1:
                    if admin_check(num) == 1:
                        return 0
                
                curs.execute(db_change(
                    "select ip from history where title = ? and ip = ?"
                ), [name, ip])
                if curs.fetchall():
                    return 0
            elif acl_data[0][0] == '30_day' or acl_data[0][0] == '90_day':
                if ip_or_user(ip) != 1:
                    if admin_check(num) == 1:
                        return 0
                    else:
                        curs.execute(db_change(
                            "select data from user_set where id = ? and name = 'date'"
                        ), [ip])
                        user_date = curs.fetchall()[0][0]
                        
                        if acl_data[0][0] == '30_day':
                            time_1 = datetime.datetime.strptime(
                                user_date, 
                                '%Y-%m-%d %H:%M:%S'
                            ) + datetime.timedelta(days = 30)
                        else:
                            time_1 = datetime.datetime.strptime(
                                user_date, 
                                '%Y-%m-%d %H:%M:%S'
                            ) + datetime.timedelta(days = 90)

                        time_2 = datetime.datetime.strptime(
                            get_time(), 
                            '%Y-%m-%d %H:%M:%S'
                        )
                        
                        if time_2 > time_1:
                            return 0
            elif acl_data[0][0] == 'email':
                if ip_or_user(ip) != 1:
                    if admin_check(num) == 1:
                        return 0
                    else:
                        curs.execute(db_change(
                            "select data from user_set where id = ? and name = 'email'"
                        ), [ip])
                        if curs.fetchall():
                            return 0
            elif acl_data[0][0] == 'owner':
                if admin_check() == 1:
                    return 0
            elif acl_data[0][0] == 'ban_admin':
                if admin_check(1) == 1 or get_ban == 1:
                    return 0
            elif acl_data[0][0] == 'not_all':
                return 1

            return 1
        elif i == (end - 1):
            if not tool in except_ban_tool_list:
                if get_ban == 1:
                    return 1
            
            if tool == 'topic':
                curs.execute(db_change(
                    "select title from rd where code = ? and stop != ''"
                ), [topic_num])
                if curs.fetchall():
                    if admin_check(3, 'topic (code ' + topic_num + ')') == 1:
                        return 0
                    else:
                        return 1
                else:
                    return 0
            else:
                return 0

    return 1

def ban_check(ip = None, tool = ''):
    curs = conn.cursor()

    ip = ip_check() if not ip else ip
    tool = '' if not tool else tool

    if admin_check(None, None, ip) == 1:
        return 0

    curs.execute(db_change(
        "update rb set ongoing = '' " + \
        "where end < ? and end != '' and ongoing = '1'"
    ), [get_time()])
    conn.commit()

    curs.execute(db_change("" + \
        "select login, block from rb " + \
        "where band = 'regex' and ongoing = '1'" + \
    ""))
    regex_d = curs.fetchall()
    for test_r in regex_d:
        g_regex = re.compile(test_r[1])
        if g_regex.search(ip):
            if tool == 'login':
                if test_r[0] != 'O':
                    return 1
            else:
                return 1

    curs.execute(db_change("" + \
        "select login from rb " + \
        "where block = ? and band = '' and ongoing = '1'" + \
        "" + \
    ""), [ip])
    ban_d = curs.fetchall()
    if ban_d:
        if tool == 'login':
            if ban_d[0][0] != 'O':
                return 1
        else:
            return 1

    return 0

def ip_pas(raw_ip, type_data = 0):
    curs = conn.cursor()

    end_ip = {}

    return_data = 0
    if type(raw_ip) != type([]):
        get_ip = [raw_ip]
        
        return_data = 1
    else:
        get_ip = raw_ip

    curs.execute(db_change("select data from other where name = 'ip_view'"))
    ip_view = curs.fetchall()
    ip_view = ip_view[0][0] if ip_view else ''
    ip_view = '' if admin_check(1) == 1 else ip_view
    
    get_ip = list(set(get_ip))
    
    for raw_ip in get_ip:
        change_ip = 0
        is_this_ip = ip_or_user(raw_ip)
        if is_this_ip != 0 and ip_view != '':
            try:
                ip = ipaddress.ip_address(raw_ip)
                if type(ip) == ipaddress.IPv6Address:
                    ip = ip.exploded
                    ip = re.sub(r':([^:]*):([^:]*)$', ':*:*', ip)
                else:
                    ip = ip.exploded
                    ip = re.sub(r'\.([^.]*)\.([^.]*)$', '.*.*', ip)
                
                # ip = hashlib.sha3_224(bytes(raw_ip, 'utf-8')).hexdigest()
                # ip = ip[0:4] + '-' + ip[4:8] + '-' + ip[8:12] + '-' + ip[12:16]

                change_ip = 1
            except:
                ip = raw_ip
        else:     
            ip = raw_ip
            
        if type_data == 0 and change_ip == 0:
            if is_this_ip == 0:
                ip = '<a href="/w/' + url_pas('user:' + raw_ip) + '">' + raw_ip + '</a>'
                
                if admin_check('all', None, raw_ip) == 1:
                    ip = '<b>' + ip + '</b>'

                curs.execute(db_change('select data from user_set where name = "user_title" and id = ?'), [raw_ip])
                db_data = curs.fetchall()
                if db_data:
                    ip = db_data[0][0] + ip

            if ban_check(raw_ip) == 1:
                ip = '<s>' + ip + '</s>'

                if ban_check(raw_ip, 'login') == 1:
                    ip = '<i>' + ip + '</i>'

            ip = ip + ' <a href="/user/' + url_pas(raw_ip) + '">(' + load_lang('tool') + ')</a>'

        end_ip[raw_ip] = ip
    
    if return_data == 1:
        return end_ip[raw_ip]
    else:
        return end_ip
        
# Func-edit
def get_edit_text_bottom():
    curs = conn.cursor()
    
    b_text = ''
    
    curs.execute(db_change('select data from other where name = "edit_bottom_text"'))
    db_data= curs.fetchall()
    if db_data and db_data[0][0] != '':
        b_text = '' + \
            db_data[0][0] + \
            '<hr class="main_hr">' + \
        ''

    return b_text

def get_edit_text_bottom_check_box():
    curs = conn.cursor()
    
    cccb_text = ''

    curs.execute(db_change('select data from other where name = "copyright_checkbox_text"'))
    sql_d = curs.fetchall()
    if sql_d and sql_d[0][0] != '':
        cccb_text = '' + \
            '<input type="checkbox" name="copyright_agreement" value="yes"> ' + sql_d[0][0] + \
            '<hr class="main_hr">' + \
        ''
        
    return cccb_text

def do_edit_text_bottom_check_box_check(data):
    curs = conn.cursor()
    
    curs.execute(db_change('select data from other where name = "copyright_checkbox_text"'))
    db_data = curs.fetchall()
    if db_data and db_data[0][0] != '':
        if data != 'yes':
            return 1
        
    return 0

def do_edit_send_check(data):
    curs = conn.cursor()
    
    curs.execute(db_change('select data from other where name = "edit_bottom_compulsion"'))
    db_data = curs.fetchall()
    if db_data and db_data[0][0] != '':
        if acl_check(None, 'edit_bottom_compulsion') == 1:
            if data == '':
                return 1
    
    return 0

def do_edit_slow_check():
    curs = conn.cursor()

    curs.execute(db_change("select data from other where name = 'slow_edit'"))
    slow_edit = curs.fetchall()
    if slow_edit and slow_edit[0][0] != '':
        if acl_check(None, 'slow_edit') == 1:
            slow_edit = int(number_check(slow_edit[0][0]))

            curs.execute(db_change(
                "select date from history where ip = ? order by date desc limit 1"
            ), [ip_check()])
            last_edit_data = curs.fetchall()
            if last_edit_data:
                last_edit_data = int(re.sub(' |:|-', '', last_edit_data[0][0]))
                now_edit_data = int((
                    datetime.datetime.now() - datetime.timedelta(seconds = slow_edit)
                ).strftime("%Y%m%d%H%M%S"))

                if last_edit_data > now_edit_data:
                    return 1

    return 0

def do_edit_filter(data):
    curs = conn.cursor()

    if admin_check(1) != 1:
        curs.execute(db_change(
            "select plus, plus_t from html_filter where kind = 'regex_filter' and plus != ''"
        ))
        for data_list in curs.fetchall():
            match = re.compile(data_list[0], re.I)
            if match.search(data):
                ban_insert(
                    ip_check(),
                    '0' if data_list[1] == 'X' else data_list[1],
                    'edit filter',
                    None,
                    'tool:edit filter'
                )

                return 1

    return 0

def do_title_length_check(name, check_type = 'document'):
    curs = conn.cursor()
    
    if check_type == 'topic':
        curs.execute(db_change('select data from other where name = "title_topic_max_length"'))
        db_data = curs.fetchall()
        if db_data and db_data[0][0] != '':
            db_data = int(number_check(db_data[0][0]))
            if len(name) > db_data:        
                return 1
    else:
        curs.execute(db_change('select data from other where name = "title_max_length"'))
        db_data = curs.fetchall()
        if db_data and db_data[0][0] != '':
            db_data = int(number_check(db_data[0][0]))
            if len(name) > db_data:        
                return 1
    
    return 0

# Func-insert
def do_add_thread(thread_code, thread_data, thread_top = '', thread_id = ''):
    curs = conn.cursor()
    
    if thread_id == '':
        curs.execute(db_change("select id from topic where code = ? order by id + 0 desc limit 1"), [thread_code])
        db_data = curs.fetchall()
        if db_data:
            thread_id = str(int(db_data[0][0]) + 1)
        else:
            thread_id = '1'
        
    curs.execute(db_change("insert into topic (id, data, date, ip, block, top, code) values (?, ?, ?, ?, ?, '', ?)"), [
        thread_id,
        thread_data,
        get_time(),
        ip_check(),
        thread_top,
        thread_code
    ])
    
    conn.commit()
    
def do_reload_recent_thread(topic_num, date, name = None, sub = None):
    curs = conn.cursor()

    curs.execute(db_change("select code from rd where code = ?"), [topic_num])
    if curs.fetchall():
        curs.execute(db_change("update rd set date = ? where code = ?"), [
            date, 
            topic_num
        ])
    else:
        curs.execute(db_change(
            "insert into rd (title, sub, code, date, band, stop, agree, acl) values (?, ?, ?, ?, '', '', '', '')"
        ), [
            name, 
            sub, 
            topic_num, 
            date
        ])

    conn.commit()

def add_alarm(who, context):
    curs = conn.cursor()

    curs.execute(db_change(
        'insert into alarm (name, data, date) values (?, ?, ?)'
    ), [who, context, get_time()])
    conn.commit()
    
def add_user(user_name, user_pw, user_email = '', user_encode = ''):
    curs = conn.cursor()

    if user_encode == '':
        user_pw_hash = pw_encode(user_pw)

        curs.execute(db_change('select data from other where name = "encode"'))
        data_encode = curs.fetchall()
        data_encode = data_encode[0][0]
    else:
        user_pw_hash = user_pw
        data_encode = user_encode

    curs.execute(db_change("select id from user_set limit 1"))
    if not curs.fetchall():
        user_auth = 'owner'
    else:
        user_auth = 'user'

    curs.execute(db_change("insert into user_set (id, name, data) values (?, 'pw', ?)"), [
        user_name,
        user_pw_hash
    ])
    curs.execute(db_change("insert into user_set (id, name, data) values (?, 'acl', ?)"), [
        user_name,
        user_auth
    ])
    curs.execute(db_change("insert into user_set (id, name, data) values (?, 'date', ?)"), [
        user_name,
        get_time()
    ])
    curs.execute(db_change("insert into user_set (id, name, data) values (?, 'encode', ?)"), [
        user_name,
        data_encode
    ])
    
    if user_email != '':
        curs.execute(db_change("insert into user_set (name, id, data) values ('email', ?, ?)"), [
            user_name,
            user_email
        ])
        
    conn.commit()
    
def ua_plus(u_id, u_ip, u_agent, time):
    curs = conn.cursor()

    curs.execute(db_change("select data from other where name = 'ua_get'"))
    rep_data = curs.fetchall()
    if rep_data and rep_data[0][0] != '':
        pass
    else:
        curs.execute(db_change(
            "insert into ua_d (name, ip, ua, today, sub) values (?, ?, ?, ?, '')"
        ), [
            u_id, 
            u_ip, 
            u_agent, 
            time
        ])
        conn.commit()

def ban_insert(name, end, why, login, blocker, type_d = None):
    curs = conn.cursor()

    now_time = get_time()
    band = type_d if type_d else ''

    curs.execute(db_change(
        "update rb set ongoing = '' where end < ? and end != '' and ongoing = '1'"
    ), [now_time])
    curs.execute(db_change("" + \
        "select block from rb " + \
        "where ((end > ? and end != '') or end = '') and block = ? and " + \
            "band = ? and ongoing = '1'" + \
    ""), [now_time, name, band])
    if curs.fetchall():
        curs.execute(db_change(
            "insert into rb (block, end, today, blocker, why, band) values (?, ?, ?, ?, ?, ?)"
        ), [
            name,
            'release',
            now_time,
            blocker,
            '',
            band
        ])
        curs.execute(db_change(
            "update rb set ongoing = '' where block = ? and band = ? and ongoing = '1'"
        ), [name, band])
    else:
        login = 'O' if login != '' else ''

        if end != '0':
            end = int(number_check(end))
            time = datetime.datetime.now()
            plus = datetime.timedelta(seconds = end)
            r_time = (time + plus).strftime("%Y-%m-%d %H:%M:%S")
        else:
            r_time = ''

        curs.execute(db_change(
            "insert into rb (block, end, today, blocker, why, band, ongoing, login) " + \
            "values (?, ?, ?, ?, ?, ?, '1', ?)"
        ), [
            name, 
            r_time, 
            now_time, 
            blocker, 
            why, 
            band,
            login
        ])

    conn.commit()

def history_plus(title, data, date, ip, send, leng, t_check = '', mode = ''):
    curs = conn.cursor()
    # 여기 좀 느린 듯
    
    curs.execute(db_change('select data from other where name = "history_recording_off"'))
    db_data = curs.fetchall()
    if db_data and db_data[0][0] != '':
        return 0

    if mode == 'add':
        curs.execute(db_change(
            "select id from history where title = ? order by id + 0 asc limit 1"
        ), [title])
        id_data = curs.fetchall()
        id_data = str(int(id_data[0][0]) - 1) if id_data else '0'
    else:
        curs.execute(db_change(
            "select id from history where title = ? order by id + 0 desc limit 1"
        ), [title])
        id_data = curs.fetchall()
        id_data = str(int(id_data[0][0]) + 1) if id_data else '1'
        
        mode = mode if not re.search('^user:', title) else 'user'

    send = re.sub(r'\(|\)|<|>', '', send)
    send = send[:128] if len(send) > 128 else send
    send = send + ' (' + t_check + ')' if t_check != '' else send

    if mode != 'add' and mode != 'user':
        curs.execute(db_change("select count(*) from rc where type = 'normal'"))
        if curs.fetchall()[0][0] >= 200:
            curs.execute(db_change(
                "select id, title from rc where type = 'normal' order by date asc limit 1"
            ))
            rc_data = curs.fetchall()
            if rc_data:
                curs.execute(db_change(
                    'delete from rc where id = ? and title = ? and type = "normal"'
                ), [
                    rc_data[0][0],
                    rc_data[0][1]
                ])
    
        curs.execute(db_change(
            "insert into rc (id, title, date, type) values (?, ?, ?, 'normal')"
        ), [
            id_data,
            title,
            date
        ])
    
    if mode != 'add':
        curs.execute(db_change("select count(*) from rc where type = ?"), [mode])
        if curs.fetchall()[0][0] >= 200:
            curs.execute(db_change(
                "select id, title from rc where type = ? order by date asc limit 1"
            ), [mode])
            rc_data = curs.fetchall()
            if rc_data:
                curs.execute(db_change(
                    'delete from rc where id = ? and title = ? and type = ?'
                ), [
                    rc_data[0][0],
                    rc_data[0][1],
                    mode
                ])
    
        curs.execute(db_change(
            "insert into rc (id, title, date, type) values (?, ?, ?, ?)"
        ), [
            id_data,
            title,
            date,
            mode
        ])
            
    curs.execute(db_change(
        "insert into history (id, title, data, date, ip, send, leng, hide, type) " + \
        "values (?, ?, ?, ?, ?, ?, ?, '', ?)"
    ), [
        id_data,
        title,
        data,
        date,
        ip,
        send,
        leng,
        mode
    ])

    data_set_exist = '' if t_check != 'delete' else '1'

    curs.execute(db_change("select doc_name from data_set where doc_name = ? and set_name = 'last_edit'"), [title])
    db_data = curs.fetchall()
    if db_data:
        curs.execute(db_change("update data_set set set_data = ?, doc_rev = ? where doc_name = ? and set_name = 'last_edit'"), [date, data_set_exist, title])
    else:
        curs.execute(db_change("insert into data_set (doc_name, doc_rev, set_name, set_data) values (?, ?, 'last_edit', ?)"), [title, data_set_exist, date])

# Func-error
def re_error(data):
    curs = conn.cursor()

    conn.commit()

    if data == '/ban':
        if ban_check() == 1:
            end = '<div id="opennamu_get_user_info">' + ip_check() + '</div>'
        else:
            end = '<ul class="opennamu_ul"><li>' + load_lang('authority_error') + '</li></ul>'

        return easy_minify(flask.render_template(skin_check(),
            imp = [load_lang('error'), wiki_set(), wiki_custom(), wiki_css([0, 0])],
            data = '<h2>' + load_lang('error') + '</h2>' + end,
            menu = 0
        )), 401
    else:
        num = int(number_check(data.replace('/error/', '')))
        if num == 1:
            data = load_lang('no_login_error')
        elif num == 2:
            data = load_lang('no_exist_user_error')
        elif num == 3:
            data = load_lang('authority_error')
        elif num == 4:
            data = load_lang('no_admin_block_error')
        elif num == 5:
            data = load_lang('error_skin_set')
        elif num == 6:
            data = load_lang('same_id_exist_error')
        elif num == 7:
            data = load_lang('long_id_error')
        elif num == 8:
            data = load_lang('id_char_error') + ' <a href="/name_filter">(' + load_lang('id_filter_list') + ')</a>'
        elif num == 9:
            data = load_lang('file_exist_error')
        elif num == 10:
            data = load_lang('password_error')
        elif num == 11:
            data = load_lang('topic_long_error')
        elif num == 12:
            data = load_lang('email_error')
        elif num == 13:
            data = load_lang('recaptcha_error')
        elif num == 14:
            data = load_lang('file_extension_error') + ' <a href="/extension_filter">(' + load_lang('extension_filter_list') + ')</a>'
        elif num == 15:
            data = load_lang('edit_record_error')
        elif num == 16:
            data = load_lang('same_file_error')
        elif num == 17:
            curs.execute(db_change('select data from other where name = "upload"'))
            db_data = curs.fetchall()
            file_max = int(number_check(db_data[0][0])) if db_data and db_data[0][0] != '' else '2'

            data = load_lang('file_capacity_error') + file_max
        elif num == 18:
            data = load_lang('email_send_error')
        elif num == 19:
            data = load_lang('move_error')
        elif num == 20:
            data = load_lang('password_diffrent_error')
        elif num == 21:
            data = load_lang('edit_filter_error')
        elif num == 22:
            data = load_lang('file_name_error')
        elif num == 23:
            data = load_lang('regex_error')
        elif num == 24:
            curs.execute(db_change("select data from other where name = 'slow_edit'"))
            db_data = curs.fetchall()
            db_data = '' if not db_data else db_data[0][0]
            data = load_lang('fast_edit_error') + db_data
        elif num == 25:
            data = load_lang('too_many_dec_error')
        elif num == 26:
            data = load_lang('application_not_found')
        elif num == 27:
            data = load_lang("invalid_password_error")
        elif num == 28:
            data = load_lang('watchlist_overflow_error')
        elif num == 29:
            data = load_lang('copyright_disagreed')
        elif num == 30:
            data = load_lang('ie_wrong_callback')
        elif num == 33:
            data = load_lang('restart_fail_error')
        elif num == 34:
            data = load_lang("update_error") + ' <a href="https://github.com/opennamu/opennamu">(Github)</a>'
        elif num == 35:
            data = load_lang('same_email_error')
        elif num == 36:
            data = load_lang('input_email_error')
        elif num == 37:
            data = load_lang('error_edit_send_request')
        elif num == 38:
            curs.execute(db_change("select data from other where name = 'title_max_length'"))
            db_data = curs.fetchall()
            db_data = '' if not db_data else db_data[0][0]
            data = load_lang('error_title_length_too_long') + db_data
        elif num == 39:
            curs.execute(db_change("select data from other where name = 'title_topic_max_length'"))
            db_data = curs.fetchall()
            db_data = '' if not db_data else db_data[0][0]
            data = load_lang('error_title_length_too_long') + db_data
        elif num == 40:
            curs.execute(db_change("select data from other where name = 'password_min_length'"))
            db_data = curs.fetchall()
            if db_data and db_data[0][0] != '':
                password_min_length = db_data[0][0]
            else:
                password_min_length = ''
                
            data = load_lang('error_password_length_too_short') + password_min_length
        else:
            data = '???'

        if num == 5:
            if flask.request.path != '/skin_set':
                data += '<br>' + load_lang('error_skin_set_old') + ' <a href="/skin_set">(' + load_lang('go') + ')</a>'

            title = load_lang('skin_set')
            tool = [['change', load_lang('user_setting')], ['change/skin_set/main', load_lang('main_skin_set')]]
            load_skin_set = ''
        
            return easy_minify(flask.render_template(skin_check(),
                imp = [title, wiki_set(), wiki_custom(), wiki_css([0, 0])],
                data = '' + \
                    '<div id="main_skin_set">' + \
                        '<h2>' + load_lang('error') + '</h2>' + \
                        '<ul class="opennamu_ul">' + \
                            '<li>' + data + '</a></li>' + \
                        '</ul>' + \
                    '</div>' + \
                    load_skin_set,
                menu = tool
            ))
        else:
            return easy_minify(flask.render_template(skin_check(),
                imp = [load_lang('error'), wiki_set(), wiki_custom(), wiki_css([0, 0])],
                data = '' + \
                     '<h2>' + load_lang('error') + '</h2>' + \
                     '<ul class="opennamu_ul">' + \
                         '<li>' + data + '</li>' + \
                     '</ul>' + \
                '',
                menu = 0
            )), 400
