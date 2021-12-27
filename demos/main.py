"""One shared terminal per URL endpoint

Plus a /new URL which will create a new terminal and redirect to it.
"""
from __future__ import print_function, absolute_import

import tornado.web
# This demo requires tornado_xstatic and XStatic-term.js
import tornado_xstatic
from database import JSONDatabase
import argparse
import pathlib

import terminado
from terminado import TermSocket, NamedTermManager
from common_demo_stuff import run_and_show_browser, STATIC_DIR, TEMPLATE_DIR


parser = argparse.ArgumentParser(description="Tmux class")
parser.add_argument("-p", "--password", dest="admin_password", required=True, type=str,
                    help="Password for user 'admin' to access admin pane")
parser.add_argument("-d", "--database", dest="db_json_path", default=None, type=str,
                    help="Path to json file, where will be info about usernanes and passwords. Default: data dir in project folder")
args = parser.parse_args()
if args.db_json_path is None:
    path_to_db = pathlib.Path(terminado.__file__).parents[2] / 'data' / 'database.json'
else:
    path_to_db = pathlib.Path(args.db_json_path)

DATABASE = JSONDatabase(path_to_db)
DATABASE.save_username_password("admin", args.admin_password)
ws_pathes = {}

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")

class MainHandler(BaseHandler):
    def get(self):
        self.redirect("/login")


class LoginHandler(BaseHandler):
    def get(self):
        if not self.current_user:
            self.render("auth.html", title="Login form")
            return
        self.redirect("/admin")

    def post(self):
        global DATABASE
        if DATABASE.check_username(self.get_argument("uname", default=None)):
            if DATABASE.check_username_password(self.get_argument("uname", default=None), self.get_argument("psw", default=None)):
                bool_remember = False if self.get_argument("remember", default=None) is None else True
                exp_days = 1 if not bool_remember else None
                self.set_secure_cookie("user", self.get_argument("uname", default=None), expires_days=exp_days)
                DATABASE.save_remember(self.get_argument("uname", default=None), bool_remember)
                self.redirect("/students/" + self.get_argument("uname"), permanent=False)
            else:
                self.redirect("wrong_psw_auth.html")
        else:
            self.redirect("wrong_username_auth.html")

class RegistrationHandler(BaseHandler):
    def get(self):
        if self.current_user:
            self.redirect("/login")
        else:
            self.render("registration.html", title="Registration form")

    def post(self):
        global DATABASE
        if DATABASE.check_username(self.get_argument("uname")):
            self.redirect("/registration_user_exists.html")
        else:
            if self.get_argument("psw") is not None and self.get_argument("uname") != '':
                DATABASE.save_username_password(self.get_argument("uname"), self.get_argument("psw"))
                self.redirect("/auth.html")
            else:
                self.redirect("/registration_no_password.html")


class LogoutHandler(BaseHandler):
    def get(self):
        if self.current_user:
            self.clear_cookie("user")
        self.redirect("/login", permanent=False)

class PageHandler(BaseHandler):
    """Render the /ttyX pages"""

    def get(self, term_name):
        if not self.current_user:
            self.redirect("/login")
            return
        username = self.current_user.decode('UTF-8')
        if username == 'admin':
            return self.render("ex.html", static=self.static_url,
                               xstatic=self.application.settings['xstatic_url'],
                               values=list(ws_pathes.values()), keys=list(ws_pathes.keys()))
        else:
            term_name, terminal = self.application\
                .settings['term_manager']\
                .new_named_terminal(name=username, shell_command=['tmux', 'new-session', '-A', '-s', username])
            ws_pathes[username] = "/_websocket/students/" + term_name
            return self.render("termpage.html", static=self.static_url,
                               xstatic=self.application.settings['xstatic_url'],
                               ws_url_path="/_websocket/students/" + term_name)

def main():
    term_manager = NamedTermManager(shell_command=['tmux','new-session', '-A', '-s', 'main'], max_terminals=100)
    handlers = [
        (r"/", MainHandler),
        (r"/login", LoginHandler),
        (r"/logout", LogoutHandler),
        (r"/registration", RegistrationHandler),
        (r"/(auth.html)", tornado.web.StaticFileHandler, {'path': './templates'}),
        (r"/(wrong_psw_auth.html)", tornado.web.StaticFileHandler, {'path': './templates'}),
        (r"/(wrong_username_auth.html)", tornado.web.StaticFileHandler, {'path': './templates'}),
        (r"/(registration.html)", tornado.web.StaticFileHandler, {'path': './templates'}),
        (r"/(registration_user_exists.html)", tornado.web.StaticFileHandler, {'path': './templates'}),
        (r"/(registration_no_password.html)", tornado.web.StaticFileHandler, {'path': './templates'}),
        (r"/(avatar.png)", tornado.web.StaticFileHandler, {'path': './templates'}),
        (r"/_websocket/students/(\w+)", TermSocket, {'term_manager': term_manager}),
        #(r"/_websocket/students/(\w+)", TermSocket, {'term_manager': term_manager}),
        (r"/students/(\w+)/?|/admin", PageHandler),
        (r"/xstatic/(.*)", tornado_xstatic.XStaticFileHandler)
    ]
    application = tornado.web.Application(handlers, static_path=STATIC_DIR,
                              template_path=TEMPLATE_DIR,
                              xstatic_url=tornado_xstatic.url_maker('/xstatic/'),
                              term_manager=term_manager, cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__")

    application.listen(8700, 'localhost')
    # run_and_show_browser("http://localhost:8700/login", term_manager)
    run_and_show_browser("http://localhost:8700/", term_manager)
    # run_and_show_browser("http://localhost:8700/public/new", term_manager)



if __name__ == "__main__":
    main()
