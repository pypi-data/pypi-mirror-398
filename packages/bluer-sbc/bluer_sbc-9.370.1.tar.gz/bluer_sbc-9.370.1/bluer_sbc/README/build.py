import os

from bluer_options.help.functions import get_help
from bluer_objects import file, README

from bluer_sbc import NAME, VERSION, ICON, REPO_NAME
from bluer_sbc.help.functions import help_functions
from bluer_sbc.README import aliases, designs, parts, root


def build():
    return all(
        README.build(
            items=readme.get("items", []),
            cols=readme.get("cols", 3),
            path=os.path.join(file.path(__file__), readme["path"]),
            ICON=ICON,
            NAME=NAME,
            VERSION=VERSION,
            REPO_NAME=REPO_NAME,
            help_function=lambda tokens: get_help(
                tokens,
                help_functions,
                mono=True,
            ),
            macros=readme.get("macros", {}),
        )
        for readme in root.docs + parts.docs + designs.docs + aliases.docs
    )
