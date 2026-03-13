"""
Section registry — maps section IDs to labels, content paths, and art paths.
Central configuration for the portfolio sections.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class SectionConfig:
    id: str
    label: str
    short_label: str
    content_path: str  # relative to content/ dir
    art_path: str      # relative to ascii_art/ dir
    is_directory: bool  # True = list/detail, False = single file


SECTIONS: tuple[SectionConfig, ...] = (
    SectionConfig(
        id="notice-board",
        label="Notice Board",
        short_label="Notice Board",
        content_path="notice-board.md",
        art_path="notice-board",
        is_directory=False,
    ),
    SectionConfig(
        id="sailing-instructions",
        label="Sailing Instructions",
        short_label="Sailing Inst.",
        content_path="sailing-instructions",
        art_path="sailing-instructions",
        is_directory=True,
    ),
    SectionConfig(
        id="rc-logs",
        label="R/C Logs",
        short_label="R/C Logs",
        content_path="rc-logs",
        art_path="rc-logs",
        is_directory=True,
    ),
    SectionConfig(
        id="contact",
        label="Contact",
        short_label="Contact",
        content_path="contact.md",
        art_path="contact",
        is_directory=False,
    ),
    SectionConfig(
        id="experience",
        label="Experience",
        short_label="Experience",
        content_path="experience",
        art_path="experience",
        is_directory=True,
    ),
)
