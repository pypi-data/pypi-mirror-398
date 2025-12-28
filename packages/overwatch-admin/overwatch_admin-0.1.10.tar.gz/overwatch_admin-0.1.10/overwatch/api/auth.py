"""
Authentication API endpoints for Overwatch admin panel.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from overwatch.core.database import get_db_session
from overwatch.middleware.auth import get_current_admin_required
from overwatch.models.admin import Admin
from overwatch.models.audit_log import OverwatchAuditAction
from overwatch.schemas.admin import (
    AdminLoginResponse,
    AdminPasswordChange,
    AdminResponse,
    AdminUpdate,
    TokenRefresh,
    TokenResponse,
)
from overwatch.services.admin_service import AdminService
from overwatch.utils.security import (
    create_access_token,
    create_refresh_token,
    get_security_manager,
    verify_token,
)

router = APIRouter(tags=["Overwatch Authentication"])


@router.post("/login", response_model=AdminLoginResponse)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db_session),
) -> Any:
    """
    Authenticate admin with username and password.

    Args:
        form_data: OAuth2 password form
        request: FastAPI request
        db: Database session

    Returns:
        Login response with tokens and admin info

    Raises:
        HTTPException: If authentication fails
    """
    admin_service = AdminService(db)

    # Authenticate admin
    admin = await admin_service.authenticate_admin(
        form_data.username, form_data.password
    )

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create tokens
    access_token = create_access_token({"sub": str(admin.id)})
    refresh_token = create_refresh_token(str(admin.id))

    admin.last_login = datetime.now(UTC)
    await db.commit()

    # Refresh admin object to get updated values
    await db.refresh(admin)

    # Create session
    await admin_service.create_admin_session(
        admin, request, access_token, refresh_token
    )

    # Log login
    await admin_service.log_admin_action(
        admin_id=getattr(admin, "id", None),
        action=OverwatchAuditAction.LOGIN,
        resource_type="Admin",
        resource_id=getattr(admin, "id", None),
        ip_address=admin_service._get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    # Create admin response using model_validate to handle SQLAlchemy objects properly
    admin_response = AdminResponse.model_validate(admin)

    # Manually set datetime fields to ensure proper ISO format
    if admin.last_login:
        admin_response.last_login = admin.last_login.isoformat()
    if admin.created_at:
        admin_response.created_at = admin.created_at.isoformat()
    if admin.updated_at:
        admin_response.updated_at = admin.updated_at.isoformat()

    return AdminLoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=get_security_manager().access_token_expire_minutes * 60,
        admin=admin_response,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_data: TokenRefresh,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> Any:
    """
    Refresh access token using refresh token.

    Args:
        token_data: Refresh token request
        request: FastAPI request
        db: Database session

    Returns:
        New access token response

    Raises:
        HTTPException: If refresh token is invalid
    """
    # Verify refresh token
    payload = verify_token(token_data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Get admin
    admin_service = AdminService(db)

    admin_id = payload.get("sub")
    if not admin_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    admin = await admin_service.get_admin_by_id(admin_id)

    if not admin or not admin.can_login:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Create new access token
    access_token = create_access_token({"sub": str(admin.id)})

    # Update session
    session = await admin_service.get_admin_session(token_data.refresh_token)
    if session:
        session.session_token = access_token
        session.last_activity = session.expires_at.utcnow()
        session.expires_at = session.expires_at.utcnow() + timedelta(
            minutes=get_security_manager().access_token_expire_minutes
        )
        await db.commit()

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=get_security_manager().access_token_expire_minutes * 60,
    )


@router.post("/logout")
async def logout(
    request: Request,
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    """
    Logout admin by invalidating session.

    Args:
        request: FastAPI request
        current_admin: Current authenticated admin
        db: Database session

    Returns:
        Success message
    """
    admin_service = AdminService(db)

    # Get token from Authorization header
    authorization = request.headers.get("authorization")
    if authorization:
        try:
            scheme, token = authorization.split()
            if scheme.lower() == "bearer":
                # Invalidate session
                await admin_service.invalidate_admin_session(token)
        except ValueError:
            pass

    # Log logout
    await admin_service.log_admin_action(
        admin_id=getattr(current_admin, "id", None),
        action=OverwatchAuditAction.LOGOUT,
        resource_type="Admin",
        resource_id=getattr(current_admin, "id", None),
        ip_address=admin_service._get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    return {"message": "Successfully logged out"}


@router.get("/me", response_model=AdminResponse)
async def get_current_admin_info(
    current_admin: Admin = Depends(get_current_admin_required),
) -> Admin:
    """
    Get current admin information.

    Args:
        current_admin: Current authenticated admin

    Returns:
        Admin information
    """
    return current_admin


@router.put("/me", response_model=AdminResponse)
async def update_current_admin(
    admin_update: AdminUpdate,
    request: Request,
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> Admin:
    """
    Update current admin information.

    Args:
        admin_update: Admin update data
        request: FastAPI request
        current_admin: Current authenticated admin
        db: Database session

    Returns:
        Updated admin information
    """
    admin_service = AdminService(db)

    # Build updates dictionary
    updates = admin_update.model_dump(exclude_unset=True)

    # Don't allow role changes through self-update
    if "role" in updates:
        del updates["role"]

    # Don't allow status changes through self-update
    if "status" in updates:
        del updates["status"]

    # Don't allow is_active changes through self-update
    if "is_active" in updates:
        del updates["is_active"]

    admin = await admin_service.update_admin(
        admin_id=getattr(current_admin, "id", None),
        updates=updates,
        updated_by=getattr(current_admin, "id", None),
    )

    # Log action
    await admin_service.log_admin_action(
        admin_id=getattr(current_admin, "id", None),
        action=OverwatchAuditAction.UPDATE,
        resource_type="Admin",
        resource_id=getattr(current_admin, "id", None),
        old_values={"id": current_admin.id},
        new_values=updates,
        ip_address=admin_service._get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    return admin


@router.put("/change-password")
async def change_password(
    password_data: AdminPasswordChange,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    current_admin: Admin = Depends(get_current_admin_required),
) -> dict[str, str]:
    """
    Change current admin password.

    Args:
        password_data: Password change data containing current and new passwords
        request: FastAPI request
        current_admin: Current authenticated admin
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If password change fails
    """
    admin_service = AdminService(db)

    try:
        await admin_service.change_admin_password(
            admin_id=getattr(current_admin, "id", None),
            current_password=password_data.current_password.get_secret_value(),
            new_password=password_data.new_password.get_secret_value(),
            updated_by=getattr(current_admin, "id", None),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    # Log action
    await admin_service.log_admin_action(
        admin_id=getattr(current_admin, "id", None),
        action=OverwatchAuditAction.UPDATE,
        resource_type="Admin",
        resource_id=getattr(current_admin, "id", None),
        old_values={"id": current_admin.id},
        new_values={"password_changed": True},
        ip_address=admin_service._get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    return {"message": "Password changed successfully"}
