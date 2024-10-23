from dataclasses import dataclass
from importlib.resources import open_text
from pathlib import Path

import typer
from dateutil.parser import parse
from frontmatter import Frontmatter
from jinja2 import Environment, FileSystemLoader
from markdown import markdown
from rich import print

app = typer.Typer()


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


@dataclass(frozen=True, kw_only=True)
class md:
    attrs: dict
    body: str


def read_md(path: Path):
    fm = Frontmatter.read_file(path)

    attrs = fm['attributes']
    attrs['path'] = path.with_suffix('.html').name

    return md(
        attrs=attrs,
        body=fm['body'])


def load_posts():
    posts = [
        read_md(post)
        for post in Path('post').glob('*.md')]

    return sorted(
        posts,
        key=lambda p: parse(p.attrs['date']))


def ensure_exists(path: Path, content: str):
    if path.exists():
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def format_date(*mds: md, fmt: str):
    for m in mds:
        if 'date' not in m.attrs:
            continue

        m.attrs['date'] = parse(m.attrs['date']).strftime(fmt)


@app.command()
def build():
    extensions = ['fenced_code']

    ensure_exists(fs.html_j2, res2str('html.j2'))
    ensure_exists(fs.index_j2, res2str('index.j2'))
    ensure_exists(fs.post_j2, res2str('post.j2'))
    ensure_exists(fs.index_css, res2str('index.css'))

    env = Environment(loader=FileSystemLoader(fs.template))
    index_j2 = env.get_template('index.j2')

    index_md = read_md(Path('index.md'))
    config = index_md.attrs

    date_format = config.get('date_format', '%d/%m/%Y')

    posts = load_posts()

    format_date(
        *posts,
        fmt=date_format)

    print('Generating [bold]index.html[/bold]')

    write(
        fs.index_html,
        index_j2.render(
            body=markdown(
                index_md.body,
                extensions=extensions),
            **index_md.attrs,
            posts=[post.attrs for post in posts]))

    post_j2 = env.get_template('post.j2')
    for i, post in enumerate(posts):
        n = len(posts)
        prev = posts[(i - 1 + n) % n]
        next = posts[(i + 1) % n]

        out = fs.docs / post.attrs['path']
        print(f'Generating [bold]{out}[/bold]')

        write(
            out,
            post_j2.render(
                body=markdown(post.body, extensions=extensions),
                **{**index_md.attrs, **post.attrs},
                related=[prev.attrs, next.attrs]))
