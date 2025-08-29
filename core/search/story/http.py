from enum import IntEnum
from typing import Annotated, Any

from fastapi import HTTPException, Query
from pydantic import BaseModel, Field

from core.config import config
from core.constant import support_language
from core.rate_limiter import Limiter
from core.server import app

from .data import multiple_memory, story_data, story_id2story_seq, text_data, zone_name
from .extra import Extra, ExtraData
from .search import StorySearchParamGroup, search


class StoryRequire(IntEnum):
    ID = 1 << 0
    TYPE = 1 << 1
    NAME = 1 << 2
    CODE = 1 << 3
    LONG_NAME = 1 << 4
    SHORT_NAME = 1 << 5
    ZONE_ID = 1 << 6
    ZONE_NAME = 1 << 7
    EXTRA = 1 << 8

    BASIC = ID | TYPE | ZONE_NAME | EXTRA

    PC = BASIC | LONG_NAME
    PHONE = BASIC | SHORT_NAME

    ALL = 1 << 9 - 1


class StoryResult(BaseModel):
    id: str
    name: str
    zone: str
    type: str
    data: list[ExtraData]


class StoryResponse(BaseModel):
    total: int
    has_more: bool
    data: list[Any | list[Any]]


class StoryRequest(BaseModel):
    params: Annotated[StorySearchParamGroup, Field(min_length=1, max_length=20)]
    lang: support_language = "zh_CN"
    limit: int = Query(ge=1, le=100, default=20)
    offset: int = Query(ge=0, default=0)
    require: int = StoryRequire.PC


def format_result(story_seq: str, require: int, lang: support_language, /, extra: Extra | None = None) -> list[Any]:
    result = []
    data = story_data[story_seq]

    if require & StoryRequire.ID:
        result.append(data.id)
    if require & StoryRequire.TYPE:
        result.append(data.type)
    if require & StoryRequire.NAME:
        result.append(data.name[lang])
    if require & StoryRequire.CODE:
        result.append(data.code)
    if require & StoryRequire.LONG_NAME:
        result.append(data.long_name[lang])
    if require & StoryRequire.SHORT_NAME:
        result.append(data.short_name[lang])
    if require & StoryRequire.ZONE_ID:
        result.append(data.zone)
    if require & StoryRequire.ZONE_NAME:
        result.append(zone_name[data.zone][lang])
    if require & StoryRequire.EXTRA and extra:
        result.append(extra.get(story_seq))

    return result


@app.post("/story", tags=["Story"], description="搜索剧情")
def search_story(req: StoryRequest, limiter=Limiter.depends(**config.limit.rate["story"].param)) -> StoryResponse:
    # search.arkfans.top 采用 10q/5s 限频
    result = sorted(search(req.params))
    total = len(result)
    has_more = False

    if req.offset > len(result):
        result = []
    else:
        result = result[req.offset :]
        if len(result) > req.limit:
            result = result[: req.limit]
            has_more = True

    if req.require & StoryRequire.EXTRA:
        result = [format_result(i, req.require, req.lang, extra=Extra(req.params)) for i in result]
    else:
        result = [format_result(i, req.require, req.lang) for i in result]

    if result and len(result[0]) == 1:
        result = [result[i][0] for i in range(len(result))]

    return StoryResponse(total=total, has_more=has_more, data=result)


@app.get("/story/read", tags=["Story"], description="获取剧情文本")
def read_story(
    id_: str, lang: support_language, limiter=Limiter.depends(**config.limit.rate["read_story"].param)
) -> tuple[str, str]:
    if (seq := story_id2story_seq.get(id_)) and (text := text_data[lang].get(seq)):
        return story_data[seq].name[lang], text

    raise HTTPException(status_code=404)


class Request(BaseModel):
    params: Annotated[StorySearchParamGroup, Field(min_length=1, max_length=20)]
    lang: support_language = "zh_CN"
    limit: int = Query(ge=1, le=100, default=20)
    offset: int = Query(ge=0, default=0)


class MultipleMemoryRequest(BaseModel):
    id: str


@app.post("/story/multiple_memory", tags=["Story"], description="获取干员密录是否有多个，用于转跳PRTS")
def read_story_multiple_memory(
    req: MultipleMemoryRequest, limiter=Limiter.depends(**config.limit.rate["story_multiple_memory"].param)
) -> bool:
    # 支持prts转跳 .e.g 安洁莉娜/干员密录/1-1 & 梅尔/干员密录/1
    return req.id in multiple_memory
