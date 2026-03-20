import aiofiles

from fastapi import APIRouter, HTTPException, Query
from pathlib import Path
from pydantic import BaseModel
from pypandoc import convert_file as pd_convert

from api.path import PathOpr
from api.file import FileInfo, FileOpr


class TranConfig(BaseModel):
    save_txt: bool = False
    del_origin: bool = False


class TranOpr:
    _files = []

    @classmethod
    async def ls(cls) -> list[FileInfo]:
        cls._files = [i for i in FileOpr._file if i.temp_name]
        return cls._files

    @staticmethod
    async def get(oldname: str) -> dict[str, str]:
        filename = next((f for f in FileOpr._file if f.name == oldname), None)
        if not filename:
            raise HTTPException(status_code=404, detail="File not found")
        for encoding in ("utf-8", "gbk"):
            try:
                async with aiofiles.open(
                    PathOpr._temp_path / filename.temp_name,
                    mode="r",
                    encoding="utf-8",
                ) as fmdf, aiofiles.open(
                    PathOpr._path / filename.name, mode="r", encoding=encoding
                ) as forg:
                    return {"format": await fmdf.read(), "origin": await forg.read()}
            except UnicodeDecodeError:
                continue

    @staticmethod
    async def set(oldname: str, content: str):
        filename = next((f for f in FileOpr._file if f.name == oldname), None)
        if not filename:
            raise HTTPException(status_code=404, detail="File not found")
        async with aiofiles.open(
            PathOpr._temp_path / filename.temp_name,
            mode="w",
            encoding="utf-8",
        ) as fmdf:
            await fmdf.write(content)

    @classmethod
    async def execute(cls, config: TranConfig) -> list[str]:
        print(f"Starting conversion... {cls._files}")
        error = []
        for f in cls._files:
            path = (
                PathOpr._path
                / "Output"
                / f.temp_name.replace(".txt", "")
                / f.temp_name.replace(".txt", ".epub")
            )
            path.parent.mkdir(parents=True, exist_ok=True)
            try:
                pd_convert(
                    str(PathOpr._temp_path / f.temp_name),
                    "epub",
                    format="markdown",
                    outputfile=str(path.resolve()),
                    extra_args=[
                        f"--css={str((Path(__file__).parent / 'epub.css').resolve())}",
                    ],
                )
            except Exception as e:
                error.append(f"{f.temp_name}: {str(e)}")
                continue
            else:
                try:
                    if config.save_txt:
                        (PathOpr._temp_path / f.temp_name).move(
                            path.parent / "Output" / f.temp_name
                        )
                    if config.del_origin:
                        (PathOpr._path / f.name).unlink()
                except Exception as e:
                    error.append(f"{f.temp_name}: {str(e)}")
                    continue
        return error


tran_router = APIRouter(prefix="/tran", tags=["tran"])


@tran_router.get("/ls", response_model=list[FileInfo])
async def ls():
    try:
        return await TranOpr.ls()
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=400, detail=str(e))


@tran_router.get("/get", response_model=dict[str, str])
async def get(oldname: str = Query(..., description="The original filename.")):
    try:
        return await TranOpr.get(oldname)
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=400, detail=str(e))


class setFetchModel(BaseModel):
    content: str


@tran_router.post("/set", response_model=None)
async def set(
    content: setFetchModel,
    oldname: str = Query(..., description="The original filename."),
):
    try:
        await TranOpr.set(oldname, content.content)
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=400, detail=str(e))


@tran_router.post("/execute", response_model=list[str])
async def execute(config: TranConfig):
    try:
        return await TranOpr.execute(config)
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=400, detail=str(e))
