from blueness import module
from bluer_options.help.functions import help_main

from bluer_agent import NAME
from bluer_agent.help.functions import help_functions

NAME = module.name(__file__, NAME)


help_main(NAME, help_functions)
