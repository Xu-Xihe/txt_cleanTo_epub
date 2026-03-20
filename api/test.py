from fastapi import APIRouter, HTTPException, Query

from api.pattern import pattern


test_router = APIRouter(prefix="/test", tags=["test"])


@test_router.get("/chinese_to_int", response_model=int)
async def test_chinese_to_int(
    s: str = Query(..., description="Chinese number to convert")
):
    try:
        return await pattern._chinese_to_int(s)
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=400, detail=str(e))


@test_router.get("/int_to_chinese", response_model=str)
async def test_int_to_chinese(num: int = Query(..., description="Integer to convert")):
    try:
        return await pattern._int_to_chinese(num)
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=400, detail=str(e))


@test_router.get("/compile_pattern", response_model=dict)
async def test_compile_pattern(type: str, string: str):
    try:
        return await pattern.match(type, string)
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=400, detail=str(e))
