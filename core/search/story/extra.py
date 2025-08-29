__all__ = ["Extra", "ExtraData"]

import re
from collections.abc import Callable
from typing import Literal

from pydantic import BaseModel

from .data import char_id2name, char_name2id, text_data
from .search import StorySearchParam, StorySearchParamGroup


class TextData(BaseModel):
    type: Literal["text"] = "text"
    data: list[list[str | None]]
    has_more: bool
    raw: str

    @classmethod
    def get_handler(cls, param: StorySearchParam) -> Callable[[str], "TextData"]:
        target = param.param
        # 结果组
        base_result = [target if i == 2 else "" for i in range(5)]

        def handler(text: str) -> TextData:
            result_group = []
            # 已处理的文本index
            forward_index = 0
            # 已添加的文本index
            added_index = 0
            while len(result_group) < 5:
                # 目标index
                target_index = text.find(target, forward_index)
                target_forward_index = target_index + len(target)
                if target_index == -1:
                    # 无目标，取消查找
                    break

                # copy基础结果
                result = base_result.copy()

                # result[3] & check 寻找最近的下一个换行符
                n2_index = text.find("\n", target_forward_index)
                if n2_index == -1:
                    # 文本末尾
                    result[3] = text[target_forward_index:]
                else:
                    result[3] = text[target_forward_index:n2_index]

                if result[3].find(": ") != -1:
                    # 排除角色名
                    forward_index = n2_index
                    continue

                # result[1]
                n1_index = text.rfind("\n", 0, target_index)
                if n1_index == -1:
                    result[1] = text[:target_index]
                else:
                    result[1] = text[n1_index + 1 : target_index]

                # result[0]
                if n1_index != -1:
                    n0_index = text.rfind("\n", 0, n1_index)
                    if n0_index >= added_index:
                        if n0_index == -1:
                            result[0] = text[:n1_index]
                        else:
                            result[0] = text[n0_index + 1 : n1_index]

                # result[4]
                if n2_index != -1:
                    n2_index += 1
                    n3_index = text.find("\n", n2_index)
                    if n3_index == -1:
                        result[4] = text[n2_index:]
                    else:
                        result[4] = text[n2_index:n3_index]

                    if result[4].find(target) > result[4].find(": "):
                        added_index = n2_index
                        # 排除下一行有target
                        result[4] = ""
                    else:
                        added_index = n3_index

                forward_index = target_forward_index
                result_group.append(result)

            self = cls.__new__(cls)
            # TODO has_more优化判断
            self.__init__(data=result_group, raw=target, has_more=len(result_group) > 4)

            return self

        return handler


class CharData(BaseModel):
    type: Literal["char"] = "char"
    data: list[str]
    has_more: bool
    raw: str

    @classmethod
    def get_handler(cls, param: StorySearchParam) -> Callable[[str], "CharData"]:
        char_possible_names = set()
        # 该角色名对应的所有可能的名称
        [[char_possible_names.add(name) for name in char_id2name(char_id)] for char_id in char_name2id(param.param)]
        regex = re.compile(rf"^(?:{'|'.join(re.escape(i) for i in char_possible_names)}):.*", flags=re.MULTILINE)

        # TODO 真路人npc名称查找问题

        def handler(text: str) -> CharData:
            """
            CharData handler
            :param text:故事文本
            :return: CharData
            """
            res = regex.findall(text)
            self = cls.__new__(cls)
            if len(res) > 5:
                self.__init__(data=res[:5], has_more=True, raw=param.param)
            else:
                self.__init__(data=res, has_more=False, raw=param.param)

            return self

        return handler


class RegexData(BaseModel):
    type: Literal["regex"] = "regex"
    data: list[list[str | None]]
    has_more: bool
    raw: str

    @classmethod
    def get_handler(cls, param: StorySearchParam) -> Callable[[str], "RegexData"]:
        # TODO 弃用纯正则，优化效率

        regex = re.compile(rf"(?:(.+)\n)?^(.*)({param.param})(.*)$(?:\n(.+))", flags=re.MULTILINE)

        def handler(text: str) -> RegexData:
            res = regex.findall(text)
            self = cls.__new__(cls)
            if len(res) > 5:
                self.__init__(data=[self.format_res(i) for i in res[:5]], has_more=True, raw=param.param)
            else:
                self.__init__(data=[self.format_res(i) for i in res], has_more=False, raw=param.param)

            return self

        return handler

    @classmethod
    def format_res(cls, group: list[str | None]):
        # TODO 灵活化限制
        if group[2] is not None and len(group[2]) > 50:
            return (
                list(group[:2]) + [group[2][:25] + f"...[{len(group[2]) - 50}]..." + group[2][-25:]] + list(group[-2:])
            )
        else:
            return list(group[:3]) + list(group[-2:])


ExtraData = TextData | CharData | RegexData


class Extra:
    """提取数据，提供快速搜索"""

    handler_dict: dict[str, Callable[[StorySearchParam], Callable[[str], ExtraData]]] = {
        "text": TextData.get_handler,
        "char": CharData.get_handler,
        "regex": RegexData.get_handler,
    }

    def __init__(self, params: StorySearchParamGroup):
        self.params: StorySearchParamGroup = params
        self.handlers = [self.handler_dict[i.type](i) for i in params if i.type in self.handler_dict]

    def get(self, story_id: str) -> list[ExtraData]:
        text = text_data["zh_CN"][story_id]
        match = [handler(text) for handler in self.handlers]
        return match
