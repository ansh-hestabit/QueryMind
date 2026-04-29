"""
Dashboard save/load endpoints for Day 4 MVP.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.dashboard_engine.models import DashboardModel

router = APIRouter()


class SaveDashboardRequest(BaseModel):
    user_id: str = Field(min_length=1)
    name: str = Field(min_length=1, max_length=255)
    source_id: str
    question: str
    sql: str | None = None
    summary: str | None = None
    dashboard_spec: dict
    data_snapshot: list[dict] | None = None


class DashboardResponse(BaseModel):
    id: str
    user_id: str
    name: str
    source_id: str
    question: str
    sql: str | None
    summary: str | None
    dashboard_spec: dict
    data_snapshot: list[dict] | None


@router.post("", response_model=DashboardResponse)
async def save_dashboard(payload: SaveDashboardRequest, db: AsyncSession = Depends(get_db)):
    model = DashboardModel(
        user_id=payload.user_id,
        name=payload.name,
        source_id=payload.source_id,
        question=payload.question,
        sql=payload.sql,
        summary=payload.summary,
        dashboard_spec=payload.dashboard_spec,
        data_snapshot=payload.data_snapshot,
    )
    db.add(model)
    await db.flush()
    await db.refresh(model)
    return DashboardResponse(
        id=str(model.id),
        user_id=model.user_id,
        name=model.name,
        source_id=model.source_id,
        question=model.question,
        sql=model.sql,
        summary=model.summary,
        dashboard_spec=model.dashboard_spec,
        data_snapshot=model.data_snapshot,
    )


@router.get("", response_model=list[DashboardResponse])
async def list_dashboards(user_id: str, db: AsyncSession = Depends(get_db)):
    rows = await db.execute(
        select(DashboardModel)
        .where(DashboardModel.user_id == user_id)
        .order_by(DashboardModel.updated_at.desc())
    )
    items = rows.scalars().all()
    return [
        DashboardResponse(
            id=str(m.id),
            user_id=m.user_id,
            name=m.name,
            source_id=m.source_id,
            question=m.question,
            sql=m.sql,
            summary=m.summary,
            dashboard_spec=m.dashboard_spec,
            data_snapshot=m.data_snapshot,
        )
        for m in items
    ]


@router.get("/{dashboard_id}", response_model=DashboardResponse)
async def get_dashboard(dashboard_id: UUID, db: AsyncSession = Depends(get_db)):
    row = await db.execute(select(DashboardModel).where(DashboardModel.id == dashboard_id))
    model = row.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return DashboardResponse(
        id=str(model.id),
        user_id=model.user_id,
        name=model.name,
        source_id=model.source_id,
        question=model.question,
        sql=model.sql,
        summary=model.summary,
        dashboard_spec=model.dashboard_spec,
        data_snapshot=model.data_snapshot,
    )
