#!/usr/bin/env python

import pueblo

params = {
    'source': './articles',
    'publish_to': './site',
    'template_dir': './templates',
    'ignore_files': ['ignore_example.markdown'],
    'site': {
        'title': 'Your site description',
        'url': 'http://yoursite.com',
        'blog_url': 'http://yoursite.com/blog/',
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
