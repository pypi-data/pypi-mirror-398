from bluer_objects.README.alias import list_of_aliases

from bluer_agent import NAME
from bluer_agent.README import aliases, audio, chat, crawl, rag, transcription, voice

docs = (
    [
        {
            "path": "../..",
            "macros": {
                "aliases:::": list_of_aliases(NAME),
            },
        },
        {
            "path": "../docs",
        },
    ]
    + aliases.docs
    + audio.docs
    + chat.docs
    + crawl.docs
    + rag.docs
    + transcription.docs
    + voice.docs
)
