from typing import List

from bluer_options.terminal import show_usage, xtra
from bluer_ai.help.git import push_options


def help_cd(
    tokens: List[str],
    mono: bool,
) -> str:
    options = "".join(
        [
            xtra("create,", mono=mono),
            "vol=<2>",
        ]
    )

    return show_usage(
        [
            "@assets",
            "cd",
            f"[{options}]",
            "[<path>]",
        ],
        "cd assets volume.",
        mono=mono,
    )


def help_mv(
    tokens: List[str],
    mono: bool,
) -> str:
    options = "".join(
        [
            xtra("create,", mono=mono),
            "extension=<png>,vol=<2>",
        ]
    )

    return show_usage(
        [
            "@assets",
            "mv",
            f"[{options}]",
            "[<path>]",
            "[push,{}]".format(
                push_options(
                    mono=mono,
                    uses_actions=False,
                    uses_pull_request=False,
                    uses_workflows=False,
                )
            ),
        ],
        "mv assets to volume.",
        mono=mono,
    )


def help_publish(
    tokens: List[str],
    mono: bool,
) -> str:
    options = "".join(
        [
            xtra("download,", mono=mono),
            "extensions=<png+txt>",
            xtra(",~pull,", mono=mono),
            "push",
        ]
    )

    args = [
        "[--asset_name <other-object-name>]",
        "[--prefix <prefix>]",
    ]

    return show_usage(
        [
            "@assets",
            "publish",
            f"[{options}]",
            "[.|<object-name>]",
        ]
        + args,
        "<object-name>/<prefix> -> assets.",
        mono=mono,
    )


help_functions = {
    "cd": help_cd,
    "mv": help_mv,
    "publish": help_publish,
}
