from typing import List

from bluer_options.terminal import show_usage, xtra


def help_convert(
    tokens: List[str],
    mono: bool,
) -> str:
    options = "".join(
        [
            "combine",
            xtra(",~compress,filename=<release.pdf>,install,", mono=mono),
            "upload",
        ]
    )

    args = [
        "[--count <2>]",
    ]

    # ---

    usage_1 = show_usage(
        [
            "@pdf",
            "convert",
            "[{}]".format(f"inline,{options}"),
            "<module-name>",
            "<.,this,this/that.md,this/that.jpg,this/that.pdf>",
            "[-|<object-name>]",
        ]
        + args,
        "md -> pdf.",
        mono=mono,
    )

    # ---

    usage_2 = show_usage(
        [
            "@pdf",
            "convert",
            f"[{options}]",
            "[.|<object-name>]",
        ]
        + args
        + [
            "[--list_missing 0]",
        ],
        "md -> pdf.",
        mono=mono,
    )

    # ---

    return "\n".join(
        [
            usage_1,
            usage_2,
        ]
    )


help_functions = {
    "convert": help_convert,
}
