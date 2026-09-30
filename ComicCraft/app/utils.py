import re
import uuid


def slugify(
    value: str,
    fallback: str = "comic"
) -> str:

    value = re.sub(
        r"[^a-zA-Z0-9_-]+",
        "-",
        value.strip()
    )

    value = value.strip("-_")

    return value[:80] or fallback


def unique_id() -> str:
    return uuid.uuid4().hex[:12]