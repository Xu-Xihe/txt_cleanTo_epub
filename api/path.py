from fastapi import APIRouter, HTTPException, Query
from pathlib import Path
from pydantic import BaseModel


class ExtendMetadata(BaseModel):
    source: str = ""
    language: str = "zh-CN"
    publisher: str = ""
    date: str = ""
    description: str = ""
    subject: str = ""


class PathOpr:
    _path = Path(__file__).parent.parent
    _need_update = False
    _temp_path = Path(__file__).parent.parent.joinpath(".temp")

    @classmethod
    async def ls_folder(cls, p: str):
        path = Path(p)
        name = [
            "/" + i.name for i in path.iterdir() if i.is_dir() and str(i.name)[0] != "."
        ]
        name.sort()
        return name

    @classmethod
    async def set(cls, p: str):
        path = Path(p)
        if not path.is_dir():
            raise Exception(f"{p} is not a directory.")
        else:
            cls._need_update = True
            cls._path = path
            cls._temp_path.mkdir(exist_ok=True)

    @classmethod
    async def get(cls):
        return str(cls._path.resolve())


path_router = APIRouter(prefix="/path", tags=["path"])


@path_router.get("/folder", response_model=list[str])
async def ls_folder(
    path: str = Query(str(PathOpr._path.resolve()), description="The path to list.")
):
    """
    List the directories in the specified path.
    """
    try:
        return await PathOpr.ls_folder(path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@path_router.get("/set", response_model=None)
async def set(path: str = Query(..., description="The path to set.")):
    try:
        await PathOpr.set(path)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail=str(e))


@path_router.get("/get", response_model=str)
async def get():
    try:
        return await PathOpr.get()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
