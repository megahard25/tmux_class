"""One shared terminal per URL endpoint

Plus a /new URL which will create a new terminal and redirect to it.
"""
from __future__ import print_function, absolute_import

import tornado.web
# This demo requires tornado_xstatic and XStatic-term.js
import tornado_xstatic
from database import JSONDatabase

from terminado import TermSocket, NamedTermManager
from common_demo_stuff import run_and_show_browser, STATIC_DIR, TEMPLATE_DIR


path_to_json_file = "/mnt/c/Users/anton/programming/nets_arch/terminado/data/database.json"
DATABASE = JSONDatabase(path_to_json_file)


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")

class MainHandler(BaseHandler):
    def get(self):
        #self.clear_all_cookies()
        if not self.current_user:
            self.redirect("/login")
            return
        name = tornado.escape.xhtml_escape(self.current_user)
        self.write("Hello, " + name)

class LoginHandler(BaseHandler):
    def get(self):
        # self.write('<html><body><form action="/login" method="post">'
        #            'Name: <input type="text" name="name">'
        #            '<input type="submit" value="Sign in">'
        #            '</form></body></html>')
        if self.current_user:
            self.redirect("/public/new")
        else:
            self.render("auth.html", title="My title")

    def post(self):
        global DATABASE
        if DATABASE.check_username(self.get_argument("uname")):
            if DATABASE.check_username_password(self.get_argument("uname"), self.get_argument("psw")):
                self.set_secure_cookie("user", self.get_argument("uname"), expires_days=None)
                #self.redirect("/public/new")
                DATABASE.save_remember(self.get_argument("uname"), self.get_argument("remember"))
                if self.get_argument("remember") is None or not self.get_argument("remember"):
                    print("HERE!")
                    self.clear_cookie("user")
                self.redirect("/public/" + self.get_argument("uname"), permanent=False)
            else:
                self.redirect("wrong_psw_auth.html")
        else:
            self.redirect("wrong_username_auth.html")

class RegistrationHandler(BaseHandler):
    def get(self):
        if self.current_user:
            self.redirect("/public/new")
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


class TerminalPageHandler(BaseHandler):
    """Render the /ttyX pages"""
    def get(self, term_name):
        if not self.current_user:
            self.redirect("/login")
            return
        return self.render("termpage.html", static=self.static_url,
                           xstatic=self.application.settings['xstatic_url'],
                           ws_url_path="/_websocket/public/"+term_name)

class NewTerminalHandler(BaseHandler):
    """Redirect to an unused terminal name"""
    def get(self):
        if not self.current_user:
            self.redirect("/login")
            return
        name, terminal = self.application.settings['term_manager'].new_named_terminal()
        self.redirect("/public/" + name, permanent=False)

class AdminPaneHandler(BaseHandler):
    def get(self):
        if self.current_user:
            name, terminal = self.application.settings['term_manager'].new_named_terminal()
            # term_name = "/public/" + name
            self.redirect("/public/" + name, permanent=False)
            # self.render("auth.html", static=self.static_url,
            #                xstatic=self.application.settings['xstatic_url'],
            #                ws_url_path=r"/_websocket/(\w+)")
        else:
            self.render("auth.html", title="My title")


def main():
    term_manager = NamedTermManager(shell_command=['bash'],
                                    max_terminals=100)
    handlers = [
        (r"/", MainHandler),
        (r"/login", LoginHandler),
        (r"/admin", AdminPaneHandler),
        (r"/registration", RegistrationHandler),
        (r"/(auth.html)", tornado.web.StaticFileHandler, {'path': './templates'}),
        (r"/(wrong_psw_auth.html)", tornado.web.StaticFileHandler, {'path': './templates'}),
        (r"/(wrong_username_auth.html)", tornado.web.StaticFileHandler, {'path': './templates'}),
        (r"/(registration.html)", tornado.web.StaticFileHandler, {'path': './templates'}),
        (r"/(registration_user_exists.html)", tornado.web.StaticFileHandler, {'path': './templates'}),
        (r"/(registration_no_password.html)", tornado.web.StaticFileHandler, {'path': './templates'}),
        (r"/(avatar.png)", tornado.web.StaticFileHandler, {'path': './templates'}),
        # (r"/(termpage.html)", tornado.web.StaticFileHandler, {'path': './templates'}),
        # (r"/(uimod.html)", tornado.web.StaticFileHandler, {'path': './templates'}),
        #(r"/(term.js)", tornado.web.StaticFileHandler, {'path': './xstatic/pkg/termjs/data'}),
        #(r"/(terminado.js)", tornado.web.StaticFileHandler, {'path': './terminado/_static'}),
        (r"/_websocket/public/(\w+)", TermSocket, {'term_manager': term_manager}),
        (r"/public/new/?", NewTerminalHandler),
        (r"/public/(\w+)/?", TerminalPageHandler),
        (r"/xstatic/(.*)", tornado_xstatic.XStaticFileHandler)
    ]
    application = tornado.web.Application(handlers, static_path=STATIC_DIR,
                              template_path=TEMPLATE_DIR,
                              xstatic_url=tornado_xstatic.url_maker('/xstatic/'),
                              term_manager=term_manager, cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__")

    application.listen(8700, 'localhost')
    # run_and_show_browser("http://localhost:8700/login", term_manager)
    run_and_show_browser("http://localhost:8700/admin", term_manager)
    # run_and_show_browser("http://localhost:8700/public/new", term_manager)

if __name__ == "__main__":
    main()
