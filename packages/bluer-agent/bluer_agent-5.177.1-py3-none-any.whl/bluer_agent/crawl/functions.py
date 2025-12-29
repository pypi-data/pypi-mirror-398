import re


def url_to_filename(url: str) -> str:
    return re.sub(
        r"[^a-zA-Z0-9_-]",
        "_",
        url.replace("https://", "")
        .replace("http://", "")
        .replace(".", "_")
        .rstrip("/"),
    )
