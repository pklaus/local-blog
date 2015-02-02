#!/usr/bin/env python

import os
from datetime import datetime, date

class Posts(object):

    FILE_EXTENSION = 'mdtxt'
    TIME_FMT = "%Y-%m-%dT%H:%M:%S"

    def __init__(self, folder, baselink = 'http://yourblog.com'):
        self.folder = folder
        self.posts = []
        self.years = []
        self.months = []
        self.baselink = baselink
        for file in os.listdir(folder):
            if file.endswith("." + self.FILE_EXTENSION):
                self._add_post(file)
        self.update_collections()

    def update_collections(self):
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

    def _add_post(self, file):
        post = dict()
        filecontent = open(os.path.join(self.folder, file), 'r').read()
        parts = filecontent.split("\n\n### Content\n\n")
        header = parts[0]
        postcontent = parts[1]
        header = header.split("\n")
        assert header[0].startswith('# ')
        title = header[0][2:]
        assert header[2].startswith('* Categories: ')
        categories = header[2][14:].split(', ')
        if categories == ['']: categories = []
        assert header[3].startswith('* Tags: ')
        tags = header[3][8:].split(', ')
        if tags == ['']: tags = []
        assert header[4].startswith('* Creation Date: ')
        creation_date = datetime.strptime(header[4][17:], self.TIME_FMT)
        assert header[5].startswith('* Modification Date: ')
        modification_date = datetime.strptime(header[5][21:], self.TIME_FMT)
        assert header[6].startswith('* Link: <')
        link = header[6][9:-1]
        address = link.replace(self.baselink, '')
        if address.startswith('/?'): address = None
        slug = None
        if address: slug = address.split('/')[3]
        status = None
        if file.startswith('p_') or file.startswith('publish_'):
            status = 'publish'
        if file.startswith('pr_') or file.startswith('private_'):
            status = 'private'
        if file.startswith('d_') or file.startswith('draft_'):
            status = 'draft'
        #import pdb; pdb.set_trace()
        post['file'] = file
        post['title'] = title
        post['categories'] = categories
        post['tags'] = tags
        post['creation_date'] = creation_date
        post['year'] = creation_date.year
        post['month'] = creation_date.month
        post['modification_date'] = modification_date
        post['link'] = link
        post['status'] = status
        post['address'] = address
        post['slug'] = slug
        post['content'] = postcontent
        post['filecontent'] = filecontent
        self.posts.append(post)

    def search_literally(self, search_phrase):
        results = []
        for post in self.posts:
            if search_phrase in post['filecontent']:
                results.append(post)
        return results

    @property
    def latest(self):
        newest_date = datetime(1000, 1, 1, 1, 1, 1)
        newest_post = None
        for post in self.posts:
            if post['creation_date'] > newest_date:
                newest_date = post['creation_date']
                newest_post = post
        return newest_post

    def published(self):
        return [post for post in self.posts if post['status'] == 'publish']

    def total(self):
        return len(self.posts)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Testing the posts module')
    parser.add_argument('local_blog_folder', help='Folder containing the blog posts')
    parser.add_argument('--baselink', '-b', help='Baselink of your blog, like http://philipp.wordpress.com')
    args = parser.parse_args()

    if args.baselink:
        posts = Posts(args.local_blog_folder, args.baselink)
    else:
        posts = Posts(args.local_blog_folder)
    print("This directory contains {} blog posts".format(posts.total()))
    print("The first 10 published posts:")
    for post in posts.published()[:10]:
        print(post['title'])
        print(post['slug'])

