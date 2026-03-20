import aiofiles
import re

from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Query

from api.path import PathOpr
from api.pattern import pattern


class FileInfo(BaseModel):
    name: str
    title: str
    creator: str = ""
    temp_name: str = ""
    desc: str = ""
    source: str = ""


class Cursor(BaseModel):
    """
    Start at 1.
    """

    start_line: int
    end_line: int


class FileOpr:
    _content: list[str] = []
    _file: list[FileInfo] = []
    _is_empty = False

    @classmethod
    async def ls_file(cls) -> list[FileInfo]:
        if PathOpr._need_update:
            cls._file.clear()
            name = [
                i.name
                for i in PathOpr._path.iterdir()
                if i.is_file() and str(i.name)[0] != "." and i.suffix == ".txt"
            ]
            name.sort()
            for i in name:
                pt = await pattern.match("file", i.replace(".txt", ""))
                cls._file.append(
                    FileInfo(
                        name=i,
                        title=pt.get("title", i.replace(".txt", "")),
                        creator=pt.get("creator", ""),
                    )
                )
        return cls._file

    @classmethod
    async def read(cls, filename: str) -> int:
        for encoding in ("utf-8", "gbk"):
            cls._content.clear()
            try:
                async with aiofiles.open(
                    PathOpr._path / filename, mode="r", encoding=encoding
                ) as f:
                    async for line in f:
                        cls._content.append(line.strip("\n"))

            except UnicodeDecodeError:
                continue

            else:
                return len(cls._content)

        raise Exception("Cannot decode file with utf-8 or gbk")

    @classmethod
    async def _match_line(cls, line: str) -> str | None:
        if line.strip() == "":
            if not cls._is_empty:
                cls._is_empty = True
                return ""

        elif re.match(r"^\s*[-=]{3,}\s*$", line):
            return '<div class="separator"></div>'

        elif pt := await pattern.match("adv", line):
            return None

        elif pt := await pattern.match("volume", line):
            sline = ""
            if not cls._is_empty:
                sline += "\n"
            sline += f"{f'# 第{await pattern._int_to_chinese(pt['chapter'])}卷' if pt['chapter'] else ''}{' ' if pt['chapter'] and pt['title'] else ''}{pt['title']}"
            cls._is_empty = True
            return sline + "\n"

        elif pt := await pattern.match("chapter", line):
            sline = ""
            if not cls._is_empty:
                sline += "\n"
            sline += f"{f"## 第{pt['chapter']}章" if pt['chapter'] else ''}{' ' if pt['chapter'] and pt['title'] else ''}{pt['title']}"
            cls._is_empty = True
            return sline + "\n"

        elif line.startswith(" ") or line.startswith("\t") or line.startswith("　"):
            if cls._is_empty:
                cls._is_empty = False
                return line.strip()
            else:
                return "\n" + line.strip()
        else:
            cls._is_empty = False
            return line.strip()

    @classmethod
    async def get(cls, cursor: Cursor) -> dict[str, list[str]]:
        print(f"Get content from line {cursor.start_line} to {cursor.end_line}")

        if not cls._content:
            raise Exception("No file is read.")

        format_out: list[str] = []
        if cursor.end_line > len(cls._content):
            cursor.end_line = len(cls._content)

        cls._is_empty = False
        for i in range(cursor.start_line - 1, cursor.end_line):
            data = await cls._match_line(cls._content[i])
            if data is not None:
                format_out.append(data)

        return {
            "origin": cls._content[cursor.start_line - 1 : cursor.end_line],
            "format": format_out,
        }

    @classmethod
    async def update_metadata(cls, data: FileInfo):
        for i in range(len(cls._file)):
            if cls._file[i].name == data.name:
                cls._file[i] = data
                return

        raise Exception("Cannot find file name in list.")

    @classmethod
    async def execute(cls):
        error = []
        cls._content.clear()
        for i in PathOpr._temp_path.iterdir():
            if i.is_file():
                i.unlink()
        for i in range(len(cls._file)):
            cls._file[i].temp_name = (
                f"{cls._file[i].title}{"_" + cls._file[i].creator if cls._file[i].creator else ''}.txt"
            )
            isEncode = False
            for encoding in ("utf-8", "gbk"):
                try:
                    async with aiofiles.open(
                        PathOpr._path / cls._file[i].name, mode="r", encoding=encoding
                    ) as fr, aiofiles.open(
                        PathOpr._temp_path / cls._file[i].temp_name,
                        mode="w",
                        encoding="utf-8",
                    ) as fw:
                        await fw.write(
                            f"---\ntitle: {cls._file[i].title}\nauthor: {cls._file[i].creator}\nlanguage: zh-cn\ndesc: {cls._file[i].desc}\nsource: {cls._file[i].source}\n---\n\n"
                        )
                        async for line in fr:
                            data = await cls._match_line(line)
                            if data is not None:
                                await fw.write(data + "\n")

                except UnicodeDecodeError:
                    continue
                else:
                    isEncode = True
                    break
            if not isEncode:
                cls._file[i].temp_name = ""
                error.append(
                    f"{cls._file[i].name}: Cannot decode file with utf-8 or gbk"
                )

        return error if error else None


file_router = APIRouter(prefix="/file", tags=["file"])


@file_router.get("/ls", response_model=list[FileInfo])
async def ls_file():
    """
    List the txt files in the specified path.
    """
    try:
        return await FileOpr.ls_file()
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=400, detail=str(e))


@file_router.post("/update", response_model=None)
async def updata(data: FileInfo):
    try:
        await FileOpr.update_metadata(data)
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=400, detail=str(e))


@file_router.get("/read", response_model=int)
async def read(filename: str = Query(..., description="The file name to read.")):
    try:
        return await FileOpr.read(filename)
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=400, detail=str(e))


@file_router.get("/get", response_model=dict[str, list[str]])
async def get(
    start_line: int = Query(
        ..., description="The start line number of the visible area."
    ),
    end_line: int = Query(..., description="The end line number of the visible area."),
):
    try:
        print(f"Get content from line {start_line} to {end_line}")
        return await FileOpr.get(Cursor(start_line=start_line, end_line=end_line))
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=400, detail=str(e))


@file_router.post("/execute", response_model=list[str] | None)
async def execute():
    try:
        return await FileOpr.execute()
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=400, detail=str(e))
