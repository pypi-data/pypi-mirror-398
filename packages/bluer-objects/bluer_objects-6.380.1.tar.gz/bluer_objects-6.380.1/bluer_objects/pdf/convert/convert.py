from tqdm import tqdm
from typing import List
import os
from PIL import Image

from blueness import module

from bluer_objects import NAME
from bluer_objects import file, path
from bluer_objects.metadata import get_from_object, post_to_object
from bluer_objects.pdf.convert.combination import combine_pdfs
from bluer_objects.pdf.convert.image import convert_image
from bluer_objects.pdf.convert.md import convert_md
from bluer_objects.pdf.convert.pdf import convert_pdf
from bluer_objects.logger import logger


NAME = module.name(__file__, NAME)


def convert(
    path_prefix: str,
    list_of_suffixes: List[str],
    object_name: str,
    combine: bool,
    count: int = -1,
    incremental: bool = True,
) -> bool:
    logger.info(f"path_prefix: {path_prefix}")

    list_of_pdfs: List[str] = (
        get_from_object(
            object_name,
            "list_of_pdfs",
            [],
        )
        if incremental
        else []
    )
    if incremental:
        logger.info(f"found {len(list_of_pdfs)} pdf(s)...")

    list_of_pdfs_len_target = -1 if count == -1 else len(list_of_pdfs) + count
    for suffix in tqdm(list_of_suffixes):
        if (
            list_of_pdfs_len_target != -1
            and len(list_of_pdfs) >= list_of_pdfs_len_target
        ):
            logger.info(f"max count {count}, stopping.")
            break

        logger.info(
            "{}.convert {} -> {}".format(
                NAME,
                suffix,
                object_name,
            )
        )

        source_filename = os.path.join(path_prefix, suffix)
        if path.exists(source_filename):
            source_filename = os.path.join(source_filename, "README.md")
            suffix = os.path.join(suffix, "README.md")

        if source_filename.endswith(".md"):
            if not convert_md(
                source_filename,
                suffix,
                object_name,
                list_of_pdfs,
            ):
                return False
        elif file.extension(source_filename) == "pdf":
            if not convert_pdf(
                source_filename,
                suffix,
                object_name,
                list_of_pdfs,
            ):
                return False
        elif file.extension(source_filename) in [
            extension.split(".", 1)[1]
            for extension in Image.registered_extensions().keys()
        ]:
            if not convert_image(
                source_filename,
                suffix,
                object_name,
                list_of_pdfs,
            ):
                return False
        else:
            logger.error(f"{source_filename}: cannot convert to pdf.")
            return False

    if incremental:
        logger.info(f"{len(list_of_pdfs)} pdf(s) so far ...")
        if not post_to_object(
            object_name,
            "list_of_pdfs",
            list_of_pdfs,
        ):
            return False

    if combine:
        return combine_pdfs(
            list_of_pdfs,
            object_name,
        )

    return True
