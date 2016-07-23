import cgi
import datetime
import glob
import os
import re
import time
import itertools
from shutil import copyfile

import jinja2
import markdown
from slugify import slugify

from settings import config

tag_regex = re.compile(r'<[^<]+?>')
summary_regex = re.compile(r'^(.*?)<!-- more -->.*')
extension_regex = re.compile(r"\.[^.]*$")
trailing_html_regex = re.compile(r"(?<!\.html)$")

class ClassProperty(property):
    def __get__(self, instance, owner):
        return self.fget.__get__(None, owner)()

def clsprop(func):
    if not isinstance(func, (classmethod, staticmethod)):
        func = classmethod(func)
    return ClassProperty(func)

def issubpath(P, C):
    return os.path.abspath(C).startswith(
        os.path.abspath(
            os.path.join(
                P,
                '' #To gain trailing slash!
            )
        )
    )

def enhance_path(P, C):
    return os.path.abspath(os.path.join( P, C))\
            if not os.path.isabs(C)\
            and not issubpath(P, C)\
            else os.path.abspath(C)

def ensure_dir_exists(full_name):
    (path, ignore) = os.path.split(full_name)
    if not os.path.exists(path):
        os.makedirs(path)

def elm_of_lst_get(lst, ind):
    def func(key, alt='', as_list=False):
        if as_list:
            return lst.get(key, alt)
        return lst.get(key, [alt])[ind]
    return func

class WebObject(object):
    _objects=None
    export_setting='export_to'
    import_setting='template_dir'
    template_dir = config[import_setting]

    @clsprop
    def import_path(cls):
        return enhance_path(
            config['source'],
            config[cls.import_setting]
        )

    @clsprop
    def base_path(cls):
        return enhance_path(
            config['export_to'],
            config[cls.export_setting]
        )

    @clsprop
    def base_url(cls):
        return config["site"]["blog_url"]+os.path.relpath(
            cls.base_path,
            config['export_to']
        )

    # Use the full loader so we get an informative traceback from jinja
    # which includes the filename and line of the template.
    jinja2env = jinja2.Environment(
                loader=jinja2.FileSystemLoader(config["template_dir"])
            )

    def __init__(self, file):
        self.file = file
        self.template = WebObject.jinja2env.get_template(file)
        self.target_html = file.replace(
                self.import_path,
                self.base_path
            )

    @property
    def target_url(self):
        target = self.target_html
        if issubpath(self.base_path, self.target_html):
            target = os.path.relpath(
                self.target_html,
                self.base_path
            )
        return os.path.join(self.base_url, target)

    def _get_files(path):
        """Get names of files in path excluding the ignored ones."""
        source_files = set(itertools.chain.from_iterable(
                            map(
                                lambda include: set(glob.glob(os.path.join(path, include))),
                                config['select_files']
                            )
                        ))
        ignore_files = set(itertools.chain.from_iterable(
                            map(
                                lambda ignore: set(glob.glob(os.path.join(path, ignore))),
                                config['ignore_files']
                            )
                        ))
        return source_files - ignore_files

    @classmethod
    def collect_sources(cls):
        """Retrieve all sources within directory and return
        WebObject - instances"""
        if cls._objects == None:
            cls._objects = [
                cls(file)
                for file in cls._get_files(cls.import_path)
            ]
        return cls._objects

    #EXPECTS self.template TO BE FULLY FLEDGED TEMPLATE!
    #(self.file, self.template and self.layout are
    # ambiguous as possible template-names!)
    def build_object(self, **template_args):
        full_output = enhance_path(config['export_to'], self.target_html)
        ensure_dir_exists(full_output)
        with open(full_output, 'w') as f:
            f.write(self.template.render(**template_args))

class Article(WebObject):
    export_setting = 'post_to'
    import_setting = 'article_source'

    def link_article(linkname, article, **kwargs):
        if not isinstance(article, Article):
            pick = glob.glob(os.path.join(Article.import_path, "*%s*"%slugify(article, max_length=50)))
            if not len(pick) == 1:
                print("couldn't find unabiguose article with name "+article)
                print("(This can usually be fixed by adding the pub-date)")
                print("Aborting")
                exit(1)
            article = Article(pick[0])
        attrs = " ".join([key+"="+val for key, val in kwargs.items()])
        target_url = article.target_url
        return '<a%s href="%s">%s</a>'%(attrs, target_url, linkname)

    WebObject.jinja2env.filters["link_article"] = link_article

    def __init__(self, file):
        #sets two attributes, both overwritten later.
        #mainly for compatibility with future changes.
        super(Article, self).__init__('article.html')
        (self.path, filename) = os.path.split(file)
        self.html_filename = extension_regex.sub('.html', filename)

        md = markdown.Markdown(extensions=['meta'])
        with open(file) as f:
            self.html = md.convert(f.read())

        self.meta = md.Meta
        meta_get = elm_of_lst_get(self.meta, 0)
        self.published = meta_get('published', False)
        self.author = meta_get('author')
        self.title = cgi.escape(meta_get('title'))
        self.layout = trailing_html_regex.sub('.html', meta_get('layout', config['default_layout']))

        summary_match = summary_regex.match(self.html)
        summary = summary_match.group(0) if summary_match else self.html[0:200]
        self.summary = tag_regex.sub('', summary).replace('\n', ' ')

        self.datetime = datetime.datetime.strptime(
                self.meta['date'][0], #If there is no date, this should break dramatically!
                "%Y-%m-%d %H:%M"
            )
        #overwrite wrong target_html!
        self.target_html = os.path.join(
            Article.base_path,
            self.datetime.strftime("%Y-%m-%d-")\
            + slugify(self.title, max_length=20)+'.html'
        )
        self.date_txt = self.datetime.strftime(config['post_format'])
        self.date_rss = self.datetime.strftime(config['rss_format'])
        
    @classmethod
    def collect_sources(cls):
        """Get Article objects from the markdown files on disk"""
        articles = super(Article, cls).collect_sources()
        articles.sort(key=lambda k: k.datetime, reverse=True)
        return articles

    def build_object(self, **template_args):
        #RENDERING HAPPENS HERE!
        unrendered_article = WebObject.jinja2env.from_string(self.html)
        #template_args could be passed here?
        self.html = unrendered_article.render(**template_args)
        self.template = WebObject.jinja2env.get_template(self.layout)

        return super(Article, self).build_object(article=self, **template_args)

class Static(WebObject):
    export_setting = 'static_export'
    import_setting = 'static_source'

    static_groups = {"group_name":["list_all.css", "required_statics.js"]}

    ext_templates={
        '.js': '<script type="text/javascript" src="%s">',
        '.css': '<link rel="stylsheet" type="text/css" href="%s">'
    }

    def load_static(static_name):
        files = Static.static_groups.get(static_name, [static_name])
        return '\n'.join([
            Static.ext_templates[
                extension_regex.search(file).group()
            ]%Static(file).target_url\
            for file in files\
        ])

    WebObject.jinja2env.filters["static"] = load_static

    def __init__(self, file):
        self.file=file
        self.target_html=file

    def build_object(self, *args, **kargs):
        src = enhance_path(self.import_path, self.file)
        dst = src.replace(self.import_path, self.base_path)
        ensure_dir_exists(dst)
        copyfile(src, dst)

class Page(WebObject):
    import_setting = 'pages_dir'
    template_dir = config[import_setting]

    def link_page(linkname, page, **kwargs):
        if not isinstance(page, Page):
            pick = glob.glob(os.path.join(Page.import_path, "*%s*"%slugify(page, max_length=50)))
            if not len(pick) == 1:
                print("couldn't find unabiguose article with name "+article)
                print("(This can usually be fixed by adding the pub-date)")
                print("Aborting")
                exit(1)
            page = Page(pick[0])
        attrs = " ".join([key+"="+val for key, val in kwargs.items()])
        target_url = page.target_url
        return '<a%s href="%s">%s</a>'%(attrs, target_url, linkname)

    WebObject.jinja2env.filters["link_page"] = link_page

    def __init__(self, file):
        self.file=file
        with open(file) as f:
                self.html = f.read()

        match = trailing_html_regex.match(self.file)
        if match:
            self.published=True
            self.author=config["site"]["author"]
            self.layout=config["default_layout"]
            self.title=file.replace('.html', '').capitalize()
        else:
            md = markdown.Markdown(extensions=["meta"])
            self.html = md.convert(self.html)

            self.meta = md.Meta
            meta_get = elm_of_lst_get(self.meta, 0)
            self.published = meta_get('published', False)
            self.author = meta_get('author')
            self.title = cgi.escape(meta_get('title'))
            self.layout = trailing_html_regex.sub(
                '.html',
                meta_get('layout', config['default_layout'])
            )

        #THE FIRST REPLACE IS TOO STATIC! BETTER REGEX REQUIRED!
        self.target_html = file.replace(".markdown", ".html").replace(
                self.import_path,
                self.base_path
            )

    def build_object(self, **template_args):
        self.template = WebObject.jinja2env.from_string(self.html)
        return super(Page, self).build_object(page=self, **template_args)
