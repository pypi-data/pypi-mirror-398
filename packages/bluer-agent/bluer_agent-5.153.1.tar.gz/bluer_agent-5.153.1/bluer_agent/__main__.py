from blueness.argparse.generic import main

from bluer_agent import NAME, VERSION, DESCRIPTION, ICON
from bluer_agent.README import build
from bluer_agent.logger import logger

main(
    ICON=ICON,
    NAME=NAME,
    DESCRIPTION=DESCRIPTION,
    VERSION=VERSION,
    main_filename=__file__,
    tasks={
        "build_README": lambda _: build.build(),
    },
    logger=logger,
)
