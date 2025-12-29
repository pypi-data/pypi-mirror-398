import numpy as np

from bluer_objects import objects
from bluer_objects.logger.confusion_matrix import log_confusion_matrix


def test_logger_confusion_matrix():
    object_name = objects.unique_object("test_logger_confusion_matrix")

    confusion_matrix = np.random.random((10, 8))

    assert log_confusion_matrix(
        confusion_matrix,
        objects.path_of(
            object_name=object_name,
            filename="confusion_matrix.png",
        ),
    )
