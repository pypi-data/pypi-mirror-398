# credit: https://github.com/PYUDNG/markdown2image
import os
import os.path as osp
from glob import glob

from playwright._impl._api_structures import PdfMargins
from playwright.sync_api import Playwright, sync_playwright

try:
    import pymupdf
except ImportError:
    pymupdf: None = None
from ..args import RenderArgs
from ..dataio import get_identifier, item2md
from .md2html import md2html
from .pdf2image import get_image_path, pdf2image

# Init browser and context
_playwright: Playwright = sync_playwright().start()
_browser = _playwright.chromium.launch()
_context = _browser.new_context(viewport={"width": 512, "height": 512})
_page = _context.new_page()


def html2image(
    html: str,
    root: str | None,
    *,
    render_args: RenderArgs,
):
    """
    Render HTML content to image(s) using Playwright.

    Args:
        html (str): The HTML content to render.
        root (str | None): The root directory to save output images.
        render_args (RenderArgs): PDF and rendering options.

    Returns:
        list: DeOCR-ed images, an iterable of image paths or objects.

    Examples::

        >>> image_paths = html2image("<h1>Hello World</h1>", root="./output")
    """
    # fallback to screenshot if
    # 1. pdf2image is not available
    # 2. forceOnePage turned on
    _do_screenshot = pymupdf is None or render_args.forceOnePage

    # predict if any disk io is needed
    _do_save_artifact = render_args.saveImage or render_args.savePDF or _do_screenshot
    if _do_save_artifact:
        assert root is not None, (
            "root directory must be specified when saving artifacts."
        )

    _page.reload(wait_until="commit")
    width, height = render_args.pagesize

    assert isinstance(width, int)
    height = None if render_args.autoAdjustHeight else height
    _page.set_viewport_size({"width": width, "height": height or width})
    _page.set_content(html=html, wait_until="load")

    # inject css if any
    if render_args.css_path is not None:
        _page.add_style_tag(path=render_args.css_path)
    if render_args.css is not None:
        _page.add_style_tag(content=render_args.css)

    # use cache
    if root is None:
        subfolder = None
    else:
        # use cache
        subfolder = f"{root}/{get_identifier(html, render_args)}"
        if osp.exists(subfolder) and not render_args.overwrite:
            cached_files = glob(f"{subfolder}/*.{render_args.save_format}")
            if len(cached_files) > 0:
                cached_files.sort()
                return cached_files

        # if any disk io is needed, prepare output dir
        if _do_save_artifact and not osp.exists(subfolder):
            os.makedirs(subfolder, exist_ok=True)

        # take screenshot
        if _do_screenshot:
            path = get_image_path(subfolder, 0, 1, render_args.save_format)
            _page.screenshot(
                path=path, full_page=render_args.autoAdjustHeight or height is None
            )
            return [path]

    # export as pdf and then convert to images
    pdf_bytes = _page.pdf(
        scale=1,
        display_header_footer=False,
        print_background=True,
        width=f"{width}px",
        height=f"{height}px" if height is not None else None,
        margin=PdfMargins(
            top=f"{render_args.marginTop}px",
            bottom=f"{render_args.marginBottom}px",
            left=f"{render_args.marginLeft}px",
            right=f"{render_args.marginRight}px",
        ),
        # save pdf if specified, root can not be None
        # since _do_save_artifact is True and asserted above
        path=f"{subfolder}/sample.pdf" if render_args.savePDF else None,
    )
    return pdf2image(
        pdf_bytes=pdf_bytes,
        subfolder=subfolder,
        dpi=render_args.dpi,
        enable_saving=render_args.saveImage,
        save_format=render_args.save_format,
        save_kwargs=render_args.save_kwargs,
    )


def markdown2image(
    md: str,
    root: str | None,
    *,
    render_args: RenderArgs,
):
    """
    Render markdown content to image(s) using Playwright.

    Args:
        md (str): The markdown content to render.
        root (str | None): The root directory to save output images.
        render_args (RenderArgs): PDF and rendering options.

    Returns:
        list: DeOCR-ed images, an iterable of image paths or objects.

    Examples::

        >>> image_paths = markdown2image("# Hello World", root="./output")
    """
    html = md2html(md)
    return html2image(html, root, render_args=render_args)


def transform(
    item: str | dict,
    cache_dir: str | None,
    render_args: RenderArgs,
):
    """
    Transform a single data item by converting specified text columns to images.

    Args:
        item (str | dict): Data item containing text fields.
        cache_dir (str | None): Directory to cache generated images.
        render_args (RenderArgs): PDF and rendering options.

    Returns:
        list: DeOCR-ed images, an iterable of image paths or objects.
    """
    md = item2md(item)

    # convert md to image via async markdown2image function
    deocr_ed = markdown2image(md, root=cache_dir, render_args=render_args)

    return deocr_ed
