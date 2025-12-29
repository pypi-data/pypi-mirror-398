import os

from bluer_options.help.functions import get_help
from bluer_objects import file, README

from bluer_agent import NAME, VERSION, ICON, REPO_NAME
from bluer_agent.help.functions import help_functions
from bluer_agent.README.docs import docs


def build():
    return all(
        README.build(
            items=readme.get("items", []),
            path=os.path.join(file.path(__file__), readme["path"]),
            ICON=ICON,
            NAME=NAME,
            VERSION=VERSION,
            REPO_NAME=REPO_NAME,
            macros=readme.get("macros", {}),
            help_function=lambda tokens: get_help(
                tokens,
                help_functions,
                mono=True,
            ),
        )
        for readme in docs
    )
