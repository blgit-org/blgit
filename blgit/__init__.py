import logging
from datetime import date, datetime, timezone
from importlib.resources import open_text
from pathlib import Path
from sqlite3 import Date

import cattrs
import typer
import yaml
from attrs import frozen
from cattr import structure, unstructure
from feedgen.feed import FeedGenerator
from frontmatter import Frontmatter as frontmatter
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from markdown import markdown
from rich import print
from rich.logging import RichHandler
from rich.table import Table

MD_EXTENSIONS = [
    'fenced_code',
    'tables',
    'footnotes',
    'toc',
    'admonition',]

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
    index_md = Path('index.md')

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
    def path_html(path_md: Path):
        return fs.docs / path_md.relative_to(fs.post).with_suffix('.html')


def res2str(name: str):
    with open_text('blgit', name) as f:
        return f.read()


@frozen
class FrontMatter:
    title: str
    description: str
    image: str
    favicon: str

    @classmethod
    def from_dict(cls, attrs: dict):
        return structure(attrs, cls)

    def as_dict(self):
        image = self.image
        image = fs.docs / image
        image = f'/{image.relative_to(fs.docs)}'

        return unstructure(self) | {'image': image}


@frozen
class IndexFrontMatter(FrontMatter):
    lang: str
    url: str
    date_format: str


@frozen
class PostFrontMatter(FrontMatter):
    author: str
    date: Date
    draft: bool


@frozen
class Index:
    fm: IndexFrontMatter
    body: str

    @classmethod
    def from_md(cls, path_md: Path = fs.index_md):
        md = frontmatter.read_file(path_md)

        return cls(
            fm=IndexFrontMatter.from_dict(md['attributes']),
            body=md['body'])


@frozen
class Post:
    fm: PostFrontMatter
    body: str

    path_html: Path
    url: str

    @classmethod
    def from_md(cls, path_md: Path):
        md = frontmatter.read_file(path_md)

        path_html = fs.path_html(path_md)

        url = path_html.relative_to(fs.docs)

        if url.name == 'index.html':
            url = url.parent

        return cls(
            fm=PostFrontMatter.from_dict(md['attributes']),
            body=md['body'],
            path_html=path_html,
            url=f'/{url}')


def related_dict(post: Post):
    return {'url': post.url} | post.fm.as_dict()


def read_posts():
    return sorted([
        Post.from_md(post)
        for post in fs.mds()],
        key=lambda p: p.fm.date)


def ensure_exists(path: Path, content: str):
    if path.exists():
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def feed(index: Index, posts: list[Post]):
    fg = FeedGenerator()
    fg.title(index.fm.title)
    fg.link(
        href=index.fm.url,
        rel='alternate')

    fg.description(index.fm.description)

    for post in posts:
        dt = datetime.combine(
            post.fm.date,
            datetime.min.time(),
            tzinfo=timezone.utc)

        fe = fg.add_entry()
        fe.title(post.fm.title)
        fe.description(post.fm.description)
        fe.published(dt)

        fe.link(
            href=f'{index.fm.url}{post.url}/',
            rel='alternate')

    return fg


def gen_index(env: Environment, posts: list[Post]):
    index_j2 = env.get_template('index.j2')

    index_md = Index.from_md()

    write(
        fs.index_html,
        index_j2.render(
            **index_md.fm.as_dict(),

            body=markdown(
                index_md.body,
                extensions=MD_EXTENSIONS),

            posts=[
                unstructure(post)
                for post in posts]))

    return index_md


def gen_posts(env: Environment, posts: list[Post], config: dict):
    post_j2 = env.get_template('post.j2')

    log.info('Generating posts:')

    table = Table(
        '',
        'date',
        'title',
        'author',
        'image')

    for i, post in enumerate(posts):
        n = len(posts)
        prev = posts[(i - 1 + n) % n]
        next = posts[(i + 1) % n]

        image = post.fm.image
        image = fs.docs / image
        color = 'green' if image.exists() else 'red'

        table.add_row(
            post.fm.favicon,
            post.fm.date.strftime(config['date_format']),
            post.fm.title,
            post.fm.author,
            f'[{color}]{image}[/{color}]')

        data = (config | post.fm.as_dict())

        write(
            post.path_html,
            post_j2.render(
                **data,

                path=post.path_html,

                body=markdown(
                    post.body,
                    extensions=MD_EXTENSIONS),

                related=[
                    related_dict(prev),
                    related_dict(next)]))

    print(table)


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

    gen_posts(env, posts, unstructure(index_md.fm))

    log.info(f'Generating {fs.rss_xml}')
    feed(index_md, posts).rss_file(fs.rss_xml, pretty=True)

    print()
    print('You can now run:')
    print('[bold]npx serve docs[/bold]')


NEW_POST_FM = PostFrontMatter(
    author='author',
    date=date.today(),
    description='description',
    favicon='🏖️',
    image='image.jpg',
    title='title',
    draft=True)


@app.command()
def new(name: str):
    post = fs.post / name / 'index.md'

    if post.exists():
        print(f'Post [bold]{name}[/bold] already exists')
        raise typer.Exit()

    post.parent.mkdir(parents=True, exist_ok=True)

    with open(post, 'w') as f:
        print('---', file=f)

        yaml.dump(
            unstructure(NEW_POST_FM),
            stream=f,
            allow_unicode=True)

        print('---', file=f)

    log.info(f'Created {post}')


@app.command()
def fix():
    for post in fs.mds():
        md = frontmatter.read_file(post)

        with open(post, 'w') as f:
            print('---', file=f)

            yaml.dump(
                unstructure(NEW_POST_FM) | md['attributes'],
                stream=f,
                allow_unicode=True)

            print('---', file=f)
            print(file=f)

            f.write(md['body'])

        log.info(f'Fixed {post}')
