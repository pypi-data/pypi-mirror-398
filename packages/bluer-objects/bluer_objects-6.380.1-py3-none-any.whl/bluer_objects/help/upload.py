from typing import List

from bluer_options.terminal import show_usage, xtra


def options(mono: bool) -> str:
    return "".join(
        [
            "filename=<filename>",
            xtra(",public,zip", mono=mono),
        ]
    )


def help_upload(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@upload",
            f"[{options(mono=mono)}]",
            "[.|<object-name>]",
        ],
        "upload <object-name>.",
        mono=mono,
    )
