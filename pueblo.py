import cgi
import datetime
import glob
import os
import re
import time

import jinja2
import markdown


class Article(object):
    def __init__(self, file):
        self.html_filename = os.path.basename(file).replace(
            '.markdown', '.html')
        md = markdown.Markdown(extensions=['meta'])
        with open(file) as f:
            self.html = md.convert(f.read())
        self.meta = md.Meta
        self.title = cgi.escape(self.meta['title'][0])
        self.date_txt = self.meta['date'][0]
        self.author = self.meta['author'][0]
        self.datetime = datetime.datetime.strptime(self.date_txt, '%d %B %Y')
        self.summary = re.sub(
            '<[^<]+?>', '', self.html)[0:200].replace('\n', ' ')
        date = time.strptime(self.date_txt, '%d %B %Y')
        self.date_rss = time.strftime('%a, %d %b %Y 06:%M:%S +0000', date)


class Site(object):

    def __init__(self, config):
        self.dest_dir = config['publish_to']
        self.ignore_files = config['ignore_files']
        self.site = config['site']
        self.src_dir = config['source']
        self.template_dir = config['template_dir']
        # Use the full loader so we get an informative traceback from jinja
        # which includes the filename and line of the template.
        self.templates = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.template_dir))

    def get_files(self):
        """Get filenames of articles excluding the ignored ones."""
        textfiles = set(glob.glob(os.path.join(self.src_dir, '*.markdown')))
        ignore_files = set(os.path.join(self.src_dir, ignore)
                           for ignore in self.ignore_files)
        return textfiles - ignore_files

    def load_articles(self):
        """Get Article objects from the markdown files on disk"""
        articles = []
        for file in self.get_files():
            articles.append(Article(file))
        articles.sort(key=lambda k: k.datetime, reverse=True)
        return articles

    def build_from_template(self, template, output_file, **template_args):
        template = self.templates.get_template(template)
        with open(os.path.join(self.dest_dir, output_file), 'w') as i:
            i.write(template.render(site=self.site, **template_args))

    def build_site(self):
        articles = self.load_articles()

        for article in articles:
            self.build_from_template('article.html',
                                     article.html_filename,
                                     article=article)

        pages_to_build = ('index.html', 'archive.html', 'rss.xml')

        for template in pages_to_build:
            self.build_from_template(template, template, articles=articles)
