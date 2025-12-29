import pytest
import numpy as np
import random

from bluer_objects.logger.stitch import stitch_images


@pytest.mark.parametrize(
    ["count"],
    [[count] for count in range(10)],
)
@pytest.mark.parametrize(
    ["cols"],
    [[cols] for cols in [-1, 1, 3]],
)
@pytest.mark.parametrize(
    ["rows"],
    [[rows] for rows in [-1, 1, 3]],
)
def test_logger_stitch_images(
    count: int,
    cols: int,
    rows: int,
):
    rng = np.random.default_rng()

    list_of_images = list_of_images = [
        rng.integers(
            0,
            256,
            (
                random.randint(1, 512),
                random.randint(1, 512),
                random.choice([1, 3]),
            ),
            dtype=np.uint8,
        )
        for _ in range(count)
    ]

    image = stitch_images(
        list_of_images,
        cols=cols,
        rows=rows,
        log=True,
    )
    assert isinstance(image, np.ndarray)
