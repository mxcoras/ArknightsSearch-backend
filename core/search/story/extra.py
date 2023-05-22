__all__ = ['Extra', 'ExtraData']

import re
from pydantic import BaseModel
from typing import Literal

from .search import StorySearchParamGroup
from .data import *


class TextData(BaseModel):
    type: Literal['text'] = 'text'
    data: list[list[str | None]]
    has_more: bool
    raw: str

    @classmethod
    def get(cls, match: list[list[str]], raw: str) -> 'TextData':
        self = cls.__new__(cls)
        if len(match) > 5:
            self.__init__(data=match[:5], raw=raw, has_more=True)
        else:
            self.__init__(data=match, raw=raw, has_more=False)
        return self


class CharData(BaseModel):
    type: Literal['char'] = 'char'
    data: list[str]
    has_more: bool
    raw: str

    @classmethod
    def get(cls, match: list[str], raw: str) -> 'CharData':
        self = cls.__new__(cls)
        if len(match) > 5:
            self.__init__(data=match[:5], has_more=True, raw=raw)
        else:
            self.__init__(data=match, has_more=False, raw=raw)
        return self


ExtraData = TextData | CharData


class Extra:
    text_regex = r'(?:(.*)\n)?(.*)(%s)(.*)(?:\n((?:.(?!%s))*)$)?'
    char_regex = r'^%s:.*'

    # TODO 异名id提取 `“焰尾”索娜`

    """提取数据，提供快速搜索"""

    def __init__(self, params: StorySearchParamGroup):
        self.params: StorySearchParamGroup = params
        self.text_params: list[str] = [i.param for i in params if i.type == 'text']
        self.text_regexes = [(i, re.compile(self.text_regex % (i, i))) for i in self.text_params]
        self.char_regexes = [(i.raw, re.compile(self.char_regex % i.raw, flags=re.MULTILINE)) for i in self.params if
                             i.type == 'char']

    def get(self, story_id: str) -> list[ExtraData]:
        text = text_data['zh_CN'][story_id]
        match = [TextData.get(r[1].findall(text), r[0]) for r in self.text_regexes] \
                + [CharData.get(r[1].findall(text), r[0]) for r in self.char_regexes]
        return match
