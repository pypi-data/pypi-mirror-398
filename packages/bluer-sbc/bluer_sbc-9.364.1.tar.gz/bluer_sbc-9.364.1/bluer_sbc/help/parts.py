from typing import List

from bluer_options.terminal import show_usage, xtra

from bluer_sbc import ALIAS


def help_cd(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@sbc",
            "parts",
            "cd",
        ],
        "cd to part images folder.",
        mono=mono,
    )


def help_adjust(
    tokens: List[str],
    mono: bool,
) -> str:
    options = xtra("dryrun,~grid", mono=mono)

    args = [
        "[--verbose 1]",
    ]

    return show_usage(
        [
            "@sbc",
            "parts",
            "adjust",
            f"[{options}]",
        ]
        + args,
        "adjust part images.",
        mono=mono,
    )


def help_edit(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@sbc",
            "parts",
            "edit",
        ],
        "edit parts db.",
        mono=mono,
    )


def help_open(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@sbc",
            "parts",
            "open",
        ],
        "open part images folder.",
        mono=mono,
    )


help_functions = {
    "adjust": help_adjust,
    "cd": help_cd,
    "edit": help_edit,
    "open": help_open,
}
