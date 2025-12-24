import os
import os.path as osp
from typing import TYPE_CHECKING, Mapping, Optional, Sequence, Union

from jsonargparse import auto_cli

from deocr.load import load_deocr_dataset

if TYPE_CHECKING:
    from datasets import (
        DownloadConfig,
        DownloadMode,
        Features,
        Split,
        VerificationMode,
        Version,
    )

    from deocr.engine.args import RenderArgs


# this is a cli convertion tool
# convert datasets to DeOCR format and save them
def convert(
    # load_dataset args
    path: str,
    name: Optional[str] = None,
    data_dir: Optional[str] = None,
    data_files: Optional[
        Union[str, Sequence[str], Mapping[str, Union[str, Sequence[str]]]]
    ] = None,
    split: Optional[Union[str, "Split", list[str], list["Split"]]] = None,
    cache_dir: Optional[str] = None,
    features: Optional["Features"] = None,
    download_config: Optional["DownloadConfig"] = None,
    download_mode: Optional[Union["DownloadMode", str]] = None,
    verification_mode: Optional[Union["VerificationMode", str]] = None,
    keep_in_memory: Optional[bool] = None,
    save_infos: bool = False,
    revision: Optional[Union[str, "Version"]] = None,
    token: Optional[Union[bool, str]] = None,
    streaming: bool = False,
    num_proc: Optional[int] = None,
    storage_options: Optional[dict] = None,
    # deocr args
    feed_columns: list[str] = ["text"],
    deocr_column: str = "deocr_processed",
    deocr_cache_dir: str | None = None,
    render_args: Optional[RenderArgs] = None,
    output_dir: str = "./deocr_datasets",
    # other kwargs from load_dataset
    **config_kwargs,
):
    ds = load_deocr_dataset(
        # load_dataset args
        path=path,
        name=name,
        data_dir=data_dir,
        data_files=data_files,
        split=split,
        cache_dir=cache_dir,
        features=features,
        download_config=download_config,
        download_mode=download_mode,
        verification_mode=verification_mode,
        keep_in_memory=keep_in_memory,
        save_infos=save_infos,
        revision=revision,
        token=token,
        streaming=streaming,
        num_proc=num_proc,
        storage_options=storage_options,
        # deocr args
        feed_columns=feed_columns,
        deocr_column=deocr_column,
        deocr_cache_dir=deocr_cache_dir,
        render_args=render_args,
        # other kwargs from load_dataset
        **config_kwargs,
    )

    ds_outdir = f"{output_dir}/{osp.dirname(path)}"
    os.makedirs(ds_outdir, exist_ok=True)
    for split in ds.keys():
        split_path = os.path.join(ds_outdir, f"{split}.parquet")
        ds[split].to_parquet(split_path)
        print(f"Saved split {split} to {split_path}")


if __name__ == "__main__":
    auto_cli(convert)
