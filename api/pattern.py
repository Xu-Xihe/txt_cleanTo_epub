import copy
import json
import aiofiles
import re

from pydantic import BaseModel
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query


class Pattern(BaseModel):
    enable: bool = True
    alias: str
    pattern: str


class pattern:
    _TOKEN_MAP = {
        r"\{title\}": r"(?P<title>\S.*)",
        r"\{creator\}": r"(?P<creator>[A-Za-z0-9\u4e00-\u9fff]+)",
        r"\{chapter\}": r"(?P<chapter>[零一二三四五六七八九十百千万]+|\d+)",
        r"\{n\}": r"(\d+)",
        r"\{e\}": r"([A-Za-z]+)",
        r"\{c\}": r"([\u4e00-\u9fff]+)",
        r"\{s\}": r"[A-Za-z0-9\u4e00-\u9fff\-_()（）[]]+",
    }

    _pattern: dict[str, list[Pattern]] = {}
    _default_pattern = {
        "file": [
            Pattern(enable=True, alias="基本", pattern="{title}"),
            Pattern(enable=True, alias="标题_作者", pattern="{title}_{creator}"),
            Pattern(enable=True, alias="标题-作者", pattern="{title}-{creator}"),
            Pattern(enable=True, alias="小说下载器", pattern="[{creator}]{title}"),
        ],
        "chapter": [
            Pattern(enable=True, alias="第几章 标题", pattern="第{chapter}章 {title}"),
            Pattern(enable=True, alias="第几章_标题", pattern="第{chapter}章_{title}"),
            Pattern(enable=True, alias="番外 标题", pattern="番外{chapter} {title}"),
            Pattern(enable=True, alias="番外_标题", pattern="番外{chapter}_{title}"),
            Pattern(enable=True, alias="序号 标题", pattern="{chapter} {title}"),
            Pattern(enable=True, alias="序号、标题", pattern="{chapter}、{title}"),
        ],
        "adv": [
            Pattern(enable=True, alias="基本", pattern="广告{s}"),
        ],
        "volume": [
            Pattern(enable=True, alias="第几卷 标题", pattern="第{chapter}卷 {title}"),
            Pattern(enable=True, alias="第几卷_标题", pattern="第{chapter}卷_{title}"),
            Pattern(enable=True, alias="卷外 标题", pattern="卷外{chapter} {title}"),
            Pattern(enable=True, alias="卷外_标题", pattern="卷外{chapter}_{title}"),
        ],
    }
    _compile_pattern: dict[str, list[re.Pattern]] = {
        key: [] for key in _default_pattern.keys()
    }
    _path = Path(__file__).parent / "pattern.json"

    @staticmethod
    async def _chinese_to_int(s: str) -> int:
        num_map = {
            "零": 0,
            "一": 1,
            "二": 2,
            "三": 3,
            "四": 4,
            "五": 5,
            "六": 6,
            "七": 7,
            "八": 8,
            "九": 9,
        }

        unit_map = {"十": 10, "百": 100, "千": 1000, "万": 10000}

        result = 0
        num = 0
        unit = 1

        for char in reversed(s):

            if char in num_map:
                num = num_map[char]
                result += num * unit

            elif char in unit_map:
                unit = unit_map[char]

            else:
                raise ValueError(f"非法中文数字: {char}")

        if "十" in char and result < 10:
            result += 10

        return result

    @staticmethod
    async def _int_to_chinese(num: int) -> str:
        if num > 99 or num < 0:
            raise ValueError("Input error. Only supports integers from 0 to 99.")
        num_map = {
            0: "零",
            1: "一",
            2: "二",
            3: "三",
            4: "四",
            5: "五",
            6: "六",
            7: "七",
            8: "八",
            9: "九",
        }
        if num < 10:
            return num_map[num]
        elif num < 20:
            return "十" + (num_map[num - 10] if num > 10 else "")
        else:
            return (
                num_map[num // 10] + "十" + (num_map[num % 10] if num % 10 > 0 else "")
            )

    @classmethod
    async def init(cls) -> None:
        if cls._path.exists():
            async with aiofiles.open(cls._path, "r") as f:
                content = await f.read()
                cls._pattern = {
                    key: [Pattern.model_validate(p) for p in patterns]
                    for key, patterns in json.loads(content).items()
                }
        else:
            cls._pattern = cls._default_pattern

        for key in cls._default_pattern.keys():
            await cls.compile(key)

    @classmethod
    async def end(cls) -> None:
        async with aiofiles.open(cls._path, "w") as f:
            await f.write(
                json.dumps(
                    {
                        key: [p.model_dump() for p in patterns]
                        for key, patterns in cls._pattern.items()
                    },
                    indent=4,
                    ensure_ascii=False,
                )
            )

    @classmethod
    async def get(cls, type: str) -> list[Pattern]:
        if type not in cls._pattern.keys():
            raise Exception("Invalid pattern type.")
        return cls._pattern[type]

    @classmethod
    async def update(cls, type: str, pattern: Pattern, old_alias: str) -> None:
        if type not in cls._pattern.keys():
            raise Exception("Invalid pattern type.")
        for i in range(len(cls._pattern[type])):
            if cls._pattern[type][i].alias == old_alias:
                cls._pattern[type][i] = pattern
                return
        cls._pattern[type].insert(0, pattern)
        await cls.compile(type)

    @classmethod
    async def delete(cls, type: str, alias: str) -> None:
        if type not in cls._pattern.keys():
            raise Exception("Invalid pattern type.")
        for i in range(len(cls._pattern[type])):
            if cls._pattern[type][i].alias == alias:
                del cls._pattern[type][i]
                await cls.compile(type)
                return
        raise Exception("Pattern not found.")

    @classmethod
    async def reset_default(cls, type: str) -> None:
        if type not in cls._default_pattern.keys():
            raise Exception("Invalid pattern type.")
        cls._pattern[type] = copy.deepcopy(cls._default_pattern[type])
        await cls.compile(type)

    @classmethod
    async def compile(cls, type: str) -> None:
        p_pattern = [p.pattern for p in cls._pattern[type] if p.enable]
        p_sort = sorted(
            p_pattern,
            key=lambda p: len(
                p.replace(r"{n}", "a")
                .replace(r"{e}", "")
                .replace(r"{c}", "")
                .replace(r"{s}", "")
                .replace(r"{title}", "a")
                .replace(r"{creator}", "a")
                .replace(r"{chapter}", "aa")
            ),
            reverse=True,
        )
        cls._compile_pattern[type].clear()
        for p in p_sort:

            p = re.escape(p)

            for token, reg in cls._TOKEN_MAP.items():
                p = p.replace(token, reg)

            p = p.replace(r"\(", r"[(（]")
            p = p.replace(r"\)", r"[)）]")
            p = p.replace(r"\[", r"[\[【]")
            p = p.replace(r"\]", r"[\]】]")

            cls._compile_pattern[type].append(re.compile("^" + p + "$"))

    @classmethod
    async def match(cls, type: str, string: str) -> dict[str, str | int] | None:
        for p in cls._compile_pattern[type]:

            match = p.match(string)
            if not match:
                continue
            result = match.groupdict()

            if result:
                if result.get("chapter"):
                    try:
                        result["chapter"] = int(result["chapter"])
                    except ValueError:
                        result["chapter"] = await cls._chinese_to_int(result["chapter"])

                return result

        return {"title": string} if type == "file" else None


pattern_router = APIRouter(prefix="/pattern", tags=["pattern"])


@pattern_router.get("/{type}", response_model=list[Pattern])
async def get_pattern(type: str):
    try:
        return await pattern.get(type)
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=400, detail=str(e))


@pattern_router.post("/{type}/update")
async def update_pattern(
    p: Pattern,
    type: str,
    old_alias: str = Query("", description="Old pattern alias"),
):
    try:
        await pattern.update(type, p, old_alias)
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=400, detail=str(e))


@pattern_router.get("/{type}/delete")
async def delete_pattern(
    type: str, alias: str = Query(..., description="Pattern alias")
):
    try:
        await pattern.delete(type, alias)
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=400, detail=str(e))


@pattern_router.get("/{type}/reset")
async def reset_default_pattern(type: str):
    try:
        await pattern.reset_default(type)
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=400, detail=str(e))
