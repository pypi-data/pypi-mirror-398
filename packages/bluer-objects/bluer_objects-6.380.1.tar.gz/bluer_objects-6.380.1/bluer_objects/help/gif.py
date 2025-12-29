from typing import List

from bluer_options.terminal import show_usage, xtra


def help_gif(
    tokens: List[str],
    mono: bool,
) -> str:
    options = xtra("~download,dryrun,~upload", mono=mono)

    args = [
        "[--frame_count <100>]",
        "[--frame_duration <150>]",
        "[--output_filename <object-name>.gif]",
        "[--scale <1>]",
        "[--suffix <.png>]",
    ]

    return show_usage(
        [
            "@gif",
            f"[{options}]",
            "[.|<object-name>]",
        ]
        + args,
        "generate <object-name>.gif.",
        mono=mono,
    )


def help_gif_open(
    tokens: List[str],
    mono: bool,
) -> str:
    options = xtra("download,filename=<filename.gif>", mono=mono)

    return show_usage(
        [
            "@gif",
            "open",
            f"[{options}]",
            "[.|<object-name>]",
        ],
        "open <object-name>.gif.",
        mono=mono,
    )


help_functions = {
    "": help_gif,
    "open": help_gif_open,
}
