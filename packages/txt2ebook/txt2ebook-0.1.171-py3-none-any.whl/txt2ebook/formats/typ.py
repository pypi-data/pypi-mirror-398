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

"""Convert source text file into typ format."""

import importlib.resources as importlib_res
import logging
import textwrap
from pathlib import Path

import importlib_resources
import typst

from txt2ebook.formats.base import BaseWriter
from txt2ebook.helpers import lower_underscore
from txt2ebook.models import Chapter, Volume

# workaround for Python 3.8
# see https://github.com/messense/typst-py/issues/12#issuecomment-1812956252
importlib_res.files = importlib_resources.files
importlib_res.as_file = importlib_resources.as_file

logger = logging.getLogger(__name__)


class TypWriter(BaseWriter):
    """Module for writing ebook in Typst (typ) format."""

    def __post_init__(self):
        """Post init code."""
        self.index_keywords = (
            self.config.index_keyword + self.book.metadata.index
        )
        logger.debug("Index keywords: %s", self.index_keywords)

    def write(self) -> None:
        """Generate Typst files."""
        new_filename = self._output_filename(".typ")
        new_filename.parent.mkdir(parents=True, exist_ok=True)

        with open(new_filename, "w", encoding="utf8") as file:
            logger.info("Generate Typst file: %s", new_filename.resolve())
            file.write(self._to_typ())

        pdf_filename = new_filename.with_suffix(".pdf")
        logger.info("Generate PDF file: %s", pdf_filename.resolve())
        # pylint: disable=E1101
        typst.compile(new_filename, output=pdf_filename)

        if self.config.open:
            self._open_file(pdf_filename)

    def _get_pagesize(self) -> str:
        return self.config.page_size or self.langconf.DEFAULT_PDF_PAGE_SIZE

    def _to_typ(self) -> str:
        return (
            self._include_packages()
            + self._to_metadata_typ()
            + self._to_cover()
            + self._to_outline()
            + '#set page(numbering: "1")'
            + "\n"
            + "#counter(page).update(1)"
            + "\n"
            + self._to_body_txt()
            + self._index_pages()
        )

    def _include_packages(self) -> str:
        return textwrap.dedent(
            """
                #import "@preview/in-dexter:0.5.3": *

        """,
        )

    def _to_metadata_typ(self) -> str:
        return textwrap.dedent(
            f"""
        #set page(
          paper: "{self._get_pagesize()}",
          margin: (x: 2.5cm, y: 2.5cm),
          numbering: "1",
          number-align: right,
        )

        #show heading.where(
          level: 1
        ): it => block(width: 100%, below: 1.5em)[
          #set align(center)
          #set text(16pt, weight: "regular")
          #smallcaps(it.body)
        ]

        #show heading.where(
          level: 2
        ): it => block(width: 100%, below: 1.5em)[
          #set align(center)
          #set text(14pt, weight: "regular")
          #smallcaps(it.body)
        ]

        #set par(
          first-line-indent: (
            amount: 2em,
            all:true,
          ),
          justify: true,
        )

        #set text(
          font: "Noto Serif CJK SC",
          size: 12pt,
        )

        #show outline.entry: it => {{
          text(it, fill: red)
        }}

        #show link: it => {{
          text(it, fill: red)
        }}

        """,
        )

    def _to_cover(self) -> str:
        return textwrap.dedent(
            f"""
            #set page(paper: "{self._get_pagesize()}", numbering: none)
            #align(center + horizon, text(17pt)[{self.book.metadata.title}])
            #align(center + horizon, text(17pt)[
                {", ".join(self.book.metadata.authors)}])
            #pagebreak()

        """,
        )

    def _to_outline(self) -> str:
        return (
            textwrap.dedent(
                f"""
            #set page(paper: "{self._get_pagesize()}", numbering: none)
            #outline(title: [目录], indent: 1em)
            #pagebreak()
            """,
            )
            if self.config.with_toc
            else ""
        )

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
            f"= {volume.title}"
            + self.config.paragraph_separator
            + self.config.paragraph_separator.join(
                [
                    self._to_chapter_txt(chapter, True)
                    for chapter in volume.chapters
                ],
            )
        )

    def _to_chapter_txt(self, chapter, part_of_volume=False) -> str:
        header = "==" if part_of_volume else "="
        return (
            f"{header} {chapter.title}"
            + self.config.paragraph_separator
            + self._process_paragraphs(chapter.paragraphs)
            + "\n#pagebreak()\n"
        )

    def _to_volume_chapter_txt(self, volume, chapter) -> str:
        return (
            f"= {volume.title} {chapter.title}"
            + self.config.paragraph_separator
            + self._process_paragraphs(chapter.paragraphs)
            + "\n#pagebreak()\n"
        )

    def _process_paragraphs(self, paragraphs) -> str:
        pars = []
        for paragraph in paragraphs:
            par = paragraph.content.strip()
            for keyword in self.index_keywords:
                replace = rf"#index[{keyword}]#link(<index>)[{keyword}]"
                par = par.replace(keyword, replace)
            pars.append(par)

        return self.config.paragraph_separator.join(pars)

    def _get_file_extension_for_split(self) -> str:
        return ".typ"

    def _get_toc_content_for_split(self) -> str:
        return self._to_outline()

    def _get_volume_chapter_content_for_split(
        self,
        volume: Volume,
        chapter: Chapter,
    ) -> str:
        return self._to_volume_chapter_txt(volume, chapter)

    def _get_chapter_content_for_split(self, chapter: Chapter) -> str:
        return self._to_chapter_txt(chapter)

    def _index_pages(self) -> str:
        return textwrap.dedent(
            """
            = 目录 <index>

            #set text(size: 8pt)
            #columns(3)[
                #make-index(outlined: false, use-page-counter: false)
            ]
        """,
        )

    def _get_metadata_filename_for_split(
        self,
        txt_filename: Path,
        extension: str,
    ) -> Path:
        return Path(self._output_folder(), "metadata").with_suffix(extension)

    def _get_toc_filename_for_split(
        self,
        txt_filename: Path,
        extension: str,
    ) -> Path:
        return Path(self._output_folder(), "toc").with_suffix(extension)

    def _get_volume_chapter_filename_for_split(
        self,
        txt_filename: Path,
        section_seq: str,
        chapter_seq: str,
        volume: Volume,
        chapter: Chapter,
        extension: str,
    ) -> Path:
        filename = f"{section_seq}-{lower_underscore(volume.title)}-{chapter_seq}-{lower_underscore(chapter.title)}"
        return Path(self._output_folder(), filename).with_suffix(extension)

    def _get_chapter_filename_for_split(
        self,
        txt_filename: Path,
        section_seq: str,
        chapter: Chapter,
        extension: str,
    ) -> Path:
        filename = f"{section_seq}-{lower_underscore(chapter.title)}"
        return Path(self._output_folder(), filename).with_suffix(extension)
