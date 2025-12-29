from typing import List

from blueness import module

from bluer_objects import NAME
from bluer_objects.metadata import get_from_object
from bluer_objects.pdf.convert.convert import convert
from bluer_objects.pdf.convert.missing import list_missing_docs
from bluer_objects.env import abcli_path_git
from bluer_objects.logger import logger


NAME = module.name(__file__, NAME)


def batch(
    object_name: str,
    combine: bool,
    count: int = -1,
    list_missing: bool = True,
) -> bool:
    logger.info(
        "{}.batch: {}{}{}{}".format(
            NAME,
            object_name,
            " + combine" if combine else "",
            "" if count == -1 else f" {count} files",
            " + list missing" if list_missing else "",
        )
    )

    list_of_suffixes: List[str] = get_from_object(
        object_name,
        "pdf",
        [],
    )

    if not convert(
        path_prefix=abcli_path_git,
        list_of_suffixes=list_of_suffixes,
        object_name=object_name,
        combine=combine,
        count=count,
        incremental=False,
    ):
        return False

    if list_missing:
        list_missing_docs(
            object_name=object_name,
            list_of_suffixes=list_of_suffixes,
        )

    return True
