#!/usr/bin/env python
# -*- coding: utf-8 -*-

# internal dependencies
from posts import Posts

# external dependencies
from bottle import Bottle, route, run, post, get, request, response, redirect, error, abort, static_file, TEMPLATE_PATH, Jinja2Template, url
from bottle import jinja2_template as template, jinja2_view as view
from bs4 import BeautifulSoup
import user_agents

# stdlib dependencies
import json, time, os, pprint, string, re, random
from datetime import datetime

### Global objects
TEMPLATE_PATH.append(os.path.join(os.path.split(os.path.realpath(__file__))[0],'views'))
POSTS = object()
BASELINK = None
DEFAULT_CONTEXT = {
  'author': "John Doe",
  'blog_title': "Local Blog",
  'catchphrase': "Your blog, served from your local computer",
  'url': url,
  'months': [],
  'external_links': [],
  'active': '',
  'ua': user_agents.parse(''),
  'additional_header_html': '',
  'additional_below_post_heading_html': '',
  'additional_leaderboard_html': '',
  'additional_sidebar_html': '',
  'show_experiment': False,
  'experiment_html': '',
  'favicon': None,
  'meta_author': None,
  'meta_copyright': None,
}
ALLOW_CRAWLING = 'Disallow'
FAVICON = None # 2-tuple containing path and filename of the favicon to serve
EXPERIMENT_PROBABILITY = 0.01
MEDIA_FOLDER = None

### The Bottle web application
interface = Bottle()

@interface.route('/static/<path:path>')
def static(path):
    return static_file(path, root='./static')

@interface.route('/wp-content/uploads/<path:path>')
@interface.route('/assets/<path:path>')
def static(path):
    match = re.match(r".*(?P<thumb>-(?P<sizex>\d+)x(?P<sizey>\d+))\..*", path)
    if match:
        path = path.replace(match.group('thumb'), '')
    return static_file(path, root=MEDIA_FOLDER)

@interface.route('/')
@view('list_posts.jinja2')
def home():
    list_title = 'The latest posts'
    posts = POSTS.posts[:8]
    return dict(active='home', posts=posts, list_title=list_title)

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
    ret_list = []
    ct = concat_tags()
    for tag in unique_tags():
        ret_list.append({'name': tag, 'occurrence': ct.count(tag)})
    ret_list = sorted(ret_list, key=lambda k: k['occurrence'], reverse=True)
    return dict(property=ret_list, introduction_paragraph=descr, property_name='Tag', active='tags')

@interface.route('/categories')
@view('property_list.jinja2')
def categorylist():
    descr = 'The categories of posts in this blog:'
    ret_list = []
    cc = concat_categories()
    for category in unique_categories():
        ret_list.append({'name': category, 'occurrence': cc.count(category)})
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
        return dict(post=result[0])
    else: abort(404, "No such blog post.")

@interface.route('/<year:int>/<month:int>/<slug>')
@view('post.jinja2')
def post_from_link(year, month, slug):
    result = [post for post in POSTS.posts if post['year'] == year and post['month'] == month and post['slug'] == slug]
    if len(result) == 1:
        post = result[0]
        return dict(post=result[0])
    else: abort(404, "No such blog post.")

@interface.route('/robots.txt')
def robots():
    response.content_type = 'text/plain'
    return "User-agent: *\n{0}: /".format(ALLOW_CRAWLING)

@interface.route('/sitemap.xml')
@view('sitemap.jinja2')
def sitemap():
    if not BASELINK:
        abort(404, "No baselink set -> no sitemap available due to missing absolute URLs.")
    #response.content_type = 'xml/application'
    response.content_type = 'text/xml;charset=UTF-8'
    urls = []
    urls.append({'loc': BASELINK, 'priority': '1.0'})
    urls.append({'loc': BASELINK + '/search', 'priority': '0.5'})
    for post in POSTS.posts:
        url = {}
        if post['address']:
            url['loc'] = BASELINK + post['address']
        else:
            url['loc'] = BASELINK + '/post/{status}/{file}'.format(**post)
        url['lastmod'] = post['modification_date'].date().isoformat()
        url['priority'] = '{:.1f}'.format(1.0)
        urls.append(url)
    for tag in unique_tags():
        urls.append({'loc': BASELINK + '/tag/' + tag, 'priority': '0.2'})
    for category in unique_categories():
        urls.append({'loc': BASELINK + '/category/' + category, 'priority': '0.2'})
    for d in POSTS.years:
        urls.append({'loc': BASELINK + '/{year}'.format(year=d.year), 'priority': '0.2'})
    for d in POSTS.months:
        urls.append({'loc': BASELINK + '/{year}/{month}'.format(year=d.year, month=d.month), 'priority': '0.2'})
    return {'urls': urls}

@interface.route('/favicon.ico')
def get_favicon():
    if FAVICON:
        path, filename = FAVICON
        return static_file(filename, root=path)
    else:
        abort(404, "No favicon set")


@interface.hook('before_request')
def set_ua():
    ua_string = request.environ.get('HTTP_USER_AGENT', '')
    ua = user_agents.parse(ua_string)
    Jinja2Template.defaults['ua'] = ua
    Jinja2Template.defaults['show_experiment'] = random.random() < EXPERIMENT_PROBABILITY


### posts helper functions

def concat_tags():
    """ Return a concatenated list of all tags found in any post """
    tags = []
    for post in POSTS.posts:
        tags += post['tags']
    return tags

def concat_categories():
    """ Return a concatenated list of all categories found in any post. Exclude the special 'Uncategorized' category. """
    categories = []
    for post in POSTS.posts:
        categories += post['categories']
    return [c for c in categories if c != 'Uncategorized']

def unique_tags():
    return set(concat_tags())

def unique_categories():
    return set(concat_categories())


class StripPathMiddleware(object):
  def __init__(self, app):
    self.app = app
  def __call__(self, e, h):
    e['PATH_INFO'] = e['PATH_INFO'].rstrip('/')
    return self.app(e,h)


def main():
    global POSTS, DEFAULT_CONTEXT, ALLOW_CRAWLING, FAVICON, EXPERIMENT_PROBABILITY, MEDIA_FOLDER, BASELINK
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
    parser.add_argument('--additional-header-html', help='Additional HTML content to be added to the header of each page')
    parser.add_argument('--additional-below-post-heading-html', help='Additional HTML content to be added below the heading of each post')
    parser.add_argument('--additional-leaderboard-html', help='Additional HTML content to be added as leaderboard')
    parser.add_argument('--additional-sidebar-html', help='Additional HTML content to be added to the sidebar')
    parser.add_argument('--external-links', '-e', help='Links to external sites of yours. Specify like Github=http://github.com,Twitter=http://twitter.com')
    parser.add_argument('--published-only', '-o', action='store_true', help='Restrict the posts shown to those already published.')
    parser.add_argument('--favicon', help='favicon image file')
    parser.add_argument('--experiment-probability', type=float, help='Set a probability for showing an experiment (instead of the additional HTML in the leaderboard)')
    parser.add_argument('--experiment-html', help='HTML content to show if the experiment is carried out. Will show instead of leaderboard')
    parser.add_argument('--copyright', default="Copyright (c)", help='Copyright statement')
    parser.add_argument('--baselink', '-b',
      help='Baselink of your blog, like http://philipp.wordpress.com')
    parser.add_argument('--media-folder', help='The folder containing the media files (defaults to "assets" inside the blog entries folder).')
    parser.add_argument('folder', help='The folder of blog entries.')
    args = parser.parse_args()

    ALLOW_CRAWLING = 'Allow' if args.allow_crawling else 'Disallow'

    POSTS = Posts(args.folder)

    if args.media_folder:
        MEDIA_FOLDER = args.media_folder
    else:
        MEDIA_FOLDER = os.path.join(args.folder, 'assets')

    if args.baselink:
        BASELINK = args.baselink

    if args.published_only:
        POSTS.keep_only_published()

    DEFAULT_CONTEXT['months'] = POSTS.months

    if args.external_links:
        for el in args.external_links.split(','):
            parts = el.split('=')
            DEFAULT_CONTEXT['external_links'].append({'name': parts[0], 'url': parts[1]})

    if args.favicon:
        FAVICON = os.path.split(args.favicon)
        DEFAULT_CONTEXT['favicon'] = '/favicon.ico'

    if args.experiment_probability:
        clamp = lambda n, minn, maxn: max(min(maxn, n), minn)
        EXPERIMENT_PROBABILITY = clamp(args.experiment_probability, 0., 1.)
    if args.experiment_html:
        DEFAULT_CONTEXT['experiment_html'] = args.experiment_html

    if args.copyright:
        DEFAULT_CONTEXT['meta_copyright'] = args.copyright

    if args.about:
        DEFAULT_CONTEXT['about'] = args.about

    if args.additional_header_html:
        DEFAULT_CONTEXT['additional_header_html'] = args.additional_header_html

    if args.additional_below_post_heading_html:
        DEFAULT_CONTEXT['additional_below_post_heading_html'] = args.additional_below_post_heading_html

    if args.additional_leaderboard_html:
        DEFAULT_CONTEXT['additional_leaderboard_html'] = args.additional_leaderboard_html

    if args.additional_sidebar_html:
        DEFAULT_CONTEXT['additional_sidebar_html'] = args.additional_sidebar_html

    if args.author:
        DEFAULT_CONTEXT['author'] = args.author
        DEFAULT_CONTEXT['meta_author'] = args.author

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

