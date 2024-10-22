import datetime
from dataclasses import dataclass
from importlib.resources import open_text
from pathlib import Path

from dateutil.parser import parse
from frontmatter import Frontmatter
from jinja2 import Environment, FileSystemLoader
from markdown import markdown


class fs:
    template = Path('template')
    html_j2 = template / 'html.j2'
    index_j2 = template / 'index.j2'
    post_j2 = template / 'post.j2'

    docs = Path('docs')
    index_html = docs / 'index.html'


def res2str(name: str):
    with open_text('blgit', name) as f:
        return f.read()


@dataclass(frozen=True, kw_only=True)
class md:
    attrs: dict
    body: str


def read_md(path: Path, date_format: str):
    fm = Frontmatter.read_file(path)
    attrs = fm['attributes']

    if 'date' not in attrs:
        attrs['date'] = datetime.date.today().strftime(date_format)

    print(attrs)

    date = parse(attrs['date'])
    attrs['date_format'] = attrs.get('date_format', date_format)
    attrs['date'] = date.strftime(date_format)

    attrs['path'] = path.with_suffix('.html').name

    return md(
        attrs=attrs,
        body=fm['body'])


def load_posts(date_format: str = '%d/%m/%Y'):
    posts = [
        read_md(post, date_format)
        for post in Path('post').glob('*.md')]

    return sorted(
        posts,
        key=lambda post: post.attrs['date'])


def ensure_exists(path: Path, content: str):
    if path.exists():
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def build():
    ensure_exists(fs.html_j2, res2str('html.j2'))
    ensure_exists(fs.index_j2, res2str('index.j2'))
    ensure_exists(fs.post_j2, res2str('post.j2'))

    env = Environment(loader=FileSystemLoader(fs.template))

    index_md = read_md(Path('index.md'))
    date_format = index_md.attrs.get('date_format', '%Y-%m-%d')

    posts = load_posts()

    index_j2 = env.get_template('index.j2')

    extensions = ['fenced_code']

    output = index_j2.render(
        body=markdown(
            index_md.body,
            extensions=extensions),
        **index_md.attrs,
        posts=[post.attrs for post in posts])

    write(fs.index_html, output)

    post_j2 = env.get_template('post.j2')
    for post in posts:
        output = post_j2.render(
            body=markdown(post.body),
            **post.attrs)

        # print(output)


if __name__ == '__main__':
    build()
    print('Done')
