import os
from typing import List
import glob
from tqdm import tqdm

from blueness import module

from bluer_objects import objects, file
from bluer_objects.env import abcli_path_git
from bluer_objects import NAME
from bluer_objects.logger import logger


NAME = module.name(__file__, NAME)


def publish(
    object_name: str,
    list_of_extensions: List[str],
    prefix: str = "",
    asset_name: str = "",
    log: bool = True,
) -> bool:
    if not asset_name:
        asset_name = object_name
    logger.info(
        "{}.publish: {}/{}.* for {} -> {}".format(
            NAME,
            object_name,
            prefix,
            ", ".join(list_of_extensions),
            asset_name,
        )
    )

    for extension in tqdm(list_of_extensions):
        for filename in glob.glob(
            objects.path_of(
                filename=f"{prefix}*.{extension}",
                object_name=object_name,
            )
        ):
            published_filename = os.path.join(
                abcli_path_git,
                "assets",
                asset_name,
                file.name_and_extension(filename).replace(
                    object_name,
                    asset_name,
                ),
            )

            if not file.copy(
                filename,
                published_filename,
                log=log,
            ):
                return False

    logger.info(f"🔗  https://github.com/kamangir/assets/tree/main/{asset_name}")

    return True
