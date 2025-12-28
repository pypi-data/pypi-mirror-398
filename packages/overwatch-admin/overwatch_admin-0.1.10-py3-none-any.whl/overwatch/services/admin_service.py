"""
Admin service for authentication and user management.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import Request
from passlib.context import CryptContext
from sqlalchemy import String, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from overwatch.models.admin import (
    Admin,
    OverwatchAdminRole,
    OverwatchAdminStatus,
)
from overwatch.models.admin_session import AdminSession
from overwatch.models.audit_log import AuditLog, OverwatchAuditAction


class AdminService:
    """Service for admin authentication and management."""

    def __init__(self, db_session: AsyncSession):
        """
        Initialize admin service.

        Args:
            db_session: Database session
        """
        self.db_session = db_session
        self.pwd_context = CryptContext(
            schemes=["pbkdf2_sha256"],
            deprecated="auto",
            # Explicitly disable deprecated schemes to avoid crypt deprecation warning
            default="pbkdf2_sha256",
        )

    async def authenticate_admin(self, username: str, password: str) -> Admin | None:
        """
        Authenticate admin with username and password.

        Args:
            username: Admin username
            password: Admin password

        Returns:
            Admin object if authentication successful, None otherwise
        """
        # Find admin by username
        result = await self.db_session.execute(
            select(Admin).where(Admin.username == username)
        )
        admin = result.scalar_one_or_none()

        if not admin:
            return None

        # Check if admin can login
        if not admin.can_login:
            return None

        # Verify password
        if not self.pwd_context.verify(password, admin.password_hash):
            await self._record_failed_login(admin)
            return None

        # Reset failed login attempts on successful login
        if admin.failed_login_attempts > 0:
            admin.failed_login_attempts = 0
            admin.locked_until = None
            await self.db_session.commit()

        return admin

    async def create_admin(
        self,
        username: str,
        password: str,
        email: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        role: OverwatchAdminRole = OverwatchAdminRole.ADMIN,
        is_active: bool = True,
        organization_id: int | None = None,
        created_by: int | None = None,
    ) -> Admin:
        """
        Create a new admin.

        Args:
            username: Admin username
            password: Admin password
            email: Admin email
            first_name: Admin first name
            last_name: Admin last name
            role: Admin role
            is_active: Whether admin is active
            created_by: ID of admin who created this admin

        Returns:
            Created admin object
        """
        # Check if username already exists
        existing = await self.db_session.execute(
            select(Admin).where(Admin.username == username)
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Admin with username '{username}' already exists")

        # Check if email already exists
        if email:
            existing_email = await self.db_session.execute(
                select(Admin).where(Admin.email == email)
            )
            if existing_email.scalar_one_or_none():
                raise ValueError(f"Admin with email '{email}' already exists")

        # Validate password
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")

        # Hash password
        password_hash = self.pwd_context.hash(password)

        # Create admin
        admin = Admin(
            username=username,
            email=email,
            password_hash=password_hash,
            first_name=first_name or username,
            last_name=last_name,
            role=role,
            status=OverwatchAdminStatus.ACTIVE
            if is_active
            else OverwatchAdminStatus.INACTIVE,
            is_active=is_active,
            organization_id=organization_id,
            created_by=created_by,
        )

        self.db_session.add(admin)
        await self.db_session.commit()
        await self.db_session.refresh(admin)

        return admin

    async def get_admin_by_id(self, admin_id: int | None) -> Admin | None:
        """
        Get admin by ID.

        Args:
            admin_id: Admin ID

        Returns:
            Admin object or None
        """
        result = await self.db_session.execute(
            select(Admin).options(selectinload(Admin.organization)).where(Admin.id == admin_id)
        )
        return result.scalar_one_or_none()

    async def get_admin_by_username(self, username: str) -> Admin | None:
        """
        Get admin by username.

        Args:
            username: Admin username

        Returns:
            Admin object or None
        """
        result = await self.db_session.execute(
            select(Admin).where(Admin.username == username)
        )
        return result.scalar_one_or_none()

    async def update_admin(
        self,
        admin_id: int | None,
        updates: dict[str, Any],
        updated_by: int | None = None,
    ) -> Admin:
        """
        Update admin.

        Args:
            admin_id: Admin ID
            updates: Dictionary of updates
            updated_by: ID of admin who made the update

        Returns:
            Updated admin object
        """
        admin = await self.get_admin_by_id(admin_id)
        if not admin:
            raise ValueError("Admin not found")

        # Update fields
        for field, value in updates.items():
            if hasattr(admin, field) and field not in ["id", "password_hash"]:
                setattr(admin, field, value)

        admin.updated_by = updated_by
        admin.updated_at = datetime.now(UTC)

        await self.db_session.commit()
        await self.db_session.refresh(admin)

        return admin

    async def delete_admin(self, admin_id: int, deleted_by: int | None = None) -> bool:
        """
        Delete admin.

        Args:
            admin_id: Admin ID
            deleted_by: ID of admin who deleted this admin

        Returns:
            True if deleted, False if not found
        """
        admin = await self.get_admin_by_id(admin_id)
        if not admin:
            return False

        await self.db_session.delete(admin)
        await self.db_session.commit()

        return True

    async def change_admin_password(
        self,
        admin_id: int | None,
        current_password: str | None = None,
        new_password: str | None = None,
        updated_by: int | None = None,
        skip_current_password_validation: bool = False,
    ) -> bool:
        """
        Change admin password.

        Args:
            admin_id: Admin ID
            current_password: Current password (required unless skip_current_password_validation is True)
            new_password: New password
            updated_by: ID of admin who changed the password
            skip_current_password_validation: Whether to skip current password validation (for admin-forced password changes)

        Returns:
            True if password changed successfully
        """
        admin = await self.get_admin_by_id(admin_id)
        if not admin:
            raise ValueError("Admin not found")

        # Validate new password
        if not new_password or len(new_password) < 8:
            raise ValueError("New password must be at least 8 characters long")

        # Validate current password unless explicitly skipped
        if not skip_current_password_validation:
            if not current_password:
                raise ValueError("Current password is required")

            if not self.pwd_context.verify(current_password, admin.password_hash):
                raise ValueError("Current password is incorrect")

        # Update password
        admin.password_hash = self.pwd_context.hash(new_password)
        admin.updated_by = updated_by
        admin.updated_at = datetime.now(UTC)

        await self.db_session.commit()

        return True

    async def create_admin_session(
        self,
        admin: Admin,
        request: Request,
        access_token: str,
        refresh_token: str,
    ) -> AdminSession:
        """
        Create admin session.

        Args:
            admin: Admin object
            request: FastAPI request object
            access_token: JWT access token
            refresh_token: JWT refresh token

        Returns:
            Created admin session
        """
        # Get client info
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent")

        # Create session
        session = AdminSession(
            admin_id=admin.id,
            session_token=access_token,
            refresh_token=refresh_token,
            ip_address=client_ip,
            user_agent=user_agent,
            expires_at=datetime.now(UTC) + timedelta(minutes=30),  # Access token expiry
        )

        self.db_session.add(session)
        await self.db_session.commit()
        await self.db_session.refresh(session)

        return session

    async def get_admin_session(self, session_token: str) -> AdminSession | None:
        """
        Get admin session by token.

        Args:
            session_token: Session token

        Returns:
            Admin session object or None
        """
        result = await self.db_session.execute(
            select(AdminSession).where(
                AdminSession.session_token == session_token, AdminSession.is_active
            )
        )
        return result.scalar_one_or_none()

    async def invalidate_admin_session(self, session_token: str) -> bool:
        """
        Invalidate admin session.

        Args:
            session_token: Session token

        Returns:
            True if session invalidated, False if not found
        """
        session = await self.get_admin_session(session_token)
        if not session:
            return False

        session.is_active = False
        session.terminated_at = datetime.now(UTC)

        await self.db_session.commit()

        return True

    async def get_admin_list(
        self,
        page: int = 1,
        per_page: int = 25,
        search: str | None = None,
        role: OverwatchAdminRole | None = None,
        is_active: bool | None = None,
        organization_id: int | None = None,
        sort_by: str = "created_at",
        sort_direction: str = "desc",
    ) -> tuple[list[Admin], int]:
        """
        Get list of admins with pagination and filtering.

        Args:
            page: Page number
            per_page: Items per page
            search: Search query
            role: Filter by role
            is_active: Filter by active status
            sort_by: Sort field
            sort_direction: Sort direction

        Returns:
            Tuple of (admins list, total count)
        """
        query = select(Admin).options(selectinload(Admin.organization))

        # Apply filters
        if search:
            query = query.where(
                Admin.username.ilike(f"%{search}%")
                | Admin.email.ilike(f"%{search}%")
                | Admin.first_name.ilike(f"%{search}%")
                | Admin.last_name.ilike(f"%{search}%")
            )

        if role:
            query = query.where(Admin.role == role)

        if is_active is not None:
            query = query.where(Admin.is_active == is_active)

        if organization_id is not None:
            query = query.where(Admin.organization_id == organization_id)

        # Get total count
        total_query = select(func.count(Admin.id))
        # Apply the same filters to count query
        if search:
            total_query = total_query.where(
                Admin.username.ilike(f"%{search}%")
                | Admin.email.ilike(f"%{search}%")
                | Admin.first_name.ilike(f"%{search}%")
                | Admin.last_name.ilike(f"%{search}%")
            )

        if role:
            total_query = total_query.where(Admin.role == role)

        if is_active is not None:
            total_query = total_query.where(Admin.is_active == is_active)

        if organization_id is not None:
            total_query = total_query.where(Admin.organization_id == organization_id)

        total_result = await self.db_session.execute(total_query)
        total = total_result.scalar() or 0

        # Apply sorting
        if hasattr(Admin, sort_by):
            # Sort by valid Admin attribute
            if sort_direction == "desc":
                query = query.order_by(getattr(Admin, sort_by).desc())
            else:
                query = query.order_by(getattr(Admin, sort_by).asc())
        else:
            # Fallback to created_at if invalid sort field
            if sort_direction == "desc":
                query = query.order_by(Admin.created_at.desc())
            else:
                query = query.order_by(Admin.created_at.asc())

        # Apply pagination
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)

        # Execute query
        result = await self.db_session.execute(query)
        admins = result.scalars().all()

        return list(admins), total

    async def _record_failed_login(self, admin: Admin) -> None:
        """
        Record failed login attempt and lock account if necessary.

        Args:
            admin: Admin object
        """
        admin.failed_login_attempts += 1

        # Lock account after 5 failed attempts for 15 minutes
        if admin.failed_login_attempts >= 5:
            admin.locked_until = datetime.now(UTC) + timedelta(minutes=15)

        await self.db_session.commit()

    def _get_client_ip(self, request: Request) -> str:
        """
        Get client IP address from request.

        Args:
            request: FastAPI request object

        Returns:
            Client IP address
        """
        # Check for forwarded IP
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        # Check for real IP
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fall back to client IP
        return request.client.host if request.client else "unknown"

    def _serialize_values(self, values: dict[str, Any] | None) -> str | None:
        """
        Serialize values to JSON, handling datetime objects.

        Args:
            values: Dictionary of values to serialize

        Returns:
            JSON string or None
        """
        import json
        from datetime import date, datetime, time

        if not values:
            return None

        def datetime_converter(obj):
            """Convert datetime objects to ISO format strings."""
            if isinstance(obj, (datetime, date, time)):
                return obj.isoformat()
            raise TypeError(
                f"Object of type {type(obj).__name__} is not JSON serializable"
            )

        return json.dumps(values, default=datetime_converter)

    async def log_admin_action(
        self,
        admin_id: int | None,
        action: OverwatchAuditAction,
        resource_type: str,
        resource_id: int | None = None,
        old_values: dict[str, Any] | None = None,
        new_values: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        success: bool = True,
        error_message: str | None = None,
    ) -> AuditLog:
        """
        Log admin action to audit trail.

        Args:
            admin_id: Admin ID
            action: Action performed
            resource_type: Type of resource
            resource_id: ID of specific resource
            old_values: Previous values (for updates)
            new_values: New values
            ip_address: Client IP address
            user_agent: Client user agent
            success: Whether action was successful
            error_message: Error message if failed

        Returns:
            Created audit log entry
        """
        audit_log = AuditLog(
            admin_id=admin_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            old_values=self._serialize_values(old_values),
            new_values=self._serialize_values(new_values),
            success=success,
            error_message=error_message,
        )

        self.db_session.add(audit_log)
        await self.db_session.commit()
        await self.db_session.refresh(audit_log)

        return audit_log

    async def get_admin_count(self) -> int:
        """
        Get total count of admin users.

        Returns:
            Total number of admin users
        """
        result = await self.db_session.execute(select(Admin))
        return len(result.scalars().all())

    async def get_audit_log_count(self) -> int:
        """
        Get total count of audit logs.

        Returns:
            Total number of audit logs
        """
        from overwatch.models.audit_log import AuditLog

        result = await self.db_session.execute(select(AuditLog))
        return len(result.scalars().all())

    async def get_admin_stats(self) -> dict[str, Any]:
        """
        Get admin statistics.

        Returns:
            Dictionary with admin statistics
        """
        # Get total admins
        total = await self.get_admin_count()

        # Get active admins
        active_result = await self.db_session.execute(
            select(Admin).where(Admin.is_active)
        )
        active = len(active_result.scalars().all())

        # Get inactive admins
        inactive_result = await self.db_session.execute(
            select(Admin).where(Admin.is_active.is_(False))
        )
        inactive = len(inactive_result.scalars().all())

        # Get suspended admins
        suspended_result = await self.db_session.execute(
            select(Admin).where(Admin.status == OverwatchAdminStatus.SUSPENDED)
        )
        suspended = len(suspended_result.scalars().all())

        # Get role-based statistics
        all_admins_result = await self.db_session.execute(select(Admin))
        all_admins = all_admins_result.scalars().all()

        super_admin = 0
        admin = 0
        read_only = 0

        for admin_obj in all_admins:
            if admin_obj.role == "super_admin":
                super_admin += 1
            elif admin_obj.role == "admin":
                admin += 1
            elif admin_obj.role == "read_only":
                read_only += 1

        return {
            "total": total,
            "active": active,
            "inactive": inactive,
            "suspended": suspended,
            "super_admin": super_admin,
            "admin": admin,
            "read_only": read_only,
        }

    async def get_recent_audit_logs(self, limit: int = 10) -> list[AuditLog]:
        """
        Get recent audit logs.

        Args:
            limit: Number of logs to return

        Returns:
            List of recent audit logs
        """
        from overwatch.models.audit_log import AuditLog

        result = await self.db_session.execute(
            select(AuditLog)
            .options(selectinload(AuditLog.admin))
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_recent_logins_count(self, hours: int = 24) -> int:
        """
        Get count of recent successful logins.

        Args:
            hours: Number of hours to look back

        Returns:
            Count of recent successful logins
        """
        from overwatch.models.audit_log import AuditLog

        cutoff_time = datetime.now(UTC) - timedelta(hours=hours)

        result = await self.db_session.execute(
            select(AuditLog).where(
                AuditLog.action == OverwatchAuditAction.LOGIN,
                AuditLog.created_at >= cutoff_time,
                AuditLog.success.is_(True),
            )
        )
        return len(result.scalars().all())

    async def get_total_actions_count(self, hours: int = 24) -> int:
        """
        Get count of total actions in specified time period.

        Args:
            hours: Number of hours to look back

        Returns:
            Count of total actions
        """
        from overwatch.models.audit_log import AuditLog

        cutoff_time = datetime.now(UTC) - timedelta(hours=hours)

        result = await self.db_session.execute(
            select(AuditLog).where(AuditLog.created_at >= cutoff_time)
        )
        return len(result.scalars().all())

    async def get_audit_logs(
        self,
        limit: int | None = None,
        page: int = 1,
        per_page: int = 20,
        search: str | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        admin_id: int | None = None,
        success: bool | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        sort_by: str = "created_at",
        sort_direction: str = "desc",
    ) -> tuple[list[AuditLog], int]:
        """
        Get audit logs with pagination and filtering.

        Args:
            page: Page number
            per_page: Items per page
            search: Search query
            action: Filter by action type
            resource_type: Filter by resource type
            admin_id: Filter by admin ID
            success: Filter by success status
            date_from: Filter by start date
            date_to: Filter by end date
            sort_by: Sort field
            sort_direction: Sort direction

        Returns:
            Tuple of (audit logs list, total count)
        """
        from overwatch.models.audit_log import AuditLog

        query = select(AuditLog)

        # Apply filters
        if search:
            query = query.where(
                AuditLog.resource_type.ilike(f"%{search}%")
                | AuditLog.action.cast(String).ilike(f"%{search}%")
            )

        if action:
            query = query.where(AuditLog.action == action)

        if resource_type:
            query = query.where(AuditLog.resource_type == resource_type)

        if admin_id:
            query = query.where(AuditLog.admin_id == admin_id)

        if success is not None:
            query = query.where(AuditLog.success == success)

        if date_from:
            query = query.where(AuditLog.created_at >= date_from)

        if date_to:
            query = query.where(AuditLog.created_at <= date_to)

        count_query = select(func.count(AuditLog.id))

        if search:
            count_query = count_query.where(
                AuditLog.resource_type.ilike(f"%{search}%")
                | AuditLog.action.cast(String).ilike(f"%{search}%")
            )

        if action:
            count_query = count_query.where(AuditLog.action == action)

        if resource_type:
            count_query = count_query.where(AuditLog.resource_type == resource_type)

        if admin_id:
            count_query = count_query.where(AuditLog.admin_id == admin_id)

        if success is not None:
            count_query = count_query.where(AuditLog.success == success)

        if date_from:
            count_query = count_query.where(AuditLog.created_at >= date_from)

        if date_to:
            count_query = count_query.where(AuditLog.created_at <= date_to)

        total_result = await self.db_session.execute(count_query)
        total = total_result.scalar() or 0

        # Apply sorting
        # Handle relationship-based sorting for admin_username
        if sort_by == "admin_username":
            # Join with Admin table and sort by admin.username
            query = query.outerjoin(Admin, AuditLog.admin_id == Admin.id)
            if sort_direction == "desc":
                query = query.order_by(Admin.username.desc())
            else:
                query = query.order_by(Admin.username.asc())
        elif hasattr(AuditLog, sort_by):
            # Sort by direct AuditLog attribute
            if sort_direction == "desc":
                query = query.order_by(getattr(AuditLog, sort_by).desc())
            else:
                query = query.order_by(getattr(AuditLog, sort_by).asc())
        else:
            # Fallback to created_at if invalid sort field
            if sort_direction == "desc":
                query = query.order_by(AuditLog.created_at.desc())
            else:
                query = query.order_by(AuditLog.created_at.asc())

        # Apply pagination (handle limit parameter)
        if limit is not None:
            query = query.limit(limit)
        else:
            offset = (page - 1) * per_page
            query = query.offset(offset).limit(per_page)

        query = query.options(selectinload(AuditLog.admin))

        # Execute query
        result = await self.db_session.execute(query)
        audit_logs = result.scalars().all()

        return list(audit_logs), total

    async def get_activity_trends(self, days: int = 7) -> list[dict[str, Any]]:
        """
        Get activity trends for the specified number of days.

        Args:
            days: Number of days to analyze

        Returns:
            List of daily activity data
        """
        from overwatch.models.audit_log import AuditLog

        trends = []
        cutoff_time = datetime.now(UTC) - timedelta(days=days)

        for i in range(days):
            day_start = cutoff_time + timedelta(days=i)
            day_end = day_start + timedelta(days=1)

            result = await self.db_session.execute(
                select(AuditLog).where(
                    AuditLog.created_at >= day_start, AuditLog.created_at < day_end
                )
            )
            count = len(result.scalars().all())

            trends.append(
                {
                    "date": day_start.strftime("%Y-%m-%d"),
                    "count": count,
                }
            )

        return trends

    async def get_top_resources(self, limit: int = 5) -> list[dict[str, Any]]:
        """
        Get top resources by activity count.

        Args:
            limit: Number of resources to return

        Returns:
            List of top resources
        """
        from sqlalchemy import func

        from overwatch.models.audit_log import AuditLog

        # Group by resource_type and count
        result = await self.db_session.execute(
            select(AuditLog.resource_type, func.count(AuditLog.id).label("count"))
            .group_by(AuditLog.resource_type)
            .order_by(func.count(AuditLog.id).desc())
            .limit(limit)
        )

        return [
            {"resource_type": row.resource_type, "count": row.count}
            for row in result.all()
        ]

    async def get_dashboard_metrics(self, days: int = 30) -> dict[str, Any]:
        """
        Get dashboard metrics for the specified time period.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with dashboard metrics
        """
        cutoff_time = datetime.now(UTC) - timedelta(days=days)

        # Get total actions
        total_actions = await self.get_total_actions_count(hours=days * 24)

        # Get successful vs failed actions
        from overwatch.models.audit_log import AuditLog

        successful_result = await self.db_session.execute(
            select(AuditLog).where(
                AuditLog.created_at >= cutoff_time,
                AuditLog.success,
            )
        )
        successful = len(successful_result.scalars().all())

        failed_result = await self.db_session.execute(
            select(AuditLog).where(
                AuditLog.created_at >= cutoff_time,
                AuditLog.success.is_(False),
            )
        )
        failed = len(failed_result.scalars().all())

        # Get top actions
        actions_result = await self.db_session.execute(
            select(AuditLog.action, func.count(AuditLog.id).label("count"))
            .where(AuditLog.created_at >= cutoff_time)
            .group_by(AuditLog.action)
            .order_by(func.count(AuditLog.id).desc())
            .limit(10)
        )

        top_actions = [
            {"action": row.action, "count": row.count} for row in actions_result.all()
        ]

        return {
            "total_actions": total_actions,
            "successful_actions": successful,
            "failed_actions": failed,
            "success_rate": (successful / total_actions * 100)
            if total_actions > 0
            else 0,
            "top_actions": top_actions,
            "period_days": days,
        }

    async def get_recent_failed_logins(self, hours: int = 24) -> int:
        """
        Get count of recent failed login attempts.

        Args:
            hours: Number of hours to look back

        Returns:
            Count of failed login attempts
        """
        from overwatch.models.audit_log import AuditLog

        cutoff_time = datetime.now(UTC) - timedelta(hours=hours)

        result = await self.db_session.execute(
            select(AuditLog).where(
                AuditLog.action == OverwatchAuditAction.LOGIN,
                AuditLog.created_at >= cutoff_time,
                AuditLog.success.is_(False),
            )
        )
        return len(result.scalars().all())

    async def get_inactive_admins(self, days: int = 30) -> int:
        """
        Get count of inactive admin users.

        Args:
            days: Number of days of inactivity

        Returns:
            Count of inactive admins
        """
        cutoff_time = datetime.now(UTC) - timedelta(days=days)

        result = await self.db_session.execute(
            select(AdminSession.admin_id)
            .where(AdminSession.created_at >= cutoff_time)
            .distinct()
        )

        active_admin_ids = {row.admin_id for row in result.all()}

        # Get all admin IDs
        all_admins_result = await self.db_session.execute(select(Admin.id))
        all_admin_ids = {row.id for row in all_admins_result.all()}

        # Inactive admins are those not in the active set
        inactive_admin_ids = all_admin_ids - active_admin_ids
        return len(inactive_admin_ids)

    async def get_recent_system_errors(self, hours: int = 24) -> int:
        """
        Get count of recent system errors.

        Args:
            hours: Number of hours to look back

        Returns:
            Count of system errors
        """
        from overwatch.models.audit_log import AuditLog

        cutoff_time = datetime.now(UTC) - timedelta(hours=hours)

        result = await self.db_session.execute(
            select(AuditLog).where(
                AuditLog.created_at >= cutoff_time,
                AuditLog.success.is_(False),
                AuditLog.error_message.isnot(None),
            )
        )
        return len(result.scalars().all())

    async def check_database_health(self) -> bool:
        """
        Check database connectivity and health.

        Returns:
            True if database is healthy
        """
        try:
            # Simple query to test connection
            await self.db_session.execute(select(Admin).limit(1))
            return True
        except Exception:
            return False

    async def get_audit_log_by_id(self, log_id: int) -> AuditLog | None:
        """
        Get audit log by ID.

        Args:
            log_id: Audit log ID

        Returns:
            Audit log object or None
        """
        from overwatch.models.audit_log import AuditLog

        result = await self.db_session.execute(
            select(AuditLog).where(AuditLog.id == log_id)
        )
        return result.scalar_one_or_none()

    async def get_audit_action_counts(self) -> list[dict[str, Any]]:
        """
        Get counts of audit logs grouped by action type.

        Returns:
            List of action counts
        """
        from sqlalchemy import func

        from overwatch.models.audit_log import AuditLog

        result = await self.db_session.execute(
            select(AuditLog.action, func.count(AuditLog.id).label("count"))
            .group_by(AuditLog.action)
            .order_by(func.count(AuditLog.id).desc())
        )

        return [{"action": row.action, "count": row.count} for row in result.all()]

    async def get_audit_resource_counts(self) -> list[dict[str, Any]]:
        """
        Get counts of audit logs grouped by resource type.

        Returns:
            List of resource counts
        """
        from sqlalchemy import func

        from overwatch.models.audit_log import AuditLog

        result = await self.db_session.execute(
            select(AuditLog.resource_type, func.count(AuditLog.id).label("count"))
            .group_by(AuditLog.resource_type)
            .order_by(func.count(AuditLog.id).desc())
        )

        return [
            {"resource_type": row.resource_type, "count": row.count}
            for row in result.all()
        ]

    async def get_audit_statistics(self, days: int = 30) -> dict[str, Any]:
        """
        Get audit log statistics for the specified time period.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with audit statistics
        """
        from sqlalchemy import func

        from overwatch.models.audit_log import AuditLog

        cutoff_time = datetime.now(UTC) - timedelta(days=days)

        # Get total audit logs in period
        total_result = await self.db_session.execute(
            select(func.count(AuditLog.id)).where(AuditLog.created_at >= cutoff_time)
        )
        total = total_result.scalar() or 0

        # Get successful vs failed actions
        successful_result = await self.db_session.execute(
            select(func.count(AuditLog.id)).where(
                AuditLog.created_at >= cutoff_time,
                AuditLog.success.is_(True),
            )
        )
        successful = successful_result.scalar() or 0

        failed_result = await self.db_session.execute(
            select(func.count(AuditLog.id)).where(
                AuditLog.created_at >= cutoff_time,
                AuditLog.success.is_(False),
            )
        )
        failed = failed_result.scalar() or 0

        # Get top actions
        top_actions_result = await self.db_session.execute(
            select(AuditLog.action, func.count(AuditLog.id).label("count"))
            .where(AuditLog.created_at >= cutoff_time)
            .group_by(AuditLog.action)
            .order_by(func.count(AuditLog.id).desc())
            .limit(10)
        )

        top_actions = [
            {"action": row.action, "count": row.count}
            for row in top_actions_result.all()
        ]

        # Get top resources
        top_resources_result = await self.db_session.execute(
            select(AuditLog.resource_type, func.count(AuditLog.id).label("count"))
            .where(AuditLog.created_at >= cutoff_time)
            .group_by(AuditLog.resource_type)
            .order_by(func.count(AuditLog.id).desc())
            .limit(10)
        )

        top_resources = [
            {"resource_type": row.resource_type, "count": row.count}
            for row in top_resources_result.all()
        ]

        # Get daily activity trends
        daily_trends = []
        for i in range(days):
            day_start = cutoff_time + timedelta(days=i)
            day_end = day_start + timedelta(days=1)

            day_result = await self.db_session.execute(
                select(func.count(AuditLog.id)).where(
                    AuditLog.created_at >= day_start, AuditLog.created_at < day_end
                )
            )
            day_count = day_result.scalar() or 0

            daily_trends.append(
                {"date": day_start.strftime("%Y-%m-%d"), "count": day_count}
            )

        return {
            "total_logs": total,
            "successful_actions": successful,
            "failed_actions": failed,
            "success_rate": (successful / total * 100) if total > 0 else 0,
            "top_actions": top_actions,
            "top_resources": top_resources,
            "daily_trends": daily_trends,
            "period_days": days,
        }

    async def cleanup_old_audit_logs(self, days: int = 90) -> int:
        """
        Clean up audit logs older than specified number of days.

        Args:
            days: Number of days to keep logs (older logs will be deleted)

        Returns:
            Number of deleted audit logs
        """
        from overwatch.models.audit_log import AuditLog

        cutoff_time = datetime.now(UTC) - timedelta(days=days)

        # Get count of logs to be deleted
        count_result = await self.db_session.execute(
            select(func.count(AuditLog.id)).where(AuditLog.created_at < cutoff_time)
        )
        delete_count = count_result.scalar() or 0

        if delete_count > 0:
            # Delete old logs
            from sqlalchemy import delete

            delete_stmt = delete(AuditLog).where(AuditLog.created_at < cutoff_time)
            await self.db_session.execute(delete_stmt)
            await self.db_session.commit()

        return delete_count
