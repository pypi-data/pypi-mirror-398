from typing import List

from bluer_options.terminal import show_usage, xtra


def help_get(
    tokens: List[str],
    mono: bool,
) -> str:
    options = "name"

    return show_usage(
        [
            "@host",
            "get",
            f"[{options}]",
        ],
        "get $abcli_host_name.",
        mono=mono,
    )


def help_reboot(
    tokens: List[str],
    mono: bool,
) -> str:
    options = xtra("dryrun,rpi", mono=mono)

    return show_usage(
        [
            "@host",
            "reboot",
            f"[{options}]",
            "[<machine-name>]",
        ],
        "reboot.",
        mono=mono,
    )


def help_shutdown(
    tokens: List[str],
    mono: bool,
) -> str:
    options = xtra("dryrun,rpi", mono=mono)

    return show_usage(
        [
            "@host",
            "shutdown",
            f"[{options}]",
            "[<machine-name>]",
        ],
        "shutdown.",
        mono=mono,
    )


help_functions = {
    "get": help_get,
    "reboot": help_reboot,
    "shutdown": help_shutdown,
}
