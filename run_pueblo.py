import os
import datetime
from argparse import ArgumentParser
from slugify import slugify

from settings import config
import pueblo
from pueblo import Page, Static, Article, WebObject

parser = ArgumentParser(
    description="This is the main Control for your Pure Blog."
)

parser.add_argument('command', metavar='CMD',
                    choices=["new_post", "build"],
                    help="command to execute"
)

args = parser.parse_args()
command = args.command

if command == 'build':
    site = config['site']

    articles = Article.collect_sources()

    pages = Page.collect_sources()
    site["pages"] = pages

    for page in pages:
        page.build_object(site=site, articles=articles)

    for article in articles:
        article.build_object(site=site)

    statics = Static.collect_sources()

    for stat in statics:
        stat.build_object(site=site)

elif command == 'new_post':
    basic_settings = {}
    basic_settings['title']=input("What's this posts title? ")
    basic_settings['layout']=input("Custom layout? (blank for default) ")
    if basic_settings['layout']:
        print("(Make sure a template of equal name exists!)")
    else:
        basic_settings['layout'] = config['default_layout']

    published = None
    for i in range(4):
        pub=input("Set post.published = True? [Y/n] ")
        if not pub or pub.lower() in ['y', 'yes']:
            published = True
            break
        elif pub.lower() in ['n', 'no']:
            published = False
            break
        else:
            if i > 2:
                print("Aborting, no files written")
                exit(1)
            print("Didn't understand, please try again!")
    now = datetime.datetime.now()
    basic_settings['published'] = published

    basic_settings['date'] = now.strftime("%Y-%m-%d %H:%M")

    basic_head = "---\n%s\n---"%'\n'.join(['%s: %s'%item for item in basic_settings.items()])

    filename = basic_settings['date'].format("%Y-%m-%d-")\
        + slugify(basic_settings['title'], max_length=50)\
        + config['select_files'][0][1:] #jump the *!
    file = os.path.join(pueblo.Article.import_path, filename)
    with open(file, 'w') as f:
        f.write(basic_head)
