"""
Authentication dependency — resolves API key to organization.
"""

from uuid import UUID

from fastapi import Header, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.org import Organization


async def get_org_from_api_key(
    x_api_key: str = Header(..., description="Organization API key"),
    db: AsyncSession = Depends(get_db),
) -> Organization:
    """Resolve API key to an Organization. Raises 401 if invalid."""
    result = await db.execute(
        select(Organization).where(
            Organization.api_key == x_api_key,
            Organization.is_active.is_(True),
        )
    )
    org = result.scalar_one_or_none()
    if org is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or inactive API key",
        )
    return org


async def get_org_id(org: Organization = Depends(get_org_from_api_key)) -> UUID:
    """Convenience — returns just the org ID."""
    return org.id
