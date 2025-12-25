"""
Authentication middleware dependencies for Overwatch admin panel.
"""

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from overwatch.core.database import get_db_session
from overwatch.models.admin import Admin
from overwatch.services.admin_service import AdminService
from overwatch.utils.security import verify_token


async def get_current_admin_optional(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> Admin | None:
    """
    Get current admin from request (optional).

    Args:
        db: Database session
        request: FastAPI request

    Returns:
        Admin object if authenticated, None otherwise
    """
    if not request:
        return None
    authorization = request.headers.get("authorization")
    if not authorization:
        return None

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            return None
    except ValueError:
        return None

    # Verify token
    payload = verify_token(token)
    if not payload:
        return None

    # Check if it's an access token
    if payload.get("type") != "access":
        return None

    # Get admin from database
    admin_service = AdminService(db)

    admin_id = payload.get("sub")
    if not admin_id:
        return None

    try:
        admin_id = int(admin_id) if isinstance(admin_id, str) else admin_id
    except (ValueError, TypeError):
        return None

    admin = await admin_service.get_admin_by_id(admin_id)

    if not admin or not admin.can_login:
        return None

    return admin


async def get_current_admin_required(
    current_admin: Admin = Depends(get_current_admin_optional),
) -> Admin:
    """
    Get current admin from request (required).

    Args:
        current_admin: Current admin from optional dependency

    Returns:
        Admin object

    Raises:
        HTTPException: If not authenticated
    """
    if not current_admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_admin
