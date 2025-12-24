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

import pytest

from txt2ebook.languages import zh_cn as lang_zh_cn
from txt2ebook.tokenizer import Token, Tokenizer


@pytest.fixture(name="config")
def fixture_config():
    return argparse.Namespace(
        author=False,
        cover=None,
        fullwidth=False,
        language="zh-cn",
        no_wrapping=False,
        output_folder="output",
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
        title=False,
        width=False,
    )


def test_parse(config):
    content = """\
---
书名：天地玄黄
作者：果珍李柰
---

序章

剑号巨阙，珠称夜光。

第一卷 第一章

天地玄黄。

第一卷 天地玄黄 第二章 剑号巨阙

果珍李柰，菜重芥姜。
"""
    tokenizer = Tokenizer(content, config, lang_zh_cn)
    tokenizer.tokenize()

    assert tokenizer.tokens == [
        Token(type="TITLE", line_no=0, value="天地玄黄"),
        Token(type="AUTHOR", line_no=0, value="果珍李柰"),
        Token(type="CHAPTER", line_no=6, value="序章"),
        Token(type="PARAGRAPH", line_no=8, value="剑号巨阙，珠称夜光。"),
        Token(
            type="VOLUME_CHAPTER",
            line_no=0,
            value=[
                Token(type="VOLUME", line_no=0, value="第一卷"),
                Token(type="CHAPTER", line_no=0, value="第一章"),
            ],
        ),
        Token(type="PARAGRAPH", line_no=12, value="天地玄黄。"),
        Token(
            type="VOLUME_CHAPTER",
            line_no=0,
            value=[
                Token(type="VOLUME", line_no=0, value="第一卷 天地玄黄"),
                Token(type="CHAPTER", line_no=0, value="第二章 剑号巨阙"),
            ],
        ),
        Token(type="PARAGRAPH", line_no=16, value="果珍李柰，菜重芥姜。"),
    ]


def test_parse_with_extra_newline_before_chapter_header(config):
    content = """\
---
书名：天地玄黄
作者：果珍李柰
---


序章

剑号巨阙，珠称夜光。


第一卷 第一章

天地玄黄。
"""
    tokenizer = Tokenizer(content, config, lang_zh_cn)
    tokenizer.tokenize()
    assert tokenizer.tokens == [
        Token(type="TITLE", line_no=0, value="天地玄黄"),
        Token(type="AUTHOR", line_no=0, value="果珍李柰"),
        Token(type="CHAPTER", line_no=7, value="序章"),
        Token(type="PARAGRAPH", line_no=9, value="剑号巨阙，珠称夜光。"),
        Token(
            type="VOLUME_CHAPTER",
            line_no=0,
            value=[
                Token(type="VOLUME", line_no=0, value="第一卷"),
                Token(type="CHAPTER", line_no=0, value="第一章"),
            ],
        ),
        Token(type="PARAGRAPH", line_no=14, value="天地玄黄。"),
    ]
