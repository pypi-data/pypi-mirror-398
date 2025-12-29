import matplotlib.pyplot as plt
import numpy as np
from typing import List

from bluer_objects.graphics.signature import justify_text
from bluer_objects import file


def log_confusion_matrix(
    confusion_matrix: np.ndarray,
    filename: str,
    header: List[str] = [],
    footer: List[str] = [],
    x_classes: List[str] = [],
    y_classes: List[str] = [],
    x_name: str = "prediction",
    y_name: str = "label",
    line_width: int = 80,
    log: bool = True,
    figsize: tuple = (10, 10),
) -> bool:
    fig, ax = plt.subplots(figsize=figsize)
    cax = ax.imshow(
        confusion_matrix,
        interpolation="nearest",
        cmap=plt.cm.Blues,
    )
    fig.colorbar(cax)
    ax.set_title(
        justify_text(
            " | ".join(header),
            line_width=line_width,
            return_str=True,
        )
    )
    ax.set_xlabel(
        justify_text(
            " | ".join([x_name] + footer),
            line_width=line_width,
            return_str=True,
        )
    )
    ax.set_ylabel(y_name)

    if not x_classes:
        x_classes = [f"class #{index}" for index in range(confusion_matrix.shape[1])]
    if not y_classes:
        y_classes = [f"class #{index}" for index in range(confusion_matrix.shape[0])]

    ax.set_xticks(np.arange(confusion_matrix.shape[1]))
    ax.set_yticks(np.arange(confusion_matrix.shape[0]))
    ax.set_xticklabels(
        x_classes,
        rotation=45,
        ha="right",
    )
    ax.set_yticklabels(y_classes)

    threshold = confusion_matrix.max() / 2.0
    for i in range(confusion_matrix.shape[0]):
        for j in range(confusion_matrix.shape[1]):
            ax.text(
                j,
                i,
                f"{100*confusion_matrix[i, j]:.1f}%",
                ha="center",
                va="center",
                color="white" if confusion_matrix[i, j] > threshold else "black",
            )

    plt.tight_layout()

    return file.save_fig(
        filename,
        log=log,
    )
