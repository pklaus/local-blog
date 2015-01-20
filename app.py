#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bottle import Bottle, route, run, post, get, request, response, redirect, error, abort, static_file, TEMPLATE_PATH
from bottle import jinja2_template as template, jinja2_view as view
import json
import time
import os
import pprint
from datetime import datetime
import string
import re
from posts import Posts
import markdown

TEMPLATE_PATH.append(os.path.join(os.path.split(os.path.realpath(__file__))[0],'views'))

interface = Bottle()

POSTS = object()

@interface.route('/static/<path:path>')
def static(path):
    return static_file(path, root='./static')

@interface.route('/')
@view('home.jinja2')
def home():
    return dict()

@interface.route('/search/<search_phrase>')
@view('search.jinja2')
def search(search_phrase):
    if not search_phrase: return dict(results=None)
    return dict(results=POSTS.search_literally(search_phrase))

@interface.route('/<year:int>/<month:int>/<slug>')
@view('post.jinja2')
def show_latest(year, month, slug):
    result = [post for post in POSTS.posts if post['year'] == year and post['month'] == month and post['slug'] == slug]
    if len(result) == 1:
        post = result[0]
        post['rendered_content'] = markdown.markdown(post['content'], extensions=['markdown.extensions.tables', 'markdown.extensions.codehilite'])
        return dict(post=result[0])
    else: abort(404, "No such blog post.")

class StripPathMiddleware(object):
  def __init__(self, app):
    self.app = app
  def __call__(self, e, h):
    e['PATH_INFO'] = e['PATH_INFO'].rstrip('/')
    return self.app(e,h)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser( 
      description='Run a local blog.' )
    parser.add_argument('-p', '--port', type=int, default=8080,
      help='The port to run the web server on.')
    parser.add_argument('-6', '--ipv6', action='store_true',
      help='Listen to incoming connections via IPv6 instead of IPv4.')
    parser.add_argument('-d', '--debug', action='store_true',
      help='Start in debug mode (with verbose HTTP error pages.')
    parser.add_argument('-l', '--log-file',
      help='The file to store the server log in.')
    parser.add_argument('--baselink', '-b',
      help='Baselink of your blog, like http://philipp.wordpress.com')
    parser.add_argument('folder', help='The folder of blog entries.')
    args = parser.parse_args()

    if args.baselink:
        POSTS = Posts(args.folder, args.baselink)
    else:
        POSTS = Posts(args.folder)

    app = StripPathMiddleware(interface)

    if args.debug and args.ipv6:
        args.error('You cannot use IPv6 in debug mode, sorry.')
    if args.debug:
        run(app, host='0.0.0.0', port=args.port, debug=True, reloader=True)
    else:
        if args.ipv6:
            # CherryPy is Python3 ready and has IPv6 support:
            run(app, host='::', server='cherrypy', port=args.port)
        else:
            run(app, host='0.0.0.0', server='cherrypy', port=args.port)

