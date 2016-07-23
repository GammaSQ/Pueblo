config = {
    'source': '.',
    'article_source': './articles',
    'static_source': './static',
    'static_export' : './static',
    'export_to': './site',
    'post_to':'posts',
    'template_dir': './templates',
    'pages_dir': './pages',
    'ignore_files': ['ignore_example.markdown'],
    'select_files': ["*.markdown", "*.md", "*.css", '*.html','*.xml'], #Don't remove *.markdown ! (Could cause apocalypse.)
    'post_format': '%d. %B. %Y',
    'rss_format': '%a, %d %b %Y 06:%M:%S +0000',
    'default_layout': 'article.html',
    'site': {
        'name': 'Site Name',
        'description': 'Your site description',
        'url': 'http://example.com',
        'blog_url': 'file:///home/user/Documents/projects/Pueblo/site/',
        'author': 'Your name here',
    },
}
