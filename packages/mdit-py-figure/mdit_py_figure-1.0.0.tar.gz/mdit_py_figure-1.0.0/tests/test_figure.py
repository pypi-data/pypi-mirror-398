"""Tests for figure plugin."""

from markdown_it import MarkdownIt

from mdit_py_figure import figure_plugin


def test_single_image_with_caption():
    """Test basic figure with single image and caption."""
    md = MarkdownIt().use(figure_plugin)
    html = md.render("![Picture of Oscar.](/path/to/cat.jpg)\nAwesome caption.")

    assert "<figure>" in html
    assert '<img src="/path/to/cat.jpg" alt="Picture of Oscar."' in html
    assert "<figcaption>Awesome caption.</figcaption>" in html
    assert "</figure>" in html


def test_single_image_with_caption_and_bold():
    """Test figure with caption containing markdown formatting."""
    md = MarkdownIt().use(figure_plugin)
    html = md.render(
        "![Picture of Oscar.](/path/to/cat.jpg)\nAwesome caption about **Oscar** the kitty."
    )

    assert "<figure>" in html
    assert (
        "<figcaption>Awesome caption about <strong>Oscar</strong> the kitty.</figcaption>"
        in html
    )


def test_multiple_images_with_caption():
    """Test figure with multiple images and caption."""
    md = MarkdownIt().use(figure_plugin)
    html = md.render(
        "![Picture of Oscar.](/path/to/cat1.jpg)\n"
        "![Picture of Luna.](/path/to/cat2.jpg)\n"
        "![Picture of Oreo.](/path/to/cat3.jpg)\n"
        "Awesome captions about the **kitties**."
    )

    assert html.count("<figure>") == 1
    assert html.count("</figure>") == 1
    assert html.count("<img") == 3
    assert '<img src="/path/to/cat1.jpg" alt="Picture of Oscar."' in html
    assert '<img src="/path/to/cat2.jpg" alt="Picture of Luna."' in html
    assert '<img src="/path/to/cat3.jpg" alt="Picture of Oreo."' in html
    assert (
        "<figcaption>Awesome captions about the <strong>kitties</strong>.</figcaption>"
        in html
    )


def test_single_image_no_caption():
    """Test image without caption (default: still transforms)."""
    md = MarkdownIt().use(figure_plugin)
    html = md.render("![Alt text](https://example.com/image.jpg)")

    assert "<figure>" in html
    assert '<img src="https://example.com/image.jpg" alt="Alt text"' in html
    assert "<figcaption>" not in html
    assert "</figure>" in html


def test_skip_no_caption_option():
    """Test skip_no_caption option."""
    md = MarkdownIt().use(figure_plugin, skip_no_caption=True)
    html = md.render("![Alt text](https://example.com/image.jpg)")

    # Should NOT be transformed to figure
    assert "<figure>" not in html
    assert "<p>" in html
    assert '<img src="https://example.com/image.jpg" alt="Alt text"' in html


def test_skip_no_caption_with_caption():
    """Test skip_no_caption option with caption present."""
    md = MarkdownIt().use(figure_plugin, skip_no_caption=True)
    html = md.render("![Alt](img.jpg)\nCaption here")

    # Should be transformed since caption exists
    assert "<figure>" in html
    assert "<figcaption>Caption here</figcaption>" in html


def test_image_link_option():
    """Test image_link option wraps images in links."""
    md = MarkdownIt().use(figure_plugin, image_link=True)
    html = md.render("![alt](image.png)\nCaption")

    assert "<figure>" in html
    assert '<a href="image.png">' in html
    assert '<img src="image.png" alt="alt"' in html
    assert "</a>" in html
    assert "<figcaption>Caption</figcaption>" in html


def test_image_link_multiple_images():
    """Test image_link option with multiple images."""
    md = MarkdownIt().use(figure_plugin, image_link=True)
    html = md.render("![a](1.png)\n![b](2.png)\nCaption")

    assert '<a href="1.png">' in html
    assert '<a href="2.png">' in html
    assert html.count('<a href="') == 2
    assert html.count("</a>") == 2


def test_image_in_middle_not_transformed():
    """Test that images in middle of text are not transformed."""
    md = MarkdownIt().use(figure_plugin)
    html = md.render("Text before ![img](a.png) and after")

    assert "<figure>" not in html
    assert "<p>Text before" in html
    assert '<img src="a.png" alt="img"' in html
    assert "and after</p>" in html


def test_image_at_end_not_transformed():
    """Test that images at the end of text are not transformed."""
    md = MarkdownIt().use(figure_plugin)
    html = md.render(
        "Following image is in the middle:\n![Alt text](https://example.com/image.jpg)"
    )

    # Image not at start, should not be transformed
    assert "<figure>" not in html
    assert "<p>Following image is in the middle:" in html


def test_regular_link_not_transformed():
    """Test that regular links are not transformed."""
    md = MarkdownIt().use(figure_plugin)
    html = md.render("[not an image](https://example.com)")

    assert "<figure>" not in html
    assert '<a href="https://example.com">not an image</a>' in html


def test_caption_with_formatting():
    """Test that caption supports inline markdown formatting."""
    md = MarkdownIt().use(figure_plugin)
    html = md.render(
        "![img](a.png)\nCaption with **bold** and *italic* and [link](url)"
    )

    assert (
        '<figcaption>Caption with <strong>bold</strong> and <em>italic</em> and <a href="url">link</a></figcaption>'
        in html
    )


def test_multiple_paragraphs_separate():
    """Test multiple image paragraphs are transformed separately."""
    md = MarkdownIt().use(figure_plugin)
    text = "![a](1.png)\nCap1\n\n![b](2.png)\nCap2"
    html = md.render(text)

    assert html.count("<figure>") == 2
    assert html.count("</figure>") == 2
    assert "<figcaption>Cap1</figcaption>" in html
    assert "<figcaption>Cap2</figcaption>" in html


def test_image_with_title():
    """Test image with title attribute."""
    md = MarkdownIt().use(figure_plugin)
    html = md.render('![alt](img.png "Title")\nCaption')

    assert "<figure>" in html
    assert 'title="Title"' in html
    assert '<img src="img.png" alt="alt"' in html


def test_empty_alt_text():
    """Test image with empty alt text."""
    md = MarkdownIt().use(figure_plugin)
    html = md.render("![](img.png)\nCaption")

    assert "<figure>" in html
    assert '<img src="img.png" alt=""' in html
    assert "<figcaption>Caption</figcaption>" in html


def test_two_images_no_caption():
    """Test multiple images without caption."""
    md = MarkdownIt().use(figure_plugin)
    html = md.render("![a](1.png)\n![b](2.png)")

    assert "<figure>" in html
    assert html.count("<img") == 2
    assert "<figcaption>" not in html


def test_combination_options():
    """Test combination of image_link and skip_no_caption."""
    md = MarkdownIt().use(figure_plugin, image_link=True, skip_no_caption=True)

    # Image without caption - should NOT transform
    html1 = md.render("![a](1.png)")
    assert "<figure>" not in html1

    # Image with caption - should transform with links
    html2 = md.render("![a](1.png)\nCaption")
    assert "<figure>" in html2
    assert '<a href="1.png">' in html2
    assert "<figcaption>Caption</figcaption>" in html2
