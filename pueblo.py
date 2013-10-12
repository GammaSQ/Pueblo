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
        self.html_filename = os.path.basename(file).rsplit('.', 1)[0]
        md = markdown.Markdown(extensions=['meta'])
        with open(file) as f:
            self.html = md.convert(f.read())
            print self.html
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

    def __init__(self, params):
        self.template_dir = params['TEMPLATE_DIR']
        self.src_dir = params['SOURCE']
        self.dest_dir = params['PUBLISH_TO']
        self.ignore_files = params['IGNORE_FILES']
        self.pagebuild_delta = params['PAGEBUILD_DELTA']
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
        articles = []
        for file in self.get_files():
            articles.append(Article(file))
        articles.sort(key=lambda k: k.datetime, reverse=True)
        return articles

    def build_from_template(self, data, template, output_file):
        template = self.templates.get_template(template)
        with open(os.path.join(self.dest_dir, output_file), 'w') as i:
            i.write(template.render(data=data))

    def build_site(self):
        articles = self.load_articles()

        for article in articles:
            output = article.html_filename
            self.build_from_template(article, 'article_template.html', output)

        pages_to_build = (
            ('index_template.html', 'index.html'),
            ('archive_template.html', 'archive.html'),
            ('rss_template.xml', 'index.xml'))

        for template, output in pages_to_build:
            self.build_from_template(articles, template, output)
