"""
Dashboard service for Overwatch admin panel statistics and metrics.
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncSession

from overwatch.core.database import get_database_manager
from overwatch.services.admin_service import AdminService


class DashboardService:
    """Service for dashboard statistics and metrics."""

    def __init__(self, db_session: AsyncSession):
        """
        Initialize dashboard service.

        Args:
            db_session: Database session
        """
        self.db_session = db_session
        self.admin_service = AdminService(db_session)

    async def get_dashboard_stats(self) -> dict[str, Any]:
        """
        Get comprehensive dashboard statistics.

        Returns:
            Dictionary with dashboard statistics
        """
        # Get basic admin stats
        admin_stats = await self.admin_service.get_admin_stats()

        # Get model statistics
        models, total_records = await self._get_model_statistics()

        system_stats = {
            "total_admins": admin_stats["total"],
            "active_admins": admin_stats["active"],
            "recent_logins": await self.admin_service.get_recent_logins_count(hours=24),
            "total_actions": await self.admin_service.get_total_actions_count(hours=24),
        }

        return {
            "total_models": len(models),
            "total_records": total_records,
            "system_stats": system_stats,
        }

    async def get_available_models(self) -> list[dict[str, Any]]:
        """
        Get list of available models for admin management.

        Returns:
            List of model information with counts
        """
        return await self._get_models_list()

    async def _get_model_statistics(
        self,
    ) -> tuple[list[dict[str, Any]], dict[str, int]]:
        """
        Get model statistics from database.

        Returns:
            Tuple of (models list, total_records dict)
        """
        models = []
        total_records = {}

        # Test database connection
        try:
            test_result = await self.db_session.execute(text("SELECT 1"))
            test_value = test_result.scalar()
            if test_value != 1:
                return models, total_records
        except Exception:
            return models, total_records

        # Get database-agnostic table names using SQLAlchemy inspector
        tables = await self._get_database_tables()

        # Filter out system tables and create model entries
        for table_name in tables:
            if self._should_skip_table(table_name):
                continue

            try:
                # Get count for this table
                count_result = await self.db_session.execute(
                    text(f"SELECT COUNT(*) FROM {table_name}")
                )
                count = count_result.scalar()

                # Convert table name to model name
                model_name = self._table_to_model_name(table_name)

                model_info = {
                    "name": model_name.lower(),
                    "label": self._model_name_to_label(model_name),
                    "count": count,
                }

                models.append(model_info)
                total_records[model_name.lower()] = count or 0

            except Exception:
                continue

        return models, total_records

    async def _get_models_list(self) -> list[dict[str, Any]]:
        """
        Get list of models with their information.

        Returns:
            List of model information
        """
        # Test database connection
        try:
            test_result = await self.db_session.execute(text("SELECT 1"))
            test_value = test_result.scalar()
            if test_value != 1:
                return [
                    {
                        "name": "example",
                        "label": "Database Connection Error",
                        "count": 0,
                    }
                ]
        except Exception:
            return [
                {"name": "example", "label": "Database Connection Error", "count": 0}
            ]

        # Get database-agnostic table names using SQLAlchemy inspector
        tables = await self._get_database_tables()

        # Filter out system tables and create model entries
        models = []
        for table_name in tables:
            if self._should_skip_table(table_name):
                continue

            try:
                # Get count for this table
                count_result = await self.db_session.execute(
                    text(f"SELECT COUNT(*) FROM {table_name}")
                )
                count = count_result.scalar()

                # Convert table name to model name
                model_name = self._table_to_model_name(table_name)
                label = self._model_name_to_label(model_name)

                models.append(
                    {
                        "name": model_name.lower(),
                        "label": label,
                        "count": count,
                    }
                )
            except Exception:
                continue

        models.sort(key=lambda x: x["name"])
        return models

    async def _get_database_tables(self) -> list[str]:
        """
        Get list of database tables using SQLAlchemy inspector.

        Returns:
            List of table names
        """
        tables = []

        def _get_tables_with_inspector(connection):
            """Helper function to get tables using inspector within run_sync."""
            inspector = inspect(connection)
            if inspector is not None:
                return inspector.get_table_names()
            return []

        try:
            # Use run_sync to get tables from the current connection
            tables = await self.db_session.run_sync(_get_tables_with_inspector)
        except Exception:
            # Fallback to database manager
            try:
                db_manager = get_database_manager()
                if hasattr(db_manager, "engine") and db_manager.engine is not None:
                    async with db_manager.engine.connect() as conn:
                        tables = await conn.run_sync(_get_tables_with_inspector)
            except Exception:
                tables = []

        return tables

    def _should_skip_table(self, table_name: str) -> bool:
        """
        Check if a table should be skipped based on naming patterns.

        Args:
            table_name: Database table name

        Returns:
            True if table should be skipped
        """
        # Skip only Overwatch internal tables and known system tables
        # Keep real application model tables
        table_lower = table_name.lower()
        return (
            table_lower.startswith("overwatch_")
            or table_lower.startswith("sqlite_")
            or "alembic" in table_lower
            or table_lower.startswith("information_schema")
            or table_lower.startswith("pg_")
            or table_lower.startswith("mysql_")
            or table_lower.startswith("performance_schema")
        )

    def _table_to_model_name(self, table_name: str) -> str:
        """
        Convert table name to model name (singular form) using kebab-case.

        Args:
            table_name: Database table name

        Returns:
            Model name in singular form using kebab-case
        """
        # Remove common suffixes and convert to singular
        name = table_name.lower()

        # Handle common plural endings
        if name.endswith("ies"):
            name = name[:-3] + "y"  # category -> categories -> category
        elif name.endswith("es"):
            name = name[:-2]  # boxes -> box
        elif name.endswith("s"):
            name = name[:-1]  # users -> user

        # Convert underscores to hyphens for kebab-case
        name = name.replace("_", "-")

        return name

    def _model_name_to_label(self, model_name: str) -> str:
        """
        Convert model name to display label.

        Args:
            model_name: Model name in singular form (kebab-case)

        Returns:
            Human-readable label
        """
        # Convert kebab-case to Title Case and make plural
        label = model_name.replace("-", " ").title()

        # Add 's' for plural form (simple heuristic)
        if not label.endswith("s") and not label.endswith("y"):
            label += "s"
        elif label.endswith("y"):
            label = label[:-1] + "ies"

        return label

    async def get_health_status(self) -> dict[str, str]:
        """
        Get system health status.

        Returns:
            Health status information
        """
        # Check database connection
        try:
            await self.admin_service.check_database_health()
            database_status = "healthy"
        except Exception:
            database_status = "unhealthy"

        return {
            "status": "healthy" if database_status == "healthy" else "degraded",
            "database": database_status,
            "timestamp": datetime.now(UTC).isoformat(),
            "version": "0.1.0",  # This should come from __init__.py
        }

    async def get_dashboard_overview(self) -> dict[str, Any]:
        """
        Get comprehensive dashboard overview.

        Returns:
            Dashboard overview data
        """
        # Get various statistics
        admin_stats = await self.admin_service.get_admin_stats()
        recent_actions = await self.admin_service.get_recent_audit_logs(limit=5)

        # Get activity trends (last 7 days)
        activity_trends = await self.admin_service.get_activity_trends(days=7)

        # Get top resources by activity
        top_resources = await self.admin_service.get_top_resources(limit=5)

        return {
            "summary": {
                "total_admins": admin_stats["total"],
                "active_admins": admin_stats["active"],
                "inactive_admins": admin_stats["inactive"],
                "suspended_admins": admin_stats["suspended"],
            },
            "recent_actions": [
                {
                    "id": action.id,
                    "admin_username": action.admin.username
                    if action.admin
                    else "System",
                    "action": action.action,
                    "action_display": action.action_display,
                    "resource_type": action.resource_type,
                    "resource_display": action.resource_display,
                    "success": action.success,
                    "created_at": action.created_at.isoformat()
                    if action.created_at
                    else None,
                }
                for action in recent_actions
            ],
            "activity_trends": activity_trends,
            "top_resources": top_resources,
        }

    async def get_dashboard_metrics(self, days: int = 30) -> dict[str, Any]:
        """
        Get dashboard metrics for the specified time period.

        Args:
            days: Number of days to analyze

        Returns:
            Dashboard metrics
        """
        return await self.admin_service.get_dashboard_metrics(days=days)

    async def get_dashboard_alerts(self) -> dict[str, Any]:
        """
        Get system alerts and notifications.

        Returns:
            System alerts
        """
        alerts = []

        # Check for failed login attempts
        failed_logins = await self.admin_service.get_recent_failed_logins(hours=24)
        if failed_logins > 10:
            alerts.append(
                {
                    "type": "security",
                    "severity": "warning",
                    "title": "High Failed Login Attempts",
                    "message": f"{failed_logins} failed login attempts in the last 24 hours",
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )

        # Check for inactive admins
        inactive_admins = await self.admin_service.get_inactive_admins(days=30)
        if inactive_admins > 0:
            alerts.append(
                {
                    "type": "admin",
                    "severity": "info",
                    "title": "Inactive Admins",
                    "message": f"{inactive_admins} admin users haven't logged in for 30 days",
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )

        # Check for system errors
        system_errors = await self.admin_service.get_recent_system_errors(hours=24)
        if system_errors > 0:
            alerts.append(
                {
                    "type": "system",
                    "severity": "error",
                    "title": "System Errors",
                    "message": f"{system_errors} system errors in the last 24 hours",
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )

        return {
            "alerts": alerts,
            "total": len(alerts),
        }
