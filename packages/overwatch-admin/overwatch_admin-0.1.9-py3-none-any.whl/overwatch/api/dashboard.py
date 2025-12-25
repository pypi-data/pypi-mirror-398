"""
Dashboard API endpoints for Overwatch admin panel.
"""

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from overwatch.core.database import get_db_session
from overwatch.models.admin import Admin
from overwatch.schemas.crud import DashboardStatsResponse, HealthCheckResponse
from overwatch.services.dashboard_service import DashboardService

from .auth import get_current_admin_required

router = APIRouter(tags=["Overwatch Dashboard"])


@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db_session),
    current_admin: Admin = Depends(get_current_admin_required),
) -> dict[str, Any]:
    """
    Get dashboard statistics.
    """
    dashboard_service = DashboardService(db)
    return await dashboard_service.get_dashboard_stats()


@router.get("/recent-activity")
async def get_recent_activity(
    limit: int = Query(20, ge=1, le=100),
    action_type: str | None = Query(None),
    resource_type: str | None = Query(None),
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """
    Get recent admin activity.
    """
    from overwatch.services.admin_service import AdminService

    admin_service = AdminService(db)

    # Get recent audit logs
    audit_logs, _ = await admin_service.get_audit_logs(
        limit=limit,
        action=action_type,
        resource_type=resource_type,
    )

    # Format response
    activities = []
    for log in audit_logs:
        activities.append(
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
                "changes_summary": log.get_changes_summary(),
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
        )

    return {
        "activities": activities,
        "total": len(activities),
    }


@router.get("/health", response_model=HealthCheckResponse)
async def health_check(
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    """
    Health check endpoint for monitoring.
    """
    dashboard_service = DashboardService(db)
    return await dashboard_service.get_health_status()


@router.get("/overview")
async def get_dashboard_overview(
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """
    Get comprehensive dashboard overview.
    """
    dashboard_service = DashboardService(db)
    return await dashboard_service.get_dashboard_overview()


@router.get("/metrics")
async def get_dashboard_metrics(
    days: int = Query(30, ge=1, le=365),
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """
    Get dashboard metrics for specified time period.
    """
    dashboard_service = DashboardService(db)
    return await dashboard_service.get_dashboard_metrics(days=days)


@router.get("/models")
async def get_available_models(
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> list[dict[str, Any]]:
    """
    Get list of available models for admin management.
    Uses registered models from OverwatchAdmin with database-agnostic table discovery.
    """
    dashboard_service = DashboardService(db)
    return await dashboard_service.get_available_models()


@router.get("/alerts")
async def get_dashboard_alerts(
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """
    Get system alerts and notifications.
    """
    dashboard_service = DashboardService(db)
    return await dashboard_service.get_dashboard_alerts()
