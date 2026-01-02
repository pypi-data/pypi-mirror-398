# mdit-py-figure

[![PyPI version](https://img.shields.io/pypi/v/mdit-py-figure.svg)](https://pypi.org/project/mdit-py-figure/)
[![Python versions](https://img.shields.io/pypi/pyversions/mdit-py-figure.svg)](https://pypi.org/project/mdit-py-figure/)
[![License](https://img.shields.io/pypi/l/mdit-py-figure.svg)](https://github.com/mangoumbrella/mdit-py-figure/blob/main/LICENSE)

[mdit-py-figure](https://github.com/mangoumbrella/mdit-py-figure) is a
[markdown-it-py](https://github.com/executablebooks/markdown-it-py)
plugin to parse markdown paragraphs that start with an image into HTML
`<figure>` elements. One nice thing is it doesn't use any new markdown
syntaxes.

Example markdown source:

```md
![Picture of Oscar.](/path/to/cat.jpg)
Awesome caption about **Oscar** the kitty.
```

Render result:

```html
<figure>
<img src="/path/to/cat.jpg" alt="Picture of Oscar." />
<figcaption>Awesome caption about <strong>Oscar</strong> the kitty.</figcaption>
</figure>
```

Multiple images are supported:

```md
![Picture of Oscar.](/path/to/cat1.jpg)
![Picture of Luna.](/path/to/cat2.jpg)
Awesome captions about the **kitties**.
```

```html
<figure>
<img src="/path/to/cat1.jpg" alt="Picture of Oscar.">
<img src="/path/to/cat2.jpg" alt="Picture of Luna.">
<figcaption>Awesome captions about the <strong>kitties</strong>.</figcaption>
</figure>
```

# Why?

Using dedicated `<figure>` and `<figcaption>` elements makes styling images
with descriptions much easier.
[Here](https://mangobaby.app/parenting-tips/how-to-burp-a-newborn) is an
example:

![Example of an HTML figure with figcaption.](/assets/example.png)

I hear they are also good for SEO.

# Installation

```
pip install mdit-py-figure
```

Or with uv:

```
uv add mdit-py-figure
```

# Usage

```python
from markdown_it import MarkdownIt
from mdit_py_figure import figure_plugin

md = MarkdownIt().use(figure_plugin)

source = """
![Picture of Oscar.](/path/to/cat.jpg)
Awesome caption about **Oscar** the kitty.
"""

html = md.render(source)
print(html)
```

## Option to add link to the image

Example:

```python
md = MarkdownIt().use(figure_plugin, image_link=True)
```

Render result:

```html
<figure>
<a href="/path/to/cat.jpg">
<img src="/path/to/cat.jpg" alt="Picture of Oscar." />
</a>
<figcaption>Awesome caption about <strong>Oscar</strong> the kitty.</figcaption>
</figure>
```

See [`tests/test_figure.py`](/tests/test_figure.py) for more examples.

## Option to skip images without captions

Example:

```python
md = MarkdownIt().use(figure_plugin, skip_no_caption=True)
```

In case a link to an image doesn't have a caption (a line of text following it without any linebreaks in between), it won't be wrapped in a `<figure>`.

See `test_skip_no_caption_option()` in [`tests/test_figure.py`](/tests/test_figure.py) for an example.

# Changelog

## v1.0.0 (2025-12-27)

* Initial release - Python port of [goldmark-figure](https://github.com/mangoumbrella/goldmark-figure)

# LICENSE

Apache-2.0
