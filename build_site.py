#!/usr/bin/env python

import pueblo

params = {
    'source': './articles',
    'publish_to': './site',
    'template_dir': './templates',
    'ignore_files': ['ignore_example.markdown'],
    'site': {
        'name': 'Site Name',
        'description': 'Your site description',
        'url': 'http://example.com',
        'blog_url': 'http://example.com/blog',
        'author': 'Your name here',
    },
}

print "Content-type: text/html\n\n"

site = pueblo.Site(params)
site.build_site()

print """<html>
    <head><title>Site Rebuilt</title></head>
    <body>
        <h1>Site Rebuilt</h1>
    </body>
</html>"""
