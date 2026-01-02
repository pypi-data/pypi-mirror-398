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

"""Abstract class for all supported formats."""

import argparse
import gettext
import io
import logging
import os
import shutil
import subprocess
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from types import ModuleType

from txt2ebook.helpers import lower_underscore
from txt2ebook.models import Book, Chapter, Volume

logger = logging.getLogger(__name__)


class BaseWriter(ABC):
    """Base class for writing to ebook format."""

    def __init__(
        self,
        book: Book,
        opts: argparse.Namespace,
        langconf: ModuleType,
    ) -> None:
        """Create a Writer module.

        Args:
            book(Book): The book model which contains metadata and table of
            contents of volumes and chapters.
            opts(argparse.Namespace): The configs from the command-line.
            langconf(ModuleType): The language configuration module.

        Returns:
            None
        """
        self.book = book
        self.config = opts
        self.langconf = langconf

        if not self.config.output_file:
            self._refresh_output_folder()

        self._load_translation()
        self.__post_init__()

    def _load_translation(self):
        localedir = Path(Path(__file__).parent.parent, "locales")
        translation = gettext.translation(
            "txt2ebook",
            localedir=localedir,
            languages=[self.config.language],
        )
        self._ = translation.gettext

    def _open_file(self, filename):
        if sys.platform == "linux":
            subprocess.call(["xdg-open", filename])
        elif sys.platform == "darwin":
            subprocess.call(["open", filename])
        elif sys.platform == "windows":
            os.startfile(filename)

        logger.info("Open file: %s using default program.", filename.resolve())

    def _refresh_output_folder(self):
        cwd = self._output_folder()
        if self.config.purge and cwd.exists():
            if self.config.yes:
                logger.debug("Purge output folder: %s", cwd.absolute())
                shutil.rmtree(cwd)
            else:
                answer = input(
                    f"Are you sure to purge output folder: {cwd.absolute()}? "
                    "[y/N] ",
                )
                if answer.lower() == "y":
                    logger.debug("Purge output folder: %s", cwd.absolute())
                    shutil.rmtree(cwd)

        logger.debug("Create output folder: %s", cwd)
        cwd.mkdir(parents=True, exist_ok=True)

    def _output_folder(self) -> Path:
        """Get the current working directory.

        Returns:
            Path
        """
        output_folder = Path(self.config.output_folder)
        if output_folder.is_absolute():
            return output_folder.resolve()

        return Path(os.getcwd(), self.config.output_folder).resolve()

    def _output_filename(self, extension: str) -> Path:
        filename = "default"
        if self.config.filename_format:
            filename = self.book.filename_format(self.config.filename_format)
        elif self.config.output_file:
            filename = str(self.config.output_file)
        elif isinstance(
            self.config.input_file,
            (io.TextIOWrapper, io.BufferedReader),
        ):
            if self.config.input_file.name != "<stdin>":
                filename = self.config.input_file.name
            # input from redirection or piping
            elif self.book.metadata.title:
                filename = self.book.metadata.title

        file = Path(filename)

        # do not create to output folder when we explicit set the output path
        # and file
        if self.config.output_file:
            return Path(file.parent, lower_underscore(file.stem)).with_suffix(
                extension,
            )

        return Path(
            file.parent,
            self.config.output_folder,
            lower_underscore(file.stem),
        ).with_suffix(extension)

    def _get_toc_content_for_split(self) -> str:
        raise NotImplementedError

    def _get_volume_chapter_content_for_split(
        self,
        volume: Volume,
        chapter: Chapter,
    ) -> str:
        raise NotImplementedError

    def _get_chapter_content_for_split(self, chapter: Chapter) -> str:
        raise NotImplementedError

    def _get_file_extension_for_split(self) -> str:
        raise NotImplementedError

    def _export_multiple_files(self) -> Path:
        logger.info("Split multiple files")

        extension = self._get_file_extension_for_split()
        txt_filename = Path(self.config.input_file.name)

        metadata_filename = self._get_metadata_filename_for_split(
            txt_filename,
            extension,
        )
        metadata_filename.parent.mkdir(parents=True, exist_ok=True)
        logger.info("Creating %s", metadata_filename)
        with open(metadata_filename, "w", encoding="utf8") as file:
            file.write(self._to_metadata_txt())

        sc_seq = 1
        if self.config.with_toc:
            export_filename = self._get_toc_filename_for_split(
                txt_filename,
                extension,
            )
            export_filename.parent.mkdir(parents=True, exist_ok=True)
            logger.info("Creating %s", export_filename)
            with open(export_filename, "w", encoding="utf8") as file:
                file.write(self._get_toc_content_for_split())

            sc_seq = 2

        for section in self.book.toc:
            section_seq = str(sc_seq).rjust(2, "0")

            ct_seq = 0
            if isinstance(section, Volume):
                for chapter in section.chapters:
                    chapter_seq = str(ct_seq).rjust(2, "0")
                    export_filename = (
                        self._get_volume_chapter_filename_for_split(
                            txt_filename,
                            section_seq,
                            chapter_seq,
                            section,
                            chapter,
                            extension,
                        )
                    )
                    export_filename.parent.mkdir(parents=True, exist_ok=True)
                    logger.info("Creating %s", export_filename)
                    with open(export_filename, "w", encoding="utf8") as file:
                        file.write(
                            self._get_volume_chapter_content_for_split(
                                section,
                                chapter,
                            ),
                        )
                    ct_seq = ct_seq + 1
            if isinstance(section, Chapter):
                export_filename = self._get_chapter_filename_for_split(
                    txt_filename,
                    section_seq,
                    section,
                    extension,
                )
                export_filename.parent.mkdir(parents=True, exist_ok=True)
                logger.info("Creating %s", export_filename)
                with open(export_filename, "w", encoding="utf8") as file:
                    file.write(self._get_chapter_content_for_split(section))

            sc_seq = sc_seq + 1

        return metadata_filename

    def _get_metadata_filename_for_split(
        self,
        txt_filename: Path,
        extension: str,
    ) -> Path:
        raise NotImplementedError

    def _get_toc_filename_for_split(
        self,
        txt_filename: Path,
        extension: str,
    ) -> Path:
        raise NotImplementedError

    def _get_volume_chapter_filename_for_split(
        self,
        txt_filename: Path,
        section_seq: str,
        chapter_seq: str,
        volume: Volume,
        chapter: Chapter,
        extension: str,
    ) -> Path:
        raise NotImplementedError

    def _get_chapter_filename_for_split(
        self,
        txt_filename: Path,
        section_seq: str,
        chapter: Chapter,
        extension: str,
    ) -> Path:
        raise NotImplementedError

    def _to_metadata_txt(self) -> str:
        metadata = [
            self._("title:") + self.book.metadata.title,
            self._("author:") + "，".join(self.book.metadata.authors),
            self._("translator:") + "，".join(self.book.metadata.translators),
            self._("tag:") + "，".join(self.book.metadata.tags),
        ]
        return (
            "---\n"
            + "\n".join(metadata)
            + "\n---"
            + self.config.paragraph_separator
        )

    def _to_toc(self, list_symbol, header_symbol="") -> str:
        toc = ""
        toc += header_symbol + self._("toc") + "\n"

        for section in self.book.toc:
            if isinstance(section, Volume):
                toc += f"\n{list_symbol} " + section.title
                for chapter in section.chapters:
                    toc += f"\n  {list_symbol} " + chapter.title
            if isinstance(section, Chapter):
                toc += f"\n{list_symbol} " + section.title

        return toc + self.config.paragraph_separator

    @abstractmethod
    def write(self) -> None:
        """Generate text files."""

    def __post_init__(self) -> None:
        """Post init code for child class."""
