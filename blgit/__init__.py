import logging
from datetime import date, datetime, timezone
from importlib.resources import open_text
from pathlib import Path
from sqlite3 import Date

import cattrs
import typer
from attr import dataclass
from cattr import structure, unstructure
from feedgen.feed import FeedGenerator
from frontmatter import Frontmatter
from jinja2 import Environment, FileSystemLoader
from markdown import markdown
from rich import print
from rich.logging import RichHandler

MD_EXTENSIONS = ['fenced_code', 'tables', 'footnotes']

logging.basicConfig(
    level=logging.INFO,
    handlers=[RichHandler()],
    datefmt='%H:%M:%S',
    format='%(message)s')

log = logging.getLogger()


app = typer.Typer()

cattrs.register_structure_hook(
    Date,
    lambda d, t: d)


class fs:
    template = Path('template')
    html_j2 = template / 'html.j2'
    index_j2 = template / 'index.j2'
    post_j2 = template / 'post.j2'

    docs = Path('docs')
    index_html = docs / 'index.html'
    index_css = docs / 'index.css'
    rss_xml = docs / 'rss.xml'


def res2str(name: str):
    with open_text('blgit', name) as f:
        return f.read()


@dataclass
class info:
    title: str
    description: str
    image: str
    favicon: str


@dataclass
class index_info(info):
    url: str
    lang: str
    date_format: str


@dataclass
class post_info(info):
    date: Date
    author: str


@dataclass(frozen=True, kw_only=True)
class index:
    info: index_info
    body: str


@dataclass(frozen=True, kw_only=True)
class post:
    info: post_info
    body: str
    path: str


def read_index():
    fm = Frontmatter.read_file('index.md')

    return index(
        info=structure(fm['attributes'], index_info),
        body=fm['body'])


def read_post(path: Path):
    fm = Frontmatter.read_file(path)

    info = structure(fm['attributes'], post_info)

    return post(
        info=info,
        body=fm['body'],
        path=path.with_suffix('.html').name)


def read_posts():
    return sorted([
        read_post(post)
        for post in Path('post').glob('*.md')],
        key=lambda p: p.info.date)


def ensure_exists(path: Path, content: str):
    if path.exists():
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def feed(index: index_info, posts: list[post]):
    fg = FeedGenerator()
    fg.title(index.title)
    fg.link(href=index.url, rel='alternate')
    fg.description(index.description)

    for post in posts:
        dt = datetime.combine(
            post.info.date,
            datetime.min.time(),
            tzinfo=timezone.utc)

        fe = fg.add_entry()
        fe.title(post.info.title)
        fe.link(href=f'{index.url}/{post.path}', rel='alternate')
        fe.description(post.info.description)
        fe.published(dt)

    return fg


def gen_index(env: Environment, posts: list[post]):
    index_j2 = env.get_template('index.j2')

    index_md = read_index()

    write(
        fs.index_html,
        index_j2.render(
            **unstructure(index_md.info),

            body=markdown(
                index_md.body,
                extensions=MD_EXTENSIONS),

            posts=[
                unstructure(post)
                for post in posts]))

    return index_md


def gen_posts(env: Environment, posts: list[post], config: dict):
    post_j2 = env.get_template('post.j2')

    for i, post in enumerate(posts):
        n = len(posts)
        prev = posts[(i - 1 + n) % n]
        next = posts[(i + 1) % n]

        out = fs.docs / post.path
        log.info(f'Generating {out}')

        data = (config | unstructure(post.info))

        write(
            out,
            post_j2.render(
                **data,

                path=post.path,

                body=markdown(
                    post.body,
                    extensions=MD_EXTENSIONS),

                related=[prev, next]))


@app.command()
def build():

    ensure_exists(fs.html_j2, res2str('html.j2'))
    ensure_exists(fs.index_j2, res2str('index.j2'))
    ensure_exists(fs.post_j2, res2str('post.j2'))
    ensure_exists(fs.index_css, res2str('index.css'))

    env = Environment(loader=FileSystemLoader(fs.template))
    posts = read_posts()

    log.info(f'Generating {fs.index_html}')
    index_md = gen_index(env, posts)

    gen_posts(env, posts, unstructure(index_md.info))

    log.info(f'Generating {fs.rss_xml}')
    feed(index_md.info, posts).rss_file(fs.rss_xml, pretty=True)

    print()
    print('You can now run:')
    print('[bold]npx serve docs[/bold]')


@app.command()
def new_post(name: str):
    post = Path('post') / f'{name}.md'
    if post.exists():
        print(f'Post [bold]{name}[/bold] already exists')
        raise typer.Exit()

    write(
        post,
        res2str('new_post.md').replace(
            '$date$',
            date.today().strftime('%Y-%m-%d')))
