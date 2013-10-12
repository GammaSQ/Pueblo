#!/usr/bin/env python

import pueblo

PARAMS = {
    'SOURCE': './articles',
    'PUBLISH_TO': './site',
    'TEMPLATE_DIR': './templates',
    'IGNORE_FILES': ['ignore_example.markdown'],
}

print "Content-type: text/html\n\n"

site = pueblo.Site(PARAMS)
site.build_site()

print """<html>
    <head><title>Site Rebuilt</title></head>
    <body>
        <h1>Site Rebuilt</h1>
    </body>
</html>"""
