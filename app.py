#!/usr/bin/env python
# -*- coding: utf-8 -*-

# internal dependencies
from posts import Posts

# external dependencies
from bottle import Bottle, route, run, post, get, request, response, redirect, error, abort, static_file, TEMPLATE_PATH, Jinja2Template, url
from bottle import jinja2_template as template, jinja2_view as view
from bs4 import BeautifulSoup
import markdown

# stdlib dependencies
import json, time, os, pprint, string, re
from datetime import datetime

### Global objects
TEMPLATE_PATH.append(os.path.join(os.path.split(os.path.realpath(__file__))[0],'views'))
POSTS = object()
DEFAULT_CONTEXT = {
  'author': "John Doe",
  'blog_title': "Local Blog",
  'catchphrase': "Your blog, served from your local computer",
  'url': url,
  'months': [],
  'external_links': [],
  'active': ''
}
ALLOW_CRAWLING = 'Disallow'
MD_EXTENSIONS = [
  'markdown.extensions.abbr',
  'markdown.extensions.tables',
  'markdown.extensions.codehilite(linenums=False)'
]

### The Bottle() web application
interface = Bottle()

@interface.route('/static/<path:path>')
def static(path):
    return static_file(path, root='./static')

@interface.route('/wp-content/uploads/<path:path>')
@interface.route('/assets/<path:path>')
def static(path):
    media_path = POSTS.get_media_path(path)
    if not media_path: abort(404, "No such blog post.")
    return static_file(media_path, root=POSTS.folder)

@interface.route('/')
@view('home.jinja2')
def home():
    return dict(active='home')

@interface.route('/tag/<tag>')
@view('list_posts.jinja2')
def tag_postlist(tag):
    list_title = 'Posts with the tag ' + tag
    posts = [post for post in POSTS.posts if tag in post['tags']]
    return dict(posts=posts, list_title=list_title)

@interface.route('/category/<category>')
@view('list_posts.jinja2')
def category_postlist(category):
    list_title = 'Posts with the category ' + category
    posts = [post for post in POSTS.posts if category in post['categories']]
    return dict(posts=posts, list_title=list_title)

@interface.route('/tags')
@view('property_list.jinja2')
def taglist():
    descr = 'All tags given to blog posts in this blog:'
    tags, ret_list = [], []
    for post in POSTS.posts:
        tags += post['tags']
    unique_tags = set(tags)
    for tag in unique_tags:
        ret_list.append({'name': tag, 'occurrence': tags.count(tag)})
    ret_list = sorted(ret_list, key=lambda k: k['occurrence'], reverse=True)
    return dict(property=ret_list, introduction_paragraph=descr, property_name='Tag', active='tags')

@interface.route('/categories')
@view('property_list.jinja2')
def categorylist():
    descr = 'The categories of posts in this blog:'
    categories, ret_list = [], []
    for post in POSTS.posts:
        categories += post['categories']
    unique_categories = set(categories)
    unique_categories.remove('Uncategorized')
    for category in unique_categories:
        ret_list.append({'name': category, 'occurrence': categories.count(category)})
    ret_list = sorted(ret_list, key=lambda k: k['occurrence'], reverse=True)
    return dict(property=ret_list, introduction_paragraph=descr, property_name='Category', active='categories')

@interface.route('/search')
@view('search.jinja2')
def search():
    return dict(active='search', posts=[])

@interface.route('/search/<search_phrase>')
@view('search.jinja2')
def search(search_phrase):
    results = POSTS.search_literally(search_phrase)
    return dict(active='search', posts=results, search_phrase=search_phrase)

@interface.route('/<year:int>')
@view('list_posts.jinja2')
def year_postlist(year):
    list_title = 'Posts from {:04d}'.format(year)
    posts = [post for post in POSTS.posts if post['year'] == year]
    return dict(posts=posts, list_title=list_title)

@interface.route('/<year:int>/<month:int>')
@view('list_posts.jinja2')
def year_month_postlist(year, month):
    list_title = 'Posts from {:04d}-{:02d}'.format(year, month)
    posts = [post for post in POSTS.posts if post['year'] == year and post['month'] == month]
    return dict(posts=posts, list_title=list_title)

@interface.route('/latest')
@view('post.jinja2')
def latest_post():
    post = POSTS.latest
    redirect(post['address'] or '/post/{status}/{file}'.format(**post))

@interface.route('/post/<status>/<file>')
@view('post.jinja2')
def post_from_filename(status, file):
    result = [post for post in POSTS.posts if post['status'] == status and post['file'] == file]
    if len(result) == 1:
        post = result[0]
        post['rendered_content'] = markdown.markdown(post['content'], extensions=MD_EXTENSIONS)
        return dict(post=result[0])
    else: abort(404, "No such blog post.")

@interface.route('/<year:int>/<month:int>/<slug>')
@view('post.jinja2')
def post_from_link(year, month, slug):
    result = [post for post in POSTS.posts if post['year'] == year and post['month'] == month and post['slug'] == slug]
    if len(result) == 1:
        post = result[0]
        post['rendered_content'] = markdown.markdown(post['content'], extensions=MD_EXTENSIONS)
        post['rendered_content'] = add_scrollable_to_pre(post['rendered_content'])
        return dict(post=result[0])
    else: abort(404, "No such blog post.")

@interface.route('/robots.txt')
def robots():
    response.content_type = 'text/plain'
    return "User-agent: *\n{0}: /".format(ALLOW_CRAWLING)

class StripPathMiddleware(object):
  def __init__(self, app):
    self.app = app
  def __call__(self, e, h):
    e['PATH_INFO'] = e['PATH_INFO'].rstrip('/')
    return self.app(e,h)

def add_scrollable_to_pre(html_text):
    soup = BeautifulSoup(html_text, 'html.parser')
    pres = soup.select('.codehilite pre')
    for pre in pres:
        pre['class'] = 'pre-x-scrollable'
    return str(soup)


def main():
    global POSTS, DEFAULT_CONTEXT, ALLOW_CRAWLING
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
    parser.add_argument('--allow-crawling', action='store_true', help='Allow search engines to index the site.')
    parser.add_argument('--title', '-t', help='The title of the blog')
    parser.add_argument('--about', help='Markdown description of the blog or author')
    parser.add_argument('--catchphrase', '-c', help='A catchphrase for the blog')
    parser.add_argument('--author', '-a', help='The name of the author of the blog')
    parser.add_argument('--external-links', '-e', help='Links to external sites of yours. Specify like Github=http://github.com,Twitter=http://twitter.com')
    parser.add_argument('--published-only', '-o', action='store_true', help='Restrict the posts shown to those already published.')
    parser.add_argument('--remove-upstream-links', '-r', action='store_true', help='Remove upstream links from blog posts')
    parser.add_argument('--baselink', '-b',
      help='Baselink of your blog, like http://philipp.wordpress.com')
    parser.add_argument('folder', help='The folder of blog entries.')
    args = parser.parse_args()

    ALLOW_CRAWLING = 'Allow' if args.allow_crawling else 'Disallow'

    if args.baselink:
        POSTS = Posts(args.folder, args.baselink)
    else:
        POSTS = Posts(args.folder)

    if args.published_only:
        POSTS.keep_only_published()
    if args.remove_upstream_links:
        POSTS.remove_upstream_links()

    DEFAULT_CONTEXT['months'] = POSTS.months

    if args.external_links:
        for el in args.external_links.split(','):
            parts = el.split('=')
            DEFAULT_CONTEXT['external_links'].append({'name': parts[0], 'url': parts[1]})

    if args.about:
        DEFAULT_CONTEXT['about'] = args.about

    if args.author: DEFAULT_CONTEXT['author'] = args.author
    if args.catchphrase: DEFAULT_CONTEXT['catchphrase'] = args.catchphrase
    if args.title : DEFAULT_CONTEXT['blog_title'] = args.title
    Jinja2Template.defaults = DEFAULT_CONTEXT

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

if __name__ == '__main__':
    main()

