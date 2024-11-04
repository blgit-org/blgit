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
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from markdown import markdown
from rich import print
from rich.logging import RichHandler

MD_EXTENSIONS = [
    'fenced_code',
    'tables',
    'footnotes',
    'toc']

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

    post = Path('post')

    docs = Path('docs')
    index_html = docs / 'index.html'
    index_css = docs / 'index.css'
    rss_xml = docs / 'rss.xml'

    @staticmethod
    def mds():
        return fs.post.rglob('*.md')

    @staticmethod
    def target(post_md: Path):
        return fs.docs / post_md.relative_to(fs.post).with_suffix('.html')


def res2str(name: str):
    with open_text('blgit', name) as f:
        return f.read()


@dataclass
class Info:
    title: str
    description: str
    image: str
    favicon: str


@dataclass
class IndexInfo(Info):
    url: str
    lang: str
    date_format: str


@dataclass
class PostInfo(Info):
    date: Date
    author: str


@dataclass(frozen=True, kw_only=True)
class Index:
    info: IndexInfo
    body: str


@dataclass(frozen=True, kw_only=True)
class Post:
    info: PostInfo
    body: str
    target: Path
    url: str

    @classmethod
    def from_md(cls, path_md: Path):
        fm = Frontmatter.read_file(path_md)

        target = fs.target(path_md)
        url = target.relative_to(fs.docs)

        info = structure(fm['attributes'], PostInfo)
        image = Path(info.image)

        if not image.is_absolute():
            info.image = f'/{url.parent / image}'

        if url.name == 'index.html':
            url = url.parent

        return cls(
            info=info,
            body=fm['body'],
            target=fs.target(path_md),
            url=f'/{url}')


def read_index():
    fm = Frontmatter.read_file('index.md')

    return Index(
        info=structure(fm['attributes'], IndexInfo),
        body=fm['body'])


def read_posts():
    return sorted([
        Post.from_md(post)
        for post in fs.mds()],
        key=lambda p: p.info.date)


def ensure_exists(path: Path, content: str):
    if path.exists():
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def feed(index: IndexInfo, posts: list[Post]):
    fg = FeedGenerator()
    fg.title(index.title)
    fg.link(
        href=index.url,
        rel='alternate')

    fg.description(index.description)

    for post in posts:
        dt = datetime.combine(
            post.info.date,
            datetime.min.time(),
            tzinfo=timezone.utc)

        fe = fg.add_entry()
        fe.title(post.info.title)
        fe.description(post.info.description)
        fe.published(dt)

        fe.link(
            href=f'{index.url}{post.url}/',
            rel='alternate')

    return fg


def gen_index(env: Environment, posts: list[Post]):
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


def gen_posts(env: Environment, posts: list[Post], config: dict):
    post_j2 = env.get_template('post.j2')

    for i, post in enumerate(posts):
        n = len(posts)
        prev = posts[(i - 1 + n) % n]
        next = posts[(i + 1) % n]

        log.info(f'Generating {post.info.favicon} {post.target}')

        data = (config | unstructure(post.info))

        write(
            post.target,
            post_j2.render(
                **data,

                path=post.target,

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

    env = Environment(
        undefined=StrictUndefined,
        loader=FileSystemLoader(fs.template))

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
def new(name: str):
    post = fs.post / name / 'index.md'

    if post.exists():
        print(f'Post [bold]{name}[/bold] already exists')
        raise typer.Exit()

    post.parent.mkdir(parents=True, exist_ok=True)

    write(
        post,
        res2str('new_post.md').replace(
            '$date$',
            date.today().strftime('%Y-%m-%d')))

    log.info(f'Created {post}')
