from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Goal
from app.schemas import GoalCreate, GoalResponse, GoalUpdate

router = APIRouter(prefix="/api/v1/goals", tags=["goals"])


@router.get("", response_model=list[GoalResponse])
async def list_goals(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Goal).where(Goal.is_active == True).order_by(Goal.year.desc(), Goal.month))
    return result.scalars().all()


@router.post("", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
async def create_goal(data: GoalCreate, db: AsyncSession = Depends(get_db)):
    goal = Goal(**data.model_dump())
    db.add(goal)
    await db.commit()
    await db.refresh(goal)
    return goal


@router.get("/{goal_id}", response_model=GoalResponse)
async def get_goal(goal_id: str, db: AsyncSession = Depends(get_db)):
    goal = await db.get(Goal, goal_id)
    if not goal or not goal.is_active:
        raise HTTPException(status_code=404, detail="Goal not found")
    return goal


@router.patch("/{goal_id}", response_model=GoalResponse)
async def update_goal(goal_id: str, data: GoalUpdate, db: AsyncSession = Depends(get_db)):
    goal = await db.get(Goal, goal_id)
    if not goal or not goal.is_active:
        raise HTTPException(status_code=404, detail="Goal not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(goal, key, value)
    await db.commit()
    await db.refresh(goal)
    return goal


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal(goal_id: str, db: AsyncSession = Depends(get_db)):
    goal = await db.get(Goal, goal_id)
    if not goal or not goal.is_active:
        raise HTTPException(status_code=404, detail="Goal not found")
    goal.is_active = False
    await db.commit()
