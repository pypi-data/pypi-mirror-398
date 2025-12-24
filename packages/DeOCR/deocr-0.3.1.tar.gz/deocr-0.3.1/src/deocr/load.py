import tempfile
from typing import Optional

from datasets import load_dataset

from .engine.args import RenderArgs
from .engine.defaults import MAX_ASYNC_PAGES
from .engine.playwright.async_api import transform

_DEFAULT_DEOCRED_COLUMN_NAME = "deocr"


def load_deocr_dataset(
    *args,
    feed_columns: list[str] | None = None,
    deocr_column: str | None = None,
    deocr_cache_dir: str | None = None,
    render_args: Optional[RenderArgs] = None,
    **kwargs,
):
    r"""
    A wrapper for `datasets.load_dataset`_.
    - Expects the same arguments (with some extra) as `datasets.load_dataset`_.
    - Returns a wrapper with same API as ``datasets.Dataset | datasets.DatasetDict`` depending on input args.

    Args:
        feed_columns (list[str], optional): Column IDs for DeOCR. Default: ``_DEFAULT_FEEDS_COLUMNS``.
        deocr_column (str, optional): Column ID for DeOCRed output. Default: ``_DEFAULT_DEOCRED_COLUMN_NAME``.
        cache_dir (str, optional): Root dir for caching. Default: None.
        render_args (RenderArgs, optional): PDF arguments for styling. Default: None.

    Raises:
        NotImplementedError: If the dataset type is not supported.

    Returns:
        DeOCRDataset | DeOCRDatasetDict: The wrapped dataset.

    .. _datasets.load_dataset:
        https://huggingface.co/docs/datasets/main/en/package_reference/loading_methods#datasets.load_dataset
    """
    dataset = load_dataset(*args, **kwargs)
    if feed_columns is None:
        return dataset

    if deocr_column is None:
        deocr_column = _DEFAULT_DEOCRED_COLUMN_NAME
    if deocr_cache_dir is None:
        deocr_cache_dir = tempfile.mkdtemp()
    if render_args is None:
        render_args = RenderArgs()

    async def transform_wrapper(item):
        images = await transform(
            item=item,
            cache_dir=deocr_cache_dir,
            render_args=render_args,
        )
        return {deocr_column: images}

    dataset = dataset.map(
        function=transform_wrapper,
        input_columns=feed_columns,
        batched=False,
        num_proc=MAX_ASYNC_PAGES,
    )
    return dataset
