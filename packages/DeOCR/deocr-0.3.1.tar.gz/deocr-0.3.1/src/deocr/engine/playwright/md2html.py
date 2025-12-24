import asyncio

from markdown_it import MarkdownIt


async def md2html_async(md: str) -> str:
    """
    Convert markdown content to HTML.

    Args:
        md (str): The markdown content to convert.

    Returns:
        str: The converted HTML content.

    Examples::

        >>> html_content = await md2html("# Hello World")
    """
    return await asyncio.to_thread(md2html, md)


def md2html(md: str) -> str:
    """
    Convert markdown content to HTML.

    Args:
        md (str): The markdown content to convert.

    Returns:
        str: The converted HTML content.

    Examples::

        >>> html_content = md2html("# Hello World")
    """
    _renderer = MarkdownIt("gfm-like")
    return _renderer.render(md)
