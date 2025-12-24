"""
资产管理服务层

处理资产的 CRUD 操作
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import logging

from sqlalchemy import select, func, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession

from jettask.db.models.asset import Asset, AssetType, AssetStatus
from jettask.schemas.asset import (
    AssetCreate,
    AssetUpdate,
    AssetInfo,
    AssetListResponse,
    AssetGroupSummary
)

logger = logging.getLogger(__name__)


class AssetService:
    """资产管理服务类"""

    @staticmethod
    async def create_asset(
        pg_session: AsyncSession,
        namespace: str,
        request: AssetCreate
    ) -> AssetInfo:
        existing = await pg_session.execute(
            select(Asset).where(
                Asset.namespace == namespace,
                Asset.asset_group == request.asset_group,
                Asset.name == request.name
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"资产 '{request.asset_group}/{request.name}' 已存在")

        asset = Asset(
            namespace=namespace,
            asset_type=AssetType(request.asset_type.value),
            asset_group=request.asset_group,
            name=request.name,
            config=request.config,
            weight=request.weight,
            description=request.description,
            metadata_=request.metadata,
            status=AssetStatus.ACTIVE
        )

        pg_session.add(asset)
        await pg_session.commit()
        await pg_session.refresh(asset)

        logger.info(f"资产已创建: {namespace}/{request.asset_group}/{request.name}")

        return AssetService._to_asset_info(asset)

    @staticmethod
    async def update_asset(
        pg_session: AsyncSession,
        namespace: str,
        asset_id: int,
        request: AssetUpdate
    ) -> Optional[AssetInfo]:
        result = await pg_session.execute(
            select(Asset).where(
                Asset.namespace == namespace,
                Asset.id == asset_id
            )
        )
        asset = result.scalar_one_or_none()

        if not asset:
            return None

        if request.config is not None:
            asset.config = request.config
        if request.status is not None:
            asset.status = AssetStatus(request.status.value)
        if request.weight is not None:
            asset.weight = request.weight
        if request.description is not None:
            asset.description = request.description
        if request.metadata is not None:
            asset.metadata_ = request.metadata

        asset.updated_at = datetime.now(timezone.utc)

        await pg_session.commit()
        await pg_session.refresh(asset)

        logger.info(f"资产已更新: id={asset_id}")

        return AssetService._to_asset_info(asset)

    @staticmethod
    async def delete_asset(
        pg_session: AsyncSession,
        namespace: str,
        asset_id: int
    ) -> bool:
        result = await pg_session.execute(
            select(Asset).where(
                Asset.namespace == namespace,
                Asset.id == asset_id
            )
        )
        asset = result.scalar_one_or_none()

        if not asset:
            return False

        await pg_session.delete(asset)
        await pg_session.commit()

        logger.info(f"资产已删除: id={asset_id}")

        return True

    @staticmethod
    async def get_asset(
        pg_session: AsyncSession,
        namespace: str,
        asset_id: int
    ) -> Optional[AssetInfo]:
        result = await pg_session.execute(
            select(Asset).where(
                Asset.namespace == namespace,
                Asset.id == asset_id
            )
        )
        asset = result.scalar_one_or_none()

        if not asset:
            return None

        return AssetService._to_asset_info(asset)

    @staticmethod
    async def get_asset_by_name(
        pg_session: AsyncSession,
        namespace: str,
        asset_group: str,
        name: str
    ) -> Optional[AssetInfo]:
        result = await pg_session.execute(
            select(Asset).where(
                Asset.namespace == namespace,
                Asset.asset_group == asset_group,
                Asset.name == name
            )
        )
        asset = result.scalar_one_or_none()

        if not asset:
            return None

        return AssetService._to_asset_info(asset)

    @staticmethod
    async def list_assets(
        pg_session: AsyncSession,
        namespace: str,
        asset_type: Optional[AssetType] = None,
        asset_group: Optional[str] = None,
        status: Optional[AssetStatus] = None,
        page: int = 1,
        page_size: int = 20
    ) -> AssetListResponse:
        conditions = [Asset.namespace == namespace]

        if asset_type:
            conditions.append(Asset.asset_type == asset_type)
        if asset_group:
            conditions.append(Asset.asset_group == asset_group)
        if status:
            conditions.append(Asset.status == status)

        query = select(Asset).where(and_(*conditions))

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await pg_session.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Asset.asset_group, Asset.name)
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await pg_session.execute(query)
        assets = result.scalars().all()

        return AssetListResponse(
            success=True,
            data=[AssetService._to_asset_info(a) for a in assets],
            total=total,
            page=page,
            page_size=page_size
        )

    @staticmethod
    async def list_assets_by_group(
        pg_session: AsyncSession,
        namespace: str,
        asset_group: str,
        status: Optional[AssetStatus] = None
    ) -> List[AssetInfo]:
        conditions = [
            Asset.namespace == namespace,
            Asset.asset_group == asset_group
        ]

        if status:
            conditions.append(Asset.status == status)

        query = select(Asset).where(and_(*conditions)).order_by(Asset.name)

        result = await pg_session.execute(query)
        assets = result.scalars().all()

        return [AssetService._to_asset_info(a) for a in assets]

    @staticmethod
    async def get_group_summary(
        pg_session: AsyncSession,
        namespace: str
    ) -> List[AssetGroupSummary]:
        query = select(
            Asset.asset_group,
            Asset.asset_type,
            func.count().label('total'),
            func.sum(func.cast(Asset.status == AssetStatus.ACTIVE, Integer)).label('active'),
            func.sum(func.cast(Asset.status == AssetStatus.INACTIVE, Integer)).label('inactive'),
            func.sum(func.cast(Asset.status == AssetStatus.ERROR, Integer)).label('error')
        ).where(
            Asset.namespace == namespace
        ).group_by(
            Asset.asset_group, Asset.asset_type
        ).order_by(
            Asset.asset_group
        )

        from sqlalchemy import Integer

        result = await pg_session.execute(query)
        rows = result.all()

        summaries = []
        for row in rows:
            summaries.append(AssetGroupSummary(
                asset_group=row.asset_group,
                asset_type=row.asset_type,
                total=row.total,
                active=row.active or 0,
                inactive=row.inactive or 0,
                error=row.error or 0
            ))

        return summaries

    @staticmethod
    async def batch_update_status(
        pg_session: AsyncSession,
        namespace: str,
        asset_ids: List[int],
        status: AssetStatus
    ) -> int:
        from sqlalchemy import update

        stmt = (
            update(Asset)
            .where(
                Asset.namespace == namespace,
                Asset.id.in_(asset_ids)
            )
            .values(
                status=status,
                updated_at=datetime.now(timezone.utc)
            )
        )

        result = await pg_session.execute(stmt)
        await pg_session.commit()

        return result.rowcount

    @staticmethod
    def _to_asset_info(asset: Asset) -> AssetInfo:
        from jettask.schemas.asset import AssetType as SchemaAssetType
        from jettask.schemas.asset import AssetStatus as SchemaAssetStatus

        return AssetInfo(
            id=asset.id,
            namespace=asset.namespace,
            asset_type=SchemaAssetType(asset.asset_type.value),
            asset_group=asset.asset_group,
            name=asset.name,
            config=asset.config,
            status=SchemaAssetStatus(asset.status.value),
            weight=asset.weight,
            description=asset.description,
            metadata=asset.metadata_,
            created_at=asset.created_at,
            updated_at=asset.updated_at
        )
