__all__ = [
    'story_data',
    'text_data',
    'zone_name',
    'text_index',
    'char_id2story',
    'char_name2story',
    'zone_index',
    'char_id2name',
    'char_name2id'
]

import os
from typing import TypedDict, Any

from core.util import json
from core.constant import data_path, support_language


class StoryData(TypedDict):
    id: str
    type: str
    name: dict[support_language, str]
    zone: str


class SeqData(TypedDict):
    id: set[str]
    name: set[str]


def get_path(filename: str):
    return os.path.join(data_path, 'story', filename + '.json')


def to_set(data: dict) -> dict[Any, set[Any]]:
    for k in data:
        data[k] = set(data[k])
    return data


story_data: dict[str, StoryData] = json.load(get_path('story_data'))
text_data: dict[str, dict[str, str]] = json.load(get_path('text_data'))
zone_name: dict[str, dict[support_language, str]] = json.load(get_path('zone_name'))
text_index: dict[str, set[str]] = to_set(json.load(get_path('text_index')))
char_id2story: dict[str, set[str]] = to_set(json.load(get_path('char_id2story')))
char_name2story: dict[str, set[str]] = to_set(json.load(get_path('char_name2story')))
zone_index: dict[str, set[str]] = to_set(json.load(get_path('zone_index')))
seq_data: list[SeqData] = [SeqData(id=set(i[0]), name=set(i[1])) for i in json.load(get_path('seq_data'))]
char_id2seq: dict[str, set[int]] = {}
char_name2seq: dict[str, set[int]] = {}


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


def char_id2name(char_id: str) -> set[str]:
    result = set()
    result = result.union(*(seq_data[seq]['name'] for seq in char_id2seq[char_id]))
    return result


def char_name2id(char_name: str) -> set[str]:
    result = set()
    result = result.union(*(seq_data[seq]['id'] for seq in char_name2seq[char_name]))
    return result
