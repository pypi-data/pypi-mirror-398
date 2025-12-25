"""
Audit log API endpoints for Overwatch admin panel.
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from overwatch.core.database import get_db_session
from overwatch.models.admin import Admin
from overwatch.models.audit_log import OverwatchAuditAction
from overwatch.schemas.crud import PaginatedResponse
from overwatch.services.admin_service import AdminService

from .auth import get_current_admin_required

router = APIRouter(tags=["Overwatch Audit Logs"])


@router.get("/statistics")
async def get_audit_statistics(
    days: int = Query(30, ge=1, le=365),
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """
    Get audit log statistics for the specified time period.
    """
    admin_service = AdminService(db)

    # Check permissions
    if not current_admin.has_permission("read:audit"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view audit statistics",
        )

    # Get statistics
    stats = await admin_service.get_audit_statistics(days=days)

    return stats


@router.get("", response_model=PaginatedResponse[dict[str, Any]])
async def list_audit_logs(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=1000),
    search: str | None = Query(None),
    action: str | None = Query(None),
    resource_type: str | None = Query(None),
    admin_id: int | None = Query(None),
    success: bool | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_direction: str = Query("desc", regex="^(asc|desc)$"),
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """
    Get audit logs with pagination and filtering.
    """
    admin_service = AdminService(db)

    # Check permissions
    if not current_admin.has_permission("read:audit"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view audit logs",
        )

    # Get audit logs
    audit_logs, total = await admin_service.get_audit_logs(
        page=page,
        per_page=per_page,
        search=search,
        action=action,
        resource_type=resource_type,
        admin_id=admin_id,
        success=success,
        date_from=date_from,
        date_to=date_to,
        sort_by=sort_by,
        sort_direction=sort_direction,
    )

    # Format response
    logs_response = []
    for log in audit_logs:
        logs_response.append(
            {
                "id": log.id,
                "admin_id": log.admin_id,
                "admin_username": log.admin.username if log.admin else "System",
                "action": log.action,
                "action_display": log.action_display,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "resource_display": log.resource_display,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "success": log.success,
                "error_message": log.error_message,
                "old_values": log.old_values,
                "new_values": log.new_values,
                "changes_summary": log.get_changes_summary(),
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
        )

    # Calculate pagination info
    pages = (total + per_page - 1) // per_page

    # Add metadata about the audit log fields
    metadata = {
        "fields": {
            "id": {"type": "integer", "nullable": False},
            "admin_id": {"type": "integer", "nullable": True},
            "admin_username": {"type": "string", "nullable": False},
            "action": {"type": "string", "nullable": False},
            "action_display": {"type": "string", "nullable": False},
            "resource_type": {"type": "string", "nullable": False},
            "resource_id": {"type": "integer", "nullable": True},
            "resource_display": {"type": "string", "nullable": False},
            "ip_address": {"type": "string", "nullable": True},
            "user_agent": {"type": "string", "nullable": True},
            "success": {"type": "boolean", "nullable": False},
            "error_message": {"type": "string", "nullable": True},
            "old_values": {"type": "json", "nullable": True},
            "new_values": {"type": "json", "nullable": True},
            "changes_summary": {"type": "string", "nullable": False},
            "created_at": {"type": "datetime", "nullable": False},
        },
        "sortable_fields": [
            "id",
            "admin_username",
            "action",
            "resource_type",
            "ip_address",
            "success",
            "created_at",
        ],
        "filterable_fields": ["action", "resource_type", "admin_id", "success"],
    }

    return {
        "items": logs_response,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": pages,
        "metadata": metadata,
    }


@router.get("/{log_id}")
async def get_audit_log(
    log_id: int,
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """
    Get specific audit log entry by ID.
    """
    admin_service = AdminService(db)

    # Check permissions
    if not current_admin.has_permission("read:audit"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view audit logs",
        )

    # Get audit log
    log = await admin_service.get_audit_log_by_id(log_id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit log not found",
        )

    return {
        "id": log.id,
        "admin_id": log.admin_id,
        "admin_username": log.admin.username if log.admin else "System",
        "action": log.action,
        "action_display": log.action_display,
        "resource_type": log.resource_type,
        "resource_id": log.resource_id,
        "resource_display": log.resource_display,
        "ip_address": log.ip_address,
        "user_agent": log.user_agent,
        "success": log.success,
        "error_message": log.error_message,
        "old_values": log.old_values,
        "new_values": log.new_values,
        "changes_summary": log.get_changes_summary(),
        "created_at": log.created_at.isoformat() if log.created_at else None,
    }


@router.get("/export")
async def export_audit_logs(
    request: Request,
    format: str = Query("csv", regex="^(csv|json)$"),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    action: str | None = Query(None),
    resource_type: str | None = Query(None),
    admin_id: int | None = Query(None),
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Export audit logs to various formats.
    """
    admin_service = AdminService(db)

    # Check permissions
    if not current_admin.has_permission("export:audit"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to export audit logs",
        )

    # Get all audit logs (large limit for export)
    audit_logs, _ = await admin_service.get_audit_logs(
        per_page=100,
        action=action,
        resource_type=resource_type,
        admin_id=admin_id,
        date_from=date_from,
        date_to=date_to,
    )

    # Export data
    from overwatch.utils.export import export_data

    class AuditLogInfo:
        name = "audit_log"

        def get_simple_fields(self):
            return [
                "id",
                "admin_id",
                "admin_username",
                "action",
                "action_display",
                "resource_type",
                "resource_id",
                "resource_display",
                "ip_address",
                "user_agent",
                "success",
                "error_message",
                "created_at",
            ]

    model_info = AuditLogInfo()

    # Convert to dictionaries
    data = []
    for log in audit_logs:
        data.append(
            {
                "id": log.id,
                "admin_id": log.admin_id,
                "admin_username": log.admin.username if log.admin else "System",
                "action": log.action,
                "action_display": log.action_display,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "resource_display": log.resource_display,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "success": log.success,
                "error_message": log.error_message,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
        )

    # Export
    file_path = await export_data(data, format, model_info)

    # Log export action
    await admin_service.log_admin_action(
        admin_id=getattr(current_admin, "id", None),
        action=OverwatchAuditAction.EXPORT,
        resource_type="AuditLog",
        new_values={
            "format": format,
            "count": len(data),
            "filters": {
                "action": action,
                "resource_type": resource_type,
                "admin_id": admin_id,
                "date_from": date_from.isoformat() if date_from else None,
                "date_to": date_to.isoformat() if date_to else None,
            },
        },
        ip_address=admin_service._get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    # Return file
    from fastapi.responses import FileResponse

    return FileResponse(
        file_path,
        media_type="application/octet-stream",
        filename=f"audit_logs_export.{format}",
    )


@router.get("/actions")
async def get_audit_actions(
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """
    Get list of available audit actions.
    """
    admin_service = AdminService(db)

    # Check permissions
    if not current_admin.has_permission("read:audit"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view audit logs",
        )

    # Get available actions
    actions = await admin_service.get_audit_action_counts()

    return {
        "actions": actions,
        "total": len(actions),
    }


@router.get("/resources")
async def get_audit_resources(
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """
    Get list of resources that have audit logs.
    """
    admin_service = AdminService(db)

    # Check permissions
    if not current_admin.has_permission("read:audit"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view audit logs",
        )

    # Get available resources
    resources = await admin_service.get_audit_resource_counts()

    return {
        "resources": resources,
        "total": len(resources),
    }


@router.delete("/cleanup")
async def cleanup_audit_logs(
    request: Request,
    days: int = Query(90, ge=30, le=365),
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """
    Clean up old audit logs (super admin only).
    """
    admin_service = AdminService(db)

    # Check permissions (only super admin can cleanup)
    if current_admin.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admins can cleanup audit logs",
        )

    # Delete old audit logs
    deleted_count = await admin_service.cleanup_old_audit_logs(days=days)

    # Log cleanup action
    await admin_service.log_admin_action(
        admin_id=getattr(current_admin, "id", None),
        action=OverwatchAuditAction.DELETE,
        resource_type="AuditLog",
        new_values={"deleted_count": deleted_count, "days": days},
        ip_address=admin_service._get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    return {
        "message": f"Deleted {deleted_count} audit logs older than {days} days",
        "deleted_count": deleted_count,
        "days": days,
    }
