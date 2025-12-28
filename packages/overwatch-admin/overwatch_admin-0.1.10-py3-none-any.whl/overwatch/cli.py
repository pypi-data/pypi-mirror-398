"""
Command Line Interface for Overwatch admin panel.
"""

import asyncio
from pathlib import Path

import click
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from overwatch.core.config import OverwatchConfig


@click.group()
@click.version_option(version="0.1.10")
def main() -> None:
    """Overwatch Admin Panel CLI."""
    pass


@main.command()
@click.option("--database-url", "-d", help="Database URL")
@click.option("--admin-username", "-u", default="admin", help="Admin username")
@click.option("--admin-email", "-e", default="admin@example.com", help="Admin email")
@click.option("--admin-password", "-p", default="admin123", help="Admin password")
@click.option("--config", "-c", type=click.Path(exists=True), help="Config file path")
def init(
    database_url: str | None,
    admin_username: str,
    admin_email: str,
    admin_password: str,
    config: str | None,
) -> None:
    """Initialize Overwatch admin panel."""

    async def _init() -> None:
        # Load configuration
        if config:
            import json

            with open(config) as f:
                config_data = json.load(f)
            overwatch_config = OverwatchConfig(**config_data)
        else:
            overwatch_config = OverwatchConfig()

        # Use provided database URL or config
        db_url = database_url or overwatch_config.database.url
        if not db_url:
            click.echo("Error: Database URL is required")
            return

        # Initialize database
        from overwatch.core.database import initialize_database

        db_manager = await initialize_database(db_url)

        # Create tables
        await db_manager.create_tables()
        click.echo("✓ Created Overwatch tables")

        # Create admin user
        from overwatch.services.admin_service import AdminService

        async for db in db_manager.get_session():
            admin_service = AdminService(db)

            try:
                admin = await admin_service.create_admin(
                    username=admin_username,
                    password=admin_password,
                    email=admin_email,
                    first_name="Super",
                    last_name="Admin",
                )
                click.echo(f"✓ Created admin user: {admin.username}")
                click.echo(f"  Email: {admin.email}")
                click.echo(f"  Password: {admin_password}")
                click.echo("⚠️  Change the password in production!")
            except Exception as e:
                click.echo(f"✗ Failed to create admin: {e}")

    asyncio.run(_init())


@main.command()
@click.option("--database-url", "-d", help="Database URL")
@click.option("--models", "-m", multiple=True, help="Model files to inspect")
def inspect(database_url: str, models: tuple[str, ...]) -> None:
    """Inspect SQLAlchemy models."""

    async def _inspect() -> None:
        if not database_url:
            click.echo("Error: Database URL is required")
            return

        # Initialize database connection
        engine = create_async_engine(database_url)
        async_session = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session() as db:
            from overwatch.services.introspection import ModelIntrospector

            introspector = ModelIntrospector(db)

            # Import models from specified files
            model_classes = []
            for model_file in models:
                try:
                    # This is a simplified approach - in real usage, you'd
                    # need proper module loading and model discovery
                    click.echo(f"Loading models from {model_file}")
                    # TODO: Implement proper model loading
                except Exception as e:
                    click.echo(f"Error loading {model_file}: {e}")

            if model_classes:
                models_info = await introspector.inspect_models(model_classes)

                for model_name, model_info in models_info.items():
                    click.echo(f"\n📋 Model: {model_name}")
                    click.echo(f"   Table: {model_info.table_name}")
                    click.echo(f"   Fields: {len(model_info.fields)}")
                    click.echo(f"   Relationships: {len(model_info.relationships)}")

                    if model_info.fields:
                        click.echo("\n   Fields:")
                        for field_name, field_info in model_info.fields.items():
                            click.echo(
                                f"     - {field_name} ({field_info.type_name})"
                                f"{' (PK)' if field_info.is_primary_key else ''}"
                                f"{' (FK)' if field_info.is_foreign_key else ''}"
                                f"{' nullable' if field_info.is_nullable else ' required'}"
                            )

                    if model_info.relationships:
                        click.echo("\n   Relationships:")
                        for rel_name, rel_info in model_info.relationships.items():
                            click.echo(
                                f"     - {rel_name} -> {rel_info.target_model} "
                                f"({rel_info.direction})"
                            )
            else:
                click.echo("No models to inspect")

    asyncio.run(_inspect())


@main.command()
@click.option("--database-url", "-d", help="Database URL")
@click.option("--output", "-o", default="overwatch-config.json", help="Output file")
def generate_config(database_url: str, output: str) -> None:
    """Generate a sample configuration file."""

    config = OverwatchConfig(
        admin_title="My Admin Panel",
        database={"url": database_url} if database_url else None,
        security={
            "secret_key": "your-secret-key-change-in-production",
            "access_token_expire_minutes": 30,
            "refresh_token_expire_days": 7,
            "password_min_length": 8,
        },
        theme={
            "primary_color": "#3b82f6",
            "secondary_color": "#64748b",
            "mode": "light",
            "font_family": "Inter, system-ui, sans-serif",
        },
        per_page=25,
        enable_audit_log=True,
        enable_dashboard=True,
        enable_bulk_operations=True,
        enable_export=True,
        cors_origins=["http://localhost:3000"],
    )

    import json

    with open(output, "w") as f:
        json.dump(config.model_dump(), f, indent=2, default=str)

    click.echo(f"✓ Generated configuration file: {output}")


@main.command()
@click.option("--database-url", "-d", help="Database URL")
@click.option("--limit", "-l", default=10, help="Number of recent logs to show")
def logs(database_url: str, limit: int) -> None:
    """Show recent audit logs."""

    async def _logs() -> None:
        if not database_url:
            click.echo("Error: Database URL is required")
            return

        # Initialize database connection
        engine = create_async_engine(database_url)
        async_session = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session() as db:
            from overwatch.models.audit_log import AuditLog

            result = await db.execute(
                select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
            )
            audit_logs = result.scalars().all()

            if not audit_logs:
                click.echo("No audit logs found")
                return

            click.echo(f"\n📊 Recent {len(audit_logs)} audit logs:\n")

            for log in audit_logs:
                status_icon = "✓" if log.success else "✗"
                click.echo(f"{status_icon} {log.created_at} - {log.action_display}")
                click.echo(f"   Resource: {log.resource_display}")
                if log.admin_id:
                    click.echo(f"   Admin ID: {log.admin_id}")
                if log.ip_address:
                    click.echo(f"   IP: {log.ip_address}")
                if log.error_message:
                    click.echo(f"   Error: {log.error_message}")
                click.echo()

    asyncio.run(_logs())


@main.command()
@click.option("--database-url", "-d", help="Database URL")
@click.option("--output", "-o", default="./overwatch-static", help="Output directory")
def export_static(database_url: str, output: str) -> None:
    """Export static frontend files."""

    output_path = Path(output)
    output_path.mkdir(exist_ok=True)

    # This would export the frontend files
    # For now, just create a placeholder
    index_html = """<!DOCTYPE html>
<html>
<head>
    <title>Overwatch Admin</title>
</head>
<body>
    <h1>Overwatch Admin Panel</h1>
    <p>Frontend files would be exported here.</p>
    <p>In a full implementation, this would include the TypeScript/Medusa UI frontend.</p>
</body>
</html>
"""

    (output_path / "index.html").write_text(index_html)

    click.echo(f"✓ Exported static files to: {output}")
    click.echo("📝 Note: This is a placeholder. Full frontend implementation pending.")


@main.command()
def version() -> None:
    """Show Overwatch version."""
    click.echo("Overwatch Admin Panel v0.1.0")
    click.echo("Agnostic admin panel for FastAPI applications")


if __name__ == "__main__":
    main()
