"""Tests for figure plugin."""

from markdown_it import MarkdownIt

from mdit_py_figure import figure_plugin


def test_single_image_with_caption():
    """Test basic figure with single image and caption."""
    md = MarkdownIt().use(figure_plugin)
    html = md.render("![Picture of Oscar.](/path/to/cat.jpg)\nAwesome caption.")

    assert html == """\
<figure>
<img src="/path/to/cat.jpg" alt="Picture of Oscar." />
<figcaption><p>Awesome caption.</p></figcaption>
</figure>
"""


def test_single_image_with_caption_and_bold():
    """Test figure with caption containing markdown formatting."""
    md = MarkdownIt().use(figure_plugin)
    html = md.render(
        "![Picture of Oscar.](/path/to/cat.jpg)\nAwesome caption about **Oscar** the kitty."
    )

    assert html == """\
<figure>
<img src="/path/to/cat.jpg" alt="Picture of Oscar." />
<figcaption><p>Awesome caption about <strong>Oscar</strong> the kitty.</p></figcaption>
</figure>
"""


def test_multiple_images_with_caption():
    """Test figure with multiple images and caption."""
    md = MarkdownIt().use(figure_plugin)
    html = md.render(
        "![Picture of Oscar.](/path/to/cat1.jpg)\n"
        "![Picture of Luna.](/path/to/cat2.jpg)\n"
        "![Picture of Oreo.](/path/to/cat3.jpg)\n"
        "Awesome captions about the **kitties**."
    )

    assert html == """\
<figure>
<img src="/path/to/cat1.jpg" alt="Picture of Oscar." />
<img src="/path/to/cat2.jpg" alt="Picture of Luna." />
<img src="/path/to/cat3.jpg" alt="Picture of Oreo." />
<figcaption><p>Awesome captions about the <strong>kitties</strong>.</p></figcaption>
</figure>
"""


def test_single_image_no_caption():
    """Test image without caption (default: still transforms)."""
    md = MarkdownIt().use(figure_plugin)
    html = md.render("![Alt text](https://example.com/image.jpg)")

    assert html == """\
<figure>
<img src="https://example.com/image.jpg" alt="Alt text" /></figure>
"""


def test_skip_no_caption_option():
    """Test skip_no_caption option."""
    md = MarkdownIt().use(figure_plugin, skip_no_caption=True)
    html = md.render("![Alt text](https://example.com/image.jpg)")

    # Should NOT be transformed to figure
    assert html == """\
<p><img src="https://example.com/image.jpg" alt="Alt text" /></p>
"""


def test_skip_no_caption_with_caption():
    """Test skip_no_caption option with caption present."""
    md = MarkdownIt().use(figure_plugin, skip_no_caption=True)
    html = md.render("![Alt](img.jpg)\nCaption here")

    # Should be transformed since caption exists
    assert html == """\
<figure>
<img src="img.jpg" alt="Alt" />
<figcaption><p>Caption here</p></figcaption>
</figure>
"""


def test_image_link_option():
    """Test image_link option wraps images in links."""
    md = MarkdownIt().use(figure_plugin, image_link=True)
    html = md.render("![alt](image.png)\nCaption")

    assert html == """\
<figure>
<a href="image.png"><img src="image.png" alt="alt" /></a>
<figcaption><p>Caption</p></figcaption>
</figure>
"""


def test_image_link_multiple_images():
    """Test image_link option with multiple images."""
    md = MarkdownIt().use(figure_plugin, image_link=True)
    html = md.render("![a](1.png)\n![b](2.png)\nCaption")

    assert html == """\
<figure>
<a href="1.png"><img src="1.png" alt="a" /></a>
<a href="2.png"><img src="2.png" alt="b" /></a>
<figcaption><p>Caption</p></figcaption>
</figure>
"""


def test_image_in_middle_not_transformed():
    """Test that images in middle of text are not transformed."""
    md = MarkdownIt().use(figure_plugin)
    html = md.render("Text before ![img](a.png) and after")

    assert html == """\
<p>Text before <img src="a.png" alt="img" /> and after</p>
"""


def test_image_at_end_not_transformed():
    """Test that images at the end of text are not transformed."""
    md = MarkdownIt().use(figure_plugin)
    html = md.render(
        "Following image is in the middle:\n![Alt text](https://example.com/image.jpg)"
    )

    # Image not at start, should not be transformed
    assert html == """\
<p>Following image is in the middle:
<img src="https://example.com/image.jpg" alt="Alt text" /></p>
"""


def test_regular_link_not_transformed():
    """Test that regular links are not transformed."""
    md = MarkdownIt().use(figure_plugin)
    html = md.render("[not an image](https://example.com)")

    assert html == """\
<p><a href="https://example.com">not an image</a></p>
"""


def test_caption_with_formatting():
    """Test that caption supports inline markdown formatting."""
    md = MarkdownIt().use(figure_plugin)
    html = md.render(
        "![img](a.png)\nCaption with **bold** and *italic* and [link](url)"
    )

    assert html == """\
<figure>
<img src="a.png" alt="img" />
<figcaption><p>Caption with <strong>bold</strong> and <em>italic</em> and <a href="url">link</a></p></figcaption>
</figure>
"""


def test_multiple_paragraphs_separate():
    """Test multiple image paragraphs are transformed separately."""
    md = MarkdownIt().use(figure_plugin)
    text = "![a](1.png)\nCap1\n\n![b](2.png)\nCap2"
    html = md.render(text)

    assert html == """\
<figure>
<img src="1.png" alt="a" />
<figcaption><p>Cap1</p></figcaption>
</figure>
<figure>
<img src="2.png" alt="b" />
<figcaption><p>Cap2</p></figcaption>
</figure>
"""


def test_image_with_title():
    """Test image with title attribute."""
    md = MarkdownIt().use(figure_plugin)
    html = md.render('![alt](img.png "Title")\nCaption')

    assert html == """\
<figure>
<img src="img.png" alt="alt" title="Title" />
<figcaption><p>Caption</p></figcaption>
</figure>
"""


def test_empty_alt_text():
    """Test image with empty alt text."""
    md = MarkdownIt().use(figure_plugin)
    html = md.render("![](img.png)\nCaption")

    assert html == """\
<figure>
<img src="img.png" alt="" />
<figcaption><p>Caption</p></figcaption>
</figure>
"""


def test_two_images_no_caption():
    """Test multiple images without caption."""
    md = MarkdownIt().use(figure_plugin)
    html = md.render("![a](1.png)\n![b](2.png)")

    assert html == """\
<figure>
<img src="1.png" alt="a" />
<img src="2.png" alt="b" /></figure>
"""


def test_combination_options():
    """Test combination of image_link and skip_no_caption."""
    md = MarkdownIt().use(figure_plugin, image_link=True, skip_no_caption=True)

    # Image without caption - should NOT transform
    html1 = md.render("![a](1.png)")
    assert html1 == """\
<p><img src="1.png" alt="a" /></p>
"""

    # Image with caption - should transform with links
    html2 = md.render("![a](1.png)\nCaption")
    assert html2 == """\
<figure>
<a href="1.png"><img src="1.png" alt="a" /></a>
<figcaption><p>Caption</p></figcaption>
</figure>
"""
