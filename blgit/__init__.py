from dataclasses import dataclass
from importlib.resources import open_text
from pathlib import Path

from frontmatter import Frontmatter
from jinja2 import Template
from markdown import markdown


def load(name: str):
    with open_text('blgit', name) as f:
        return f.read()


@dataclass(frozen=True, kw_only=True)
class md:
    attrs: dict
    body: str


def read_md(path: Path):
    fm = Frontmatter.read_file(path)

    return md(
        attrs=fm['attributes'],
        body=fm['body'])


if __name__ == '__main__':
    temp = Template(load('index.j2'))
    post = read_md(Path('index.md'))

    output = temp.render(
        body=markdown(post.body),
        **post.attrs)

    print(output)
