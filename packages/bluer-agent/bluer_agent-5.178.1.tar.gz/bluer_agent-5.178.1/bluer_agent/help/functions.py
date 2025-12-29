from bluer_ai.help.generic import help_functions as generic_help_functions

from bluer_agent import ALIAS
from bluer_agent.help.audio import help_functions as help_audio
from bluer_agent.help.rag import help_functions as help_rag
from bluer_agent.help.chat import help_functions as help_chat
from bluer_agent.help.crawl import help_functions as help_crawl
from bluer_agent.help.transcribe import help as help_transcribe
from bluer_agent.help.voice import help_functions as help_voice

help_functions = generic_help_functions(plugin_name=ALIAS)

help_functions.update(
    {
        "audio": help_audio,
        "chat": help_chat,
        "crawl": help_crawl,
        "rag": help_rag,
        "transcribe": help_transcribe,
        "voice": help_voice,
    }
)
