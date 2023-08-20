__all__ = [
    'story_data',
    'text_data',
    'zone_name',
    'text_index',
    'char_id2story',
    'char_name2story',
    'zone_index',
    'char_id2name',
    'char_name2id',
    'story_id2story_seq',
    'multiple_memory'
]

import os
from typing import TypedDict, Any

from core.util import json
from core.constant import data_path, support_language


class StoryData:
    id: str
    type: str
    name: dict[support_language, str]
    code: str | None
    zone: str
    long_name: dict[support_language, str]
    short_name: dict[support_language, str]

    suffix: dict[support_language, tuple[str, str]] = {
        'zh_CN': ('行动前', '行动后'),
        'ja_JP': ('戦闘前', '戦闘後'),
        'en_US': ('Before Operation', 'After Operation')
    }

    def __init__(self, data: dict):
        self.id = data['id']
        self.type = data['type']
        self.name = data['name']
        self.code = data['code']
        self.zone = data['zone']
        self.init_name()

    def init_name(self):
        if self.type in ['Memory', 'Rogue']:
            self.same_name(self.name)
        else:
            if not self.name:
                # level_act12side_tr01_end
                names = {}
                for lang in support_language:
                    names[lang] = self.code
                self.same_name(names)
                return
            if self.code:
                if self.code[-3:-1] == 'ST':
                    self.long_name = self.code_and_name
                    self.short_name = self.name.copy()
                else:
                    self.long_name = self.code_and_name
                    self.short_name = self.lang_code
            else:
                self.same_name(self.name)

            if self.id.endswith('beg'):
                self.add_suffix(0)
            elif self.id.endswith('end'):
                self.add_suffix(1)

    def same_name(self, names: dict[support_language, str]):
        self.long_name = names.copy()
        self.short_name = names.copy()

    @property
    def code_and_name(self) -> dict[support_language, str]:
        return {lang: f'{self.code} {n}' for lang, n in self.name.items()}

    @property
    def lang_code(self) -> dict[support_language, str]:
        return {lang: self.code for lang in support_language.__args__}

    def add_suffix(self, suffix_index):
        for lang in self.long_name:
            self.long_name[lang] += ' ' + self.suffix[lang][suffix_index]
        for lang in self.short_name:
            self.short_name[lang] += ' ' + self.suffix[lang][suffix_index]

    def __repr__(self):
        return f'[Story id:{self.id}]'


class SeqData(TypedDict):
    id: set[str]
    name: set[str]


def get_path(filename: str):
    return os.path.join(data_path, 'story', filename + '.json')


def to_set(data: dict) -> dict[Any, set[Any]]:
    for k in data:
        data[k] = set(data[k])
    return data


story_data: dict[str, StoryData] = {k: StoryData(v) for k, v in json.load(get_path('story_data')).items()}
text_data: dict[str, dict[str, str]] = json.load(get_path('text_data'))
zone_name: dict[str, dict[support_language, str]] = json.load(get_path('zone_name'))
text_index: dict[str, set[str]] = to_set(json.load(get_path('text_index')))
char_id2story: dict[str, set[str]] = to_set(json.load(get_path('char_id2story')))
char_name2story: dict[str, set[str]] = to_set(json.load(get_path('char_name2story')))
zone_index: dict[str, set[str]] = to_set(json.load(get_path('zone_index')))
seq_data: list[SeqData] = [SeqData(id=set(i[0]), name=set(i[1])) for i in json.load(get_path('seq_data'))]
char_id2seq: dict[str, set[int]] = {}
char_name2seq: dict[str, set[int]] = {}
story_id2story_seq: dict[str, str] = {}
multiple_memory: set[str] = set()


def init_seq_data():
    for i, data in enumerate(seq_data):
        for char_id in data['id']:
            if char_id in char_name2seq:
                char_id2seq[char_id].add(i)
            else:
                char_id2seq[char_id] = {i}
        for char_name in data['name']:
            if char_name in char_name2seq:
                char_name2seq[char_name].add(i)
            else:
                char_name2seq[char_name] = {i}


init_seq_data()


def init_story_id2story_seq_data():
    for s, data in story_data.items():
        story_id2story_seq[data.id] = s


init_story_id2story_seq_data()


def init_multiple_memory_data():
    for s, data in story_data.items():
        if data.type == 'Memory' and data.id.split('_')[-1] != '1':
            multiple_memory.add('_'.join(data.id.split('_')[:-1] + ['1']))


init_multiple_memory_data()


def char_id2name(char_id: str) -> set[str]:
    result = set()
    result = result.union(*(seq_data[seq]['name'] for seq in char_id2seq[char_id]))
    return result


def char_name2id(char_name: str) -> set[str]:
    result = set()
    result = result.union(*(seq_data[seq]['id'] for seq in char_name2seq[char_name]))
    return result
