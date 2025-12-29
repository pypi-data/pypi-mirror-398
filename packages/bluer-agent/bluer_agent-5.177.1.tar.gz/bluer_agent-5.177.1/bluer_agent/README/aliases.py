from bluer_objects.README.alias import list_of_aliases

from bluer_agent import NAME

docs = [
    {
        "path": "../docs/aliases",
        "macros": {
            "aliases:::": list_of_aliases(
                NAME,
                itemized=True,
            ),
        },
    }
] + [
    {
        "path": f"../docs/aliases/{alias_name}.md",
    }
    for alias_name in list_of_aliases(
        NAME,
        as_markdown=False,
    )
]
