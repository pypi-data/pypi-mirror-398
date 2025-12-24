from dataclasses import dataclass, field


@dataclass
class Metadata:
    """A model representing the book's metadata."""

    title: str = field(default="")
    authors: list[str] = field(default_factory=list)
    translators: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    index: list[str] = field(default_factory=list)
    cover: str = field(default="")
