from typing import List
import os
from functools import reduce
import re

from blueness import module
from bluer_options.logger.config import log_list

from bluer_objects import NAME
from bluer_objects import file
from bluer_objects.metadata import get_from_object
from bluer_objects.pdf.convert.convert import convert
from bluer_objects.env import abcli_path_git
from bluer_objects.logger import logger


def list_missing_docs(
    object_name: str,
    list_of_suffixes: List[str],
):
    logger.info(f"{NAME}.list_missing_docs: {object_name}")

    list_of_suffixes_fullpath = [
        os.path.join(abcli_path_git, suffix) for suffix in list_of_suffixes
    ]

    list_of_prefixes_to_ignore: List[str] = [
        os.path.join(abcli_path_git, prefix)
        for prefix in get_from_object(
            object_name,
            "ignore",
            [],
        )
    ]
    log_list(
        logger,
        "ignoring",
        list_of_prefixes_to_ignore,
        "prefix(s)",
        max_count=-1,
    )

    list_of_prefixes: List[str] = sorted(
        list({suffix.split(os.sep)[0] for suffix in list_of_suffixes})
    )
    log_list(
        logger,
        "found",
        list_of_prefixes,
        "prefix(s)",
        max_count=-1,
    )

    list_of_missing_docs: List[str] = [
        filename
        for filename in reduce(
            lambda x, y: x + y,
            [
                file.list_of(
                    os.path.join(
                        abcli_path_git,
                        prefix,
                        "*.md",
                    ),
                    recursive=True,
                )
                for prefix in list_of_prefixes
            ],
            [],
        )
        if not any(
            thing in filename
            for thing in [
                "template",
                "pytest_cache",
            ]
        )
        and filename not in list_of_suffixes_fullpath
        and not any(
            filename.startswith(prefix) for prefix in list_of_prefixes_to_ignore
        )
        and re.search(r"(?:^|-)v(\d+)\.md$", file.name_and_extension(filename)) is None
        and file.name_and_extension(filename) != "README.md"
    ]
    if list_of_missing_docs:
        logger.warning("missing docs.")
        log_list(
            logger,
            "found",
            list_of_missing_docs,
            "missing doc(s)",
            max_count=-1,
            max_length=-1,
        )
    else:
        logger.info("✅ no missing docs.")
