import re
from typing import Literal, Callable
from pydantic import BaseModel

from fastapi import HTTPException

from .data import *
from core.constant import support_language, default_lang

c1 = re.compile(r'\s')


def search_text(text: list[str], lang: support_language = default_lang) -> list[set[str]]:
    return [text_index.get(i, set()) for i in set(c1.sub('', ' '.join(text)))]


def search_char(char: str, lang: support_language = default_lang) -> set[str]:
    result = [char_id2story.get(i, set()) for i in char_name2id(char)] + [char_name2story.get(char, set())]
    if len(result) > 1:
        result = result[0].union(*result[1:])
    elif result:
        result = result[0]
    else:
        result = set()

    return result


def search_zone(zone: str, lang: support_language = default_lang) -> set[str]:
    return zone_index.get(zone, set())


def search_regex(regex: str, lang: support_language = default_lang) -> set[str]:
    try:
        reg = re.compile(regex, flags=re.M)
    except re.error as e:
        raise HTTPException(440, detail=e.__str__())
    return set(k for k, text in text_data[lang].items() if reg.search(text))


SearchMethod: dict[str, Callable[[str, support_language], set[str]]] = {
    'char': search_char,
    'zone': search_zone,
    'regex': search_regex
}


class StorySearchParam(BaseModel):
    type: Literal['text', 'zone', 'char', 'regex']
    param: str
    raw: str = None


StorySearchParamGroup = list[StorySearchParam]

secondary_text_pattern = r'%s(?!: )(?:.(?!: ))*$'


def search(params: StorySearchParamGroup) -> set[str]:
    text_group = [p.param for p in params if p.type == 'text']
    result = search_text(text_group) + [SearchMethod[p.type](p.param) for p in params if p.type != 'text']

    if len(result) > 1:
        result = result[0].intersection(*result[1:])
    elif result:
        result = result[0]
    else:
        result = set()

    if text_group:
        for story in result.copy():
            text = text_data['zh_CN'][story]
            for t in text_group:
                i1 = text.find(t)
                if i1 != -1:
                    i2 = text.find('\n', i1 + len(t))
                    i3 = text.find(': ', i1 + len(t), i2)
                    if i3 == -1 or re.search(secondary_text_pattern % t, text, flags=re.MULTILINE):
                        # 非角色名称
                        continue
                result.remove(story)
                break

    return result
