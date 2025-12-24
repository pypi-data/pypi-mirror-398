# credit: https://github.com/PYUDNG/markdown2image
import os
import os.path as osp
from asyncio import Future
from glob import glob
from typing import TypedDict

from playwright._impl._api_structures import PdfMargins
from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)

try:
    import pymupdf
except ImportError:
    pymupdf: None = None

from ..args import RenderArgs
from ..dataio import get_identifier, item2md
from ..defaults import MAX_ASYNC_PAGES
from .md2html import md2html
from .pdf2image import get_image_path, pdf2image_async


# Init browser and context
class T_status_page(TypedDict):
    id: int
    busy: bool
    page: Page


class IdlePagesManager:
    def __init__(self, max_pages: int) -> None:
        self.pages: list[T_status_page] = []
        self.pages_count: int = 0
        self.idle_futures: list[Future[T_status_page]] = []
        self.max_pages: int = max_pages

    async def new_page(self) -> T_status_page:
        page = await _context.new_page()
        status_page: T_status_page = {
            "id": len(self.pages),
            "busy": False,
            "page": page,
        }
        self.pages.append(status_page)
        return status_page

    async def get_idle_page(self) -> T_status_page:
        # Use existing idle page
        for status_page in self.pages:
            if not status_page["busy"]:
                return status_page

        # No idle page available for now
        if self.pages_count < self.max_pages:
            # create a new page
            self.pages_count += 1
            status_page = await self.new_page()
            return status_page
        else:
            # reaching max_page limit
            status_page = await self.wait_for_page_idle()
            return status_page

    async def wait_for_page_idle(self) -> T_status_page:
        # create a Future and wait for self.set_page_status finishing it
        future: Future[T_status_page] = Future()
        self.idle_futures.append(future)
        status_page = await future
        return status_page

    def set_page_status(self, page_id: int, busy: bool):
        for status_page in self.pages:
            if page_id == status_page["id"]:
                status_page["busy"] = busy
                if not busy and self.idle_futures:
                    future = self.idle_futures.pop(0)
                    future.set_result(status_page)
                return
        raise Exception(f"No page found with provided page_id {repr(page_id)}")


_playwright: Playwright
_browser: Browser
_context: BrowserContext
_manager: IdlePagesManager
# False: not initialized; True: initialized; Future[bool]: initializing
initialized: bool | Future[bool] = False


async def _init():
    global _playwright, _browser, _context, _manager, initialized
    initialized = Future()
    _playwright = await async_playwright().start()
    _browser = await _playwright.chromium.launch()
    _context = await _browser.new_context(viewport={"width": 512, "height": 512})
    # config vars
    # modify max_pages before first convertion/screenshot, modification later then will not take effect
    _manager = IdlePagesManager(MAX_ASYNC_PAGES)
    initialized.set_result(True)
    initialized = True


async def html2image(
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

        >>> image_paths = await html2image("<h1>Hello World</h1>", root="./output")
    """
    global initialized
    if isinstance(initialized, Future):
        await initialized
    elif not initialized:
        await _init()

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

    # Get an idle page to render
    status_page: T_status_page = await _manager.get_idle_page()
    _manager.set_page_status(status_page["id"], True)
    page = status_page["page"]

    # render & screenshot
    await page.reload(wait_until="commit")
    width, height = render_args.pagesize

    assert isinstance(width, int)
    height = None if render_args.autoAdjustHeight else height
    await page.set_viewport_size({"width": width, "height": height or width})
    await page.set_content(html=html, wait_until="load")

    # inject css if any
    if render_args.css_path is not None:
        await page.add_style_tag(path=render_args.css_path)
    if render_args.css is not None:
        await page.add_style_tag(content=render_args.css)

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
            await page.screenshot(
                path=path, full_page=render_args.autoAdjustHeight or height is None
            )
            # release page to idle pages
            _manager.set_page_status(status_page["id"], False)
            return [path]

    # export as pdf and then convert to images
    pdf_bytes = await page.pdf(
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
        # save pdf if specified
        path=f"{subfolder}/sample.pdf" if render_args.savePDF else None,
    )
    image_paths = await pdf2image_async(
        pdf_bytes=pdf_bytes,
        subfolder=subfolder,
        dpi=render_args.dpi,
        enable_saving=render_args.saveImage,
        save_format=render_args.save_format,
        save_kwargs=render_args.save_kwargs,
    )
    # release page to idle pages
    _manager.set_page_status(status_page["id"], False)
    return image_paths


async def markdown2image(
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

        >>> image_paths = await markdown2image("# Hello World", root="./output")
    """
    html = md2html(md)
    return await html2image(html, root, render_args=render_args)


async def transform(
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
    deocr_ed = await markdown2image(md, root=cache_dir, render_args=render_args)

    return deocr_ed
