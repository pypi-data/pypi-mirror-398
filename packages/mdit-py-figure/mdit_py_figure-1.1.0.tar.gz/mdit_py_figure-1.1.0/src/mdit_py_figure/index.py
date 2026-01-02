"""Figure plugin implementation for markdown-it-py."""

from typing import Sequence

from markdown_it.token import Token
from markdown_it import MarkdownIt
from markdown_it.renderer import RendererProtocol
from markdown_it.rules_core import StateCore
from markdown_it.utils import EnvType, OptionsDict


def figure_plugin(
    md: MarkdownIt,
    *,
    image_link: bool = False,
    skip_no_caption: bool = False,
) -> None:
    """Convert image paragraphs to HTML figure elements.

    Transforms markdown paragraphs that start with images into HTML <figure>
    elements with optional <figcaption> for text following the images.

    Uses standard markdown image syntax - NO new syntax required.

    Args:
        md: MarkdownIt instance
        image_link: If True, wrap images in <a href=src> tags (default: False)
        skip_no_caption: If True, only transform when caption exists (default: False)

    Example:
        >>> from markdown_it import MarkdownIt
        >>> from mdit_py_figure import figure_plugin
        >>> md = MarkdownIt().use(figure_plugin)
        >>> html = md.render("![alt](image.png)\\n\\nCaption text")
    """

    def figure_core_rule(state: StateCore) -> None:
        """Core rule to transform paragraph tokens into figure tokens."""
        tokens = state.tokens
        i = 0

        while i < len(tokens):
            # Look for paragraph_open tokens
            if tokens[i].type != "paragraph_open":
                i += 1
                continue

            # Check if this is a figure paragraph
            if not _is_figure_paragraph(tokens, i, skip_no_caption):
                i += 1
                continue

            # Extract the paragraph tokens
            para_open = tokens[i]
            inline_token = tokens[i + 1]
            para_close = tokens[i + 2]

            # Split images and caption
            images, caption = _split_images_and_caption(inline_token.children or [])

            # Build new token sequence
            new_tokens = []

            # Figure wrapper
            fig_open = Token("figure_open", "figure", 1)
            fig_open.block = True
            fig_open.map = para_open.map
            new_tokens.append(fig_open)

            # Images inline (no wrapper needed, images render directly)
            img_inline = inline_token.copy()
            img_inline.children = images

            # If image_link option is enabled, wrap images in links
            if image_link and img_inline.children:
                img_inline.children = _wrap_images_in_links(img_inline.children)

            new_tokens.append(img_inline)

            # Caption section (if exists)
            if caption:
                cap_open = Token("figure_caption_open", "figcaption", 1)
                cap_open.block = True
                new_tokens.append(cap_open)

                cap_inline = inline_token.copy()
                cap_inline.children = caption
                new_tokens.append(cap_inline)

                cap_close = Token("figure_caption_close", "figcaption", -1)
                cap_close.block = True
                new_tokens.append(cap_close)

            # Close figure
            fig_close = Token("figure_close", "figure", -1)
            fig_close.block = True
            new_tokens.append(fig_close)

            # Replace tokens[i:i+3] with new_tokens
            tokens[i : i + 3] = new_tokens

            # Skip past the newly inserted tokens
            i += len(new_tokens)

    # Register core rule after inline parsing
    md.core.ruler.after("inline", "figure", figure_core_rule)

    # Register render rules
    md.add_render_rule("figure_open", render_figure_open)
    md.add_render_rule("figure_close", render_figure_close)
    md.add_render_rule("figure_caption_open", render_figure_caption_open)
    md.add_render_rule("figure_caption_close", render_figure_caption_close)


def _split_images_and_caption(
    children: Sequence[Token],
) -> tuple[list[Token], list[Token]]:
    """Split inline children into image tokens and caption tokens.

    Args:
        children: List of inline tokens

    Returns:
        Tuple of (image_tokens, caption_tokens)

    Pattern:
        - image_tokens: [image, softbreak, image, ...]
        - caption_tokens: [text, ...] or []
    """
    images: list[Token] = []

    for i, child in enumerate(children):
        if child.type == "image":
            images.append(child)
        elif child.type == "softbreak" and images:
            # softbreak between images is allowed
            images.append(child)
        else:
            # First non-image/non-softbreak token starts caption
            return (images, list(children[i:]))

    # All tokens were images/softbreaks, no caption
    return (images, [])


def _is_figure_paragraph(
    tokens: Sequence[Token],
    idx: int,
    skip_no_caption: bool,
) -> bool:
    """Check if token at idx is start of figure paragraph.

    Args:
        tokens: Token list
        idx: Index of paragraph_open token
        skip_no_caption: Whether to skip paragraphs without captions

    Returns:
        True if this paragraph should be transformed to a figure
    """
    # Must have paragraph_open, inline, paragraph_close
    if idx + 2 >= len(tokens):
        return False

    if tokens[idx].type != "paragraph_open":
        return False

    if tokens[idx + 1].type != "inline":
        return False

    if tokens[idx + 2].type != "paragraph_close":
        return False

    # Check inline children
    inline_token = tokens[idx + 1]
    if not inline_token.children:
        return False

    # Split to check if starts with images
    images, caption = _split_images_and_caption(inline_token.children)

    # Must have at least one image
    if not images:
        return False

    # Check skip_no_caption option
    if skip_no_caption and not caption:
        return False

    return True


def _wrap_images_in_links(children: Sequence[Token]) -> list[Token]:
    """Wrap each image token in link tokens.

    Args:
        children: List of tokens containing images

    Returns:
        New list with images wrapped in links
    """
    result: list[Token] = []

    for child in children:
        if child.type == "image":
            # Create link_open token
            link_open = Token("link_open", "a", 1)
            link_open.attrSet("href", child.attrGet("src") or "")
            result.append(link_open)

            # Add image
            result.append(child)

            # Create link_close token
            link_close = Token("link_close", "a", -1)
            result.append(link_close)
        else:
            # Keep softbreaks and other tokens as-is
            result.append(child)

    return result


def render_figure_open(
    self: RendererProtocol,
    tokens: Sequence[Token],
    idx: int,
    options: OptionsDict,
    env: EnvType,
) -> str:
    """Render opening figure tag."""
    return "<figure>\n"


def render_figure_close(
    self: RendererProtocol,
    tokens: Sequence[Token],
    idx: int,
    options: OptionsDict,
    env: EnvType,
) -> str:
    """Render closing figure tag."""
    return "</figure>\n"


def render_figure_caption_open(
    self: RendererProtocol,
    tokens: Sequence[Token],
    idx: int,
    options: OptionsDict,
    env: EnvType,
) -> str:
    """Render opening figcaption tag."""
    return "<figcaption><p>"


def render_figure_caption_close(
    self: RendererProtocol,
    tokens: Sequence[Token],
    idx: int,
    options: OptionsDict,
    env: EnvType,
) -> str:
    """Render closing figcaption tag."""
    return "</p></figcaption>\n"
