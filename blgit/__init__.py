from datetime import date
from importlib.resources import open_text
from pathlib import Path
from sqlite3 import Date
from typing import Iterable

import cattrs
import typer
from attr import dataclass
from cattr import structure, unstructure
from feedgen.feed import FeedGenerator
from frontmatter import Frontmatter
from jinja2 import Environment, FileSystemLoader
from markdown import markdown
from rich import print

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
    date_str: str | None = None
    path: str | None = None


@dataclass(frozen=True, kw_only=True)
class index_md:
    info: index_info
    body: str


@dataclass(frozen=True, kw_only=True)
class post_md:
    info: post_info
    body: str


def read_index():
    fm = Frontmatter.read_file('index.md')

    return index_md(
        info=structure(fm['attributes'], index_info),
        body=fm['body'])


def read_post(path: Path):
    fm = Frontmatter.read_file(path)

    info = structure(fm['attributes'], post_info)
    info.path = path.with_suffix('.html').name

    return post_md(
        info=info,
        body=fm['body'])


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


def format_date(posts: Iterable[post_md], fmt: str):
    for post in posts:
        post.info.date_str = post.info.date.strftime(fmt)


def feed(index: index_info, posts: list[post_info]):
    fg = FeedGenerator()
    fg.title(index.title)
    fg.link(href=index.url, rel='alternate')
    fg.description(index.description)

    for post in posts:
        fe = fg.add_entry()
        fe.title(post.title)
        fe.link(href=f'{index.url}/{post.path}', rel='alternate')
        fe.description(post.description)
        fe.published(post.date)

    return fg


@app.command()
def build():
    extensions = ['fenced_code']

    ensure_exists(fs.html_j2, res2str('html.j2'))
    ensure_exists(fs.index_j2, res2str('index.j2'))
    ensure_exists(fs.post_j2, res2str('post.j2'))
    ensure_exists(fs.index_css, res2str('index.css'))

    env = Environment(loader=FileSystemLoader(fs.template))
    index_j2 = env.get_template('index.j2')

    index_md = read_index()

    date_format = index_md.info.date_format

    posts = read_posts()

    format_date(
        posts,
        fmt=date_format)

    print('Generating [bold]index.html[/bold]')

    write(
        fs.index_html,
        index_j2.render(
            **unstructure(index_md.info),

            body=markdown(
                index_md.body,
                extensions=extensions),

            posts=[
                unstructure(post.info)
                for post in posts]))

    post_j2 = env.get_template('post.j2')

    for i, post in enumerate(posts):
        n = len(posts)
        prev = posts[(i - 1 + n) % n]
        next = posts[(i + 1) % n]

        assert post.info.path is not None

        out = fs.docs / post.info.path
        print(f'Generating [bold]{out}[/bold]')

        write(
            out,
            post_j2.render(
                **unstructure(post.info),

                lang=index_md.info.lang,

                body=markdown(
                    post.body,
                    extensions=extensions),

                related=[
                    prev.info,
                    next.info]))


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
