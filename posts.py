#!/usr/bin/env python

import os, re, logging
from datetime import datetime, date

from bs4 import BeautifulSoup
from markdown import markdown

logger = logging.getLogger(__name__)

MD_EXTENSIONS = [
  'markdown.extensions.abbr',
  'markdown.extensions.tables',
  'markdown.extensions.codehilite'
]
MD_EXT_CONFIGS = {
  'markdown.extensions.codehilite': { 'linenums': False, },
}
TIME_FMT = '%Y-%m-%d %H:%M:%S'

def add_scrollable_to_pre(html_text):
    soup = BeautifulSoup(html_text, 'html.parser')
    pres = soup.select('.codehilite pre')
    for pre in pres:
        pre['class'] = 'pre-x-scrollable'
    return str(soup)

def add_bootstrap_table_style(html_text):
    soup = BeautifulSoup(html_text, 'html.parser')
    tables = soup.select('table')
    for table in tables:
        table['class'] = 'table table-striped'
    return str(soup)

def truncate_html(html, words):
    return str(BeautifulSoup(' '.join(html.split(' ')[:words]) + '...', "html.parser"))


class Post(dict):

    @property
    def rendered_content(self):
        self.render()
        return self['_rendered_content']

    @property
    def rendered_preview(self):
        self.render()
        return self['_rendered_preview']

    def render(self):
        if '_rendered_content' not in self or '_rendered_preview' not in self:
            rendered_content = markdown(self['content'], extensions=MD_EXTENSIONS, extension_configs=MD_EXT_CONFIGS)
            rendered_content = add_scrollable_to_pre(rendered_content)
            rendered_content = add_bootstrap_table_style(rendered_content)
            self['_rendered_content'] = rendered_content
            self['_rendered_preview'] = truncate_html(rendered_content, 50)

class Posts(object):

    FILE_EXTENSION = 'mdtxt'
    TIME_FMT = "%Y-%m-%dT%H:%M:%S"

    def __init__(self, folder):
        self.folder = folder
        self.posts = []
        self.years = []
        self.months = []
        for file in os.listdir(folder):
            if file.endswith("." + self.FILE_EXTENSION):
                try:
                    self._add_post(file)
                except Exception as e:
                    logger.warn('Could not add the post %s for the following reason:', file)
                    logger.warn(str(e))
        self.update_collections()

    def update_collections(self):
        self.posts.sort(key=lambda post: post['creation_date'], reverse=True)
        del self.years[:]
        del self.months[:]
        for post in self.posts:
            year = date(post['creation_date'].year, 1, 1)
            month = date(post['creation_date'].year, post['creation_date'].month, 1)
            if year not in self.years:
                self.years.append(year)
            if month not in self.months:
                self.months.append(month)
        self.years.sort(reverse=True)
        self.months.sort(reverse=True)

    def _add_post(self, filename):
        post = Post()
        filecontent = open(os.path.join(self.folder, filename), 'r').read()
        header, _, postcontent = filecontent.partition("\n\n### Content\n\n")
        # title
        title = re.search(r"^# (?P<result>.*)$", header, re.MULTILINE)
        title = title.group('result')
        # categories
        categories = re.search(r"^\* Categories: (?P<result>.*)$", header, re.MULTILINE)
        if categories: categories = categories.group('result').split(', ')
        else: categories = []
        # tags
        tags = re.search(r"^\* Tags: (?P<result>.*)$", header, re.MULTILINE)
        if tags: tags = tags.group('result').split(', ')
        else: tags = []
        # creation_date
        creation_date = re.search(r"^\* Creation Date: (?P<result>.*)$", header, re.MULTILINE)
        creation_date = datetime.strptime(creation_date.group('result'), TIME_FMT)
        # modification_date
        modification_date = re.search(r"^\* Modification Date: (?P<result>.*)$", header, re.MULTILINE)
        if modification_date: modification_date = datetime.strptime(modification_date.group('result'), TIME_FMT)
        else: modification_date = creation_date
        # slug
        slug = re.search(r"^\* Slug: (?P<result>.*)$", header, re.MULTILINE)
        if slug: slug = slug.group('result')
        else: slug = None
        # status
        status = re.search(r"^\* Status: (?P<result>.*)$", header, re.MULTILINE)
        if status: status = status.group('result')
        else: status = 'draft'
        # address (from creation_date and )
        if status in ('published', 'private'): address = '/{:04d}/{:02d}/{}'.format(creation_date.year, creation_date.month, slug)
        else: address = None
        # done
        post['file'] = filename
        post['title'] = title
        post['categories'] = categories
        post['tags'] = tags
        post['creation_date'] = creation_date
        post['year'] = creation_date.year
        post['month'] = creation_date.month
        post['modification_date'] = modification_date
        post['status'] = status
        post['address'] = address
        post['slug'] = slug
        post['content'] = postcontent
        post['filecontent'] = filecontent
        self.posts.append(post)

    def search_literally(self, search_phrase):
        search_phrase = search_phrase.lower()
        literal_results = []
        all_words_contained_results = []
        for post in self.posts:
            post_text = post['filecontent'].lower()
            if search_phrase in post_text:
                literal_results.append(post)
            elif all(word in post_text for word in search_phrase.split()):
                all_words_contained_results.append(post)
        return literal_results + all_words_contained_results

    @property
    def latest(self):
        newest_date = datetime(1000, 1, 1, 1, 1, 1)
        newest_post = None
        for post in self.posts:
            if post['creation_date'] > newest_date:
                newest_date = post['creation_date']
                newest_post = post
        return newest_post

    def keep_only(self, status_list):
        self.posts = [post for post in self.posts if post['status'] in status_list]
        self.update_collections()

    def keep_only_published(self):
        self.keep_only(['publish'])

    def total(self):
        return len(self.posts)

if __name__ == "__main__":
    import argparse, pprint, random
    parser = argparse.ArgumentParser(description='Testing the posts module')
    parser.add_argument('local_blog_folder', help='Folder containing the blog posts')
    args = parser.parse_args()

    posts = Posts(args.local_blog_folder)

    print("This directory contains {} blog posts".format(posts.total()))

    posts.keep_only_published()
    print("The latest 10 published posts:")
    for post in posts.posts[-10:]:
        print("Title: {title}, slug: {slug}, status: {status}".format(**post))

