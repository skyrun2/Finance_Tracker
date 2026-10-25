from typing import Annotated

from fastapi import Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db


async def pagination_params(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
):
    return {"page": page, "per_page": per_page}
