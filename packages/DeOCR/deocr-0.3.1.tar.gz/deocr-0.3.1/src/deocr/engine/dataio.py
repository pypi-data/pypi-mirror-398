import hashlib
import os.path as osp
import re

RE_EXTRACT_PATTERN = re.compile(r"\d{10}-(\d{10})\.\w+")


def get_image_path(subfolder: str, i: int, total: int, extension: str) -> str:
    """
    ``return f'{subfolder}/{i:010d}-{total:010d}.{extension}'``
    """
    return f"{subfolder}/{i:010d}-{total:010d}.{extension}"


def get_n_images(image_path: str) -> int:
    """
    ``extract total from f'{subfolder}/{i:010d}-{total:010d}.{extension}'``
    """
    filename = osp.basename(image_path)
    match = RE_EXTRACT_PATTERN.match(filename)
    assert match is not None
    total_str = match.group(1)
    return int(total_str)


def get_identifier(msg: str, *configs) -> str:
    """
    Generate a unique identifier for a given message.

    Args:
        msg (str): message

    Returns:
        str: identifier
    """
    msg += "".join([str(c) for c in configs])
    return hashlib.md5(msg.encode()).hexdigest()[:32]


def text2md(
    context: str,
    images: list[str | dict] | None = None,
) -> str:
    # convert context to markdown format, embed images if any
    # use 1 to 1 substitution for <image>

    # first assert num of <image> should equal to len(images)
    num_image_tags = context.count("<image>")
    if images is None:
        images = []
    assert num_image_tags == len(images), (
        f"num of <image> tags ({num_image_tags}) should equal to len(images) ({len(images)})"
    )

    # perform 1 to 1 substitution
    for img in images:
        if isinstance(img, str):
            img_md = f"![image]({img})"
        elif isinstance(img, dict) and "url" in img:
            alt = img.get("alt", "")
            url = img["url"]
            img_md = f"![{alt}]({url})"
        elif isinstance(img, dict) and "image_path" in img:
            img_md = f"![image]({img['image_path']})"
        else:
            raise ValueError(f"Unsupported image type: {type(img)}")
        context = context.replace("<image>", img_md, 1)
    return context


def item2md(item: str | dict) -> str:
    if isinstance(item, str):
        # if item is str, treat it as markdown content directly
        md = item
    elif isinstance(item, dict):
        md = " ".join(str(v) for v in item.values())
    else:
        raise TypeError(f"Unsupported item type: {type(item)}")
    return md
