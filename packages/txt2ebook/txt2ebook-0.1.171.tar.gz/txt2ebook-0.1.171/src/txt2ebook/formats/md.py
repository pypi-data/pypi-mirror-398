# Copyright (c) 2021,2022,2023,2024,2025 Kian-Meng Ang
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Convert and back source text file into text as well."""

import logging
from pathlib import Path

from txt2ebook.formats.base import BaseWriter
from txt2ebook.helpers import lower_underscore
from txt2ebook.models import Chapter, Volume

logger = logging.getLogger(__name__)


class MdWriter(BaseWriter):
    """Module for writing ebook in Markdown (md) format."""

    def write(self) -> None:
        """Generate Markdown files."""
        if self.config.split_volume_and_chapter:
            self._export_multiple_files()
        else:
            output_filename = self._output_filename(".md")
            output_filename.parent.mkdir(parents=True, exist_ok=True)

            with open(output_filename, "w", encoding="utf8") as file:
                logger.info(
                    "Generate Markdown file: %s",
                    output_filename.resolve(),
                )
                file.write(self._to_md())

            if self.config.open:
                self._open_file(output_filename)

    def _get_toc_content_for_split(self) -> str:
        return self._to_toc("-", "# ")

    def _get_volume_chapter_content_for_split(
        self,
        volume: Volume,
        chapter: Chapter,
    ) -> str:
        return self._to_volume_chapter_txt(volume, chapter)

    def _get_chapter_content_for_split(self, chapter: Chapter) -> str:
        return self._to_chapter_txt(chapter)

    def _get_file_extension_for_split(self) -> str:
        return ".md"

    def _get_metadata_filename_for_split(
        self,
        txt_filename: Path,
        extension: str,
    ) -> Path:
        return Path(
            txt_filename.resolve().parent.joinpath(
                self.config.output_folder,
                lower_underscore(
                    f"00_{txt_filename.stem}_"
                    + self._("metadata")
                    + extension,
                ),
            ),
        )

    def _get_toc_filename_for_split(
        self,
        txt_filename: Path,
        extension: str,
    ) -> Path:
        return Path(
            txt_filename.resolve().parent.joinpath(
                self.config.output_folder,
                lower_underscore(
                    f"01_{txt_filename.stem}_" + self._("toc") + extension,
                ),
            ),
        )

    def _get_volume_chapter_filename_for_split(
        self,
        txt_filename: Path,
        section_seq: str,
        chapter_seq: str,
        volume: Volume,
        chapter: Chapter,
        extension: str,
    ) -> Path:
        return Path(
            txt_filename.resolve().parent.joinpath(
                self.config.output_folder,
                lower_underscore(
                    f"{section_seq}"
                    f"_{chapter_seq}"
                    f"_{txt_filename.stem}"
                    f"_{volume.title}"
                    f"_{chapter.title}"
                    f"{extension}",
                ),
            ),
        )

    def _get_chapter_filename_for_split(
        self,
        txt_filename: Path,
        section_seq: str,
        chapter: Chapter,
        extension: str,
    ) -> Path:
        return Path(
            txt_filename.resolve().parent.joinpath(
                self.config.output_folder,
                lower_underscore(
                    f"{section_seq}_{txt_filename.stem}_{chapter.title}{extension}",
                ),
            ),
        )

    def _to_md(self) -> str:
        toc = self._to_toc("-", "# ") if self.config.with_toc else ""
        return self._to_metadata_txt() + toc + self._to_body_txt()

    def _to_body_txt(self) -> str:
        content = []
        for section in self.book.toc:
            if isinstance(section, Volume):
                content.append(self._to_volume_txt(section))
            if isinstance(section, Chapter):
                content.append(self._to_chapter_txt(section))

        return f"{self.config.paragraph_separator}".join(content)

    def _to_volume_txt(self, volume) -> str:
        return (
            f"# {volume.title}"
            + self.config.paragraph_separator
            + self.config.paragraph_separator.join(
                [
                    self._to_chapter_txt(chapter, True)
                    for chapter in volume.chapters
                ],
            )
        )

    def _to_chapter_txt(self, chapter, part_of_volume=False) -> str:
        header = "##" if part_of_volume else "#"
        return (
            f"{header} {chapter.title}"
            + self.config.paragraph_separator
            + self.config.paragraph_separator.join(chapter.paragraphs)
        )

    def _to_volume_chapter_txt(self, volume, chapter) -> str:
        return (
            f"# {volume.title} {chapter.title}"
            + self.config.paragraph_separator
            + self.config.paragraph_separator.join(chapter.paragraphs)
        )
