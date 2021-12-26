"""One shared terminal per URL endpoint

Plus a /new URL which will create a new terminal and redirect to it.
"""
from __future__ import print_function, absolute_import
import logging
import os.path
import sys
import json
from typing import Iterable
from flask import Flask, render_template

import tornado.web
# This demo requires tornado_xstatic and XStatic-term.js
import tornado_xstatic

from terminado import TermSocket, NamedTermManager
from common_demo_stuff import run_and_show_browser, STATIC_DIR, TEMPLATE_DIR

ws_pathes = {}


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")


class MainHandler(BaseHandler):
    def get(self):
        # self.clear_all_cookies()
        if not self.current_user:
            self.redirect("/login")
            return
        name = tornado.escape.xhtml_escape(self.current_user)
        if name == 'admin':
            self.redirect("/admin")
        else:
            self.redirect(f"/students/{name}")
        


class LoginHandler(BaseHandler):
    def get(self):
        # self.write('<html><body><form action="/login" method="post">'
        #            'Name: <input type="text" name="name">'
        #            '<input type="submit" value="Sign in">'
        #            '</form></body></html>')
        if self.current_user:
            self.redirect("/students/new")
        else:
            self.render("auth.html", title="My title")

    def post(self):
        self.set_secure_cookie(
            "user", self.get_argument("uname"), expires_days=None)
        # self.redirect("/students/new")
        if self.get_argument("uname") == 'admin':
            self.redirect("/" + self.get_argument("uname"), permanent=False)
        else:
            self.redirect(
                "/students/" + self.get_argument("uname"), permanent=False)


class TerminalPageHandler(BaseHandler):
    """Render the /ttyX pages"""

    def get(self, term_name):
        if not self.current_user:
            self.redirect("/login")
            return

        if self.current_user == b'admin':
            return self.render("ex.html", static=self.static_url,
                               xstatic=self.application.settings['xstatic_url'],
                               values=list(ws_pathes.values()), keys=list(ws_pathes.keys()))
        else:
            ws_pathes[self.current_user.decode(
                'UTF-8')] = "/_websocket/students/" + term_name
            return self.render("termpage.html", static=self.static_url,
                               xstatic=self.application.settings['xstatic_url'],
                               ws_url_path="/_websocket/students/"+term_name)


class NewTerminalHandler(BaseHandler):
    """Redirect to an unused terminal name"""

    def get(self):
        if not self.current_user:
            self.redirect("/login")
            return
        if self.current_user == b'admin':
            self.redirect("/" + 'admin', permanent=False)
        else:
            name, terminal = self.application.settings['term_manager'].new_named_terminal(
            )
            self.redirect("/students/" + name, permanent=False)


class AuthenticationPaneHandler(BaseHandler):
    def get(self):
        self.clear_cookie("user")
        self.render("auth.html", title="My title")


def main():
    term_manager = NamedTermManager(shell_command=['bash'],
                                    max_terminals=100)
    handlers = [
        (r"/", MainHandler),
        (r"/login", LoginHandler),
        # (r"/(index.png)", tornado.web.StaticFileHandler, {'path': './templates'}),
        # (r"/(termpage.html)", tornado.web.StaticFileHandler, {'path': './templates'}),
        # (r"/(uimod.html)", tornado.web.StaticFileHandler, {'path': './templates'}),
        #(r"/(term.js)", tornado.web.StaticFileHandler, {'path': './xstatic/pkg/termjs/data'}),
        #(r"/(terminado.js)", tornado.web.StaticFileHandler, {'path': './terminado/_static'}),
        (r"/_websocket/(\S*)", TermSocket,
         {'term_manager': term_manager}),
        #(r"/new", NewTerminalHandler),
        (r"/students/(\w+)/?|/admin", TerminalPageHandler),

        (r"/xstatic/(.*)", tornado_xstatic.XStaticFileHandler)
    ]
    application = tornado.web.Application(handlers, static_path=STATIC_DIR,
                                          template_path=TEMPLATE_DIR,
                                          xstatic_url=tornado_xstatic.url_maker(
                                              '/xstatic/'),
                                          term_manager=term_manager, cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__")

    application.listen(8700, 'localhost')
    # run_and_show_browser("http://localhost:8700/login", term_manager)
    run_and_show_browser("http://localhost:8700/", term_manager)
    # run_and_show_browser("http://localhost:8700/students/new", term_manager)


if __name__ == "__main__":
    main()
