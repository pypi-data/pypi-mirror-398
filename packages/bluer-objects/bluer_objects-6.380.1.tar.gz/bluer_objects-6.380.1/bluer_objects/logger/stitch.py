from typing import List
import numpy as np

from blueness import module
from bluer_options import string

from bluer_objects import NAME
from bluer_objects.logger import logger

NAME = module.name(__file__, NAME)


def stitch_images(
    list_of_images: List[np.ndarray],
    cols: int = -1,
    rows: int = -1,
    log: bool = False,
) -> np.ndarray:
    if not list_of_images:
        return np.zeros((1, 1, 3), dtype=np.uint8)

    list_of_images = list_of_images.copy()

    if rows == -1:
        rows = int(np.floor(np.sqrt(len(list_of_images))))
        cols = -1

    if cols == -1:
        cols = int(np.ceil(len(list_of_images) / rows))

    if log:
        logger.info(
            "{}.stitch_images[{}x{}]({}): {}".format(
                NAME,
                rows,
                cols,
                len(list_of_images),
                ", ".join(
                    [string.pretty_shape_of_matrix(image) for image in list_of_images]
                ),
            )
        )

    for image in list_of_images:
        if len(image.shape) == 2:
            image = np.stack([image, image, image], axis=2)

    if rows == 1:
        output = np.zeros(
            (
                max([image.shape[0] for image in list_of_images]),
                sum([image.shape[1] for image in list_of_images]),
                3,
            ),
            dtype=np.uint8,
        )
        x: int = 0
        for image in list_of_images:
            x_new = x + image.shape[1]

            output[
                : image.shape[0],
                x:x_new,
                :,
            ] = image

            x = x_new

        return output

    if cols == 1:
        output = np.zeros(
            (
                sum([image.shape[0] for image in list_of_images]),
                max([image.shape[1] for image in list_of_images]),
                3,
            ),
            dtype=np.uint8,
        )
        y: int = 0
        for image in list_of_images:
            y_new = y + image.shape[0]

            output[
                y:y_new,
                : image.shape[1],
                :,
            ] = image

            y = y_new

        return output

    return stitch_images(
        list_of_images=[
            stitch_images(
                list_of_images[row * cols : (row + 1) * cols],
                cols=cols,
                rows=1,
                log=log,
            )
            for row in range(rows)
        ],
        cols=1,
        rows=rows,
        log=log,
    )
