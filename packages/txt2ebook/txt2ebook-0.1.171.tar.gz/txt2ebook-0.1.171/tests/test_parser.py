# # Copyright (c) 2021,2022,2023,2024,2025 Kian-Meng Ang
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
import argparse
from importlib import import_module

import pytest

from txt2ebook.parser import Parser


@pytest.fixture(name="config")
def fixture_config():
    return argparse.Namespace(
        author=False,
        translator=False,
        cover=None,
        fullwidth=False,
        header_number=False,
        language="zh-cn",
        no_wrapping=False,
        paragraph_separator="\n\n",
        raise_on_warning=False,
        re_author=(),
        re_chapter=(),
        re_delete=False,
        re_delete_line=False,
        re_replace=False,
        re_title=(),
        re_volume=(),
        re_volume_chapter=(),
        sort_volume_and_chapter=False,
        title=False,
        verbose=1,
        width=False,
    )


def test_parsing_two_newlines_as_paragraph_separator(config):
    content = """\
---
书名：月下独酌·其一
作者：李白
---

第一章

天地玄黄。(paragraph 1)

寒来暑往，秋收冬藏。(paragraph 2)
云腾致雨，露结为霜，金生丽水。(paragraph 2)

第二章

剑号巨阙，珠称夜光，果珍李柰，菜重芥姜。(paragraph 1)
"""
    langconf = import_module("txt2ebook.languages.zh_cn")
    parser = Parser(content, config, langconf)
    [chapter1, chapter2] = parser.parse().toc
    assert len(chapter1.paragraphs) == 2
    assert len(chapter2.paragraphs) == 1


def test_parsing_one_newline_as_paragraph_separator(config):
    content = """\
---
书名：月下独酌·其一
作者：李白
---

第一章
天地玄黄。(paragraph 1)
寒来暑往，秋收冬藏。 (paragraph 2)
云腾致雨，露结为霜，金生丽水。 (paragraph 3)
第二章
剑号巨阙，珠称夜光，果珍李柰，菜重芥姜。(paragraph 1)
"""
    config.paragraph_separator = "\n"
    langconf = import_module("txt2ebook.languages.zh_cn")
    parser = Parser(content, config, langconf)
    book = parser.parse()
    [chapter1, chapter2] = book.toc
    assert len(chapter1.paragraphs) == 3
    assert len(chapter2.paragraphs) == 1
