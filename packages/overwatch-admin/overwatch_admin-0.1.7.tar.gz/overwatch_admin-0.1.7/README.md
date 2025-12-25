# Overwatch - Admin Panel for FastAPI

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-red.svg)](https://sqlalchemy.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Overwatch is a reusable, admin panel package for FastAPI applications that automatically generates CRUD interfaces for SQLAlchemy models. It provides an Admin experience with enhanced features including audit logging, permissions, and a modern TypeScript frontend.

## ✨ Features

- **🔧 Model Agnostic**: Works with any SQLAlchemy model
- **🎨 Modern UI**: TypeScript frontend with Modern components
- **🔐 Authentication**: Secure JWT-based authentication system
- **👥 Role Management**: Hierarchical roles with fine-grained permissions
- **📊 Audit Logging**: Complete audit trail of all admin actions
- **🔍 Search & Filter**: Advanced search and filtering capabilities
- **📄 Pagination**: Efficient pagination for large datasets
- **🚀 Performance**: Async operations and optimized queries

## 🚀 Quick Start

### Installation

```bash
pip install overwatch-admin
```

### Basic Usage

```python
from fastapi import FastAPI
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from overwatch import OverwatchAdmin, OverwatchConfig

# Create FastAPI app
app = FastAPI()

# Define your models
Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True)
    email = Column(String(100))

# Initialize Overwatch admin
admin = OverwatchAdmin(
    app=app,
    db_session=get_db_session,  # Your database session dependency
    models=[User],  # Your SQLAlchemy models
    admin_title="My Admin Panel"
)

# Configure model display
admin.configure_model(
    User,
    list_fields=["id", "username", "email"],
    search_fields=["username", "email"],
)

app.run()
```

## 📋 Requirements

- Python 3.11+
- FastAPI 0.104+
- SQLAlchemy 2.0+
- Async database driver (asyncpg, aiosqlite, etc.)

## ⚙️ Configuration

Overwatch can be configured through environment variables or direct configuration:

```python
from overwatch import OverwatchConfig
from overwatch.core.config import SecurityConfig

config = OverwatchConfig(
    admin_title="My Admin Panel",
    security=SecurityConfig(
        secret_key="your-secret-key",
        access_token_expire_minutes=30,
        password_min_length=8,
    ),
    per_page=25,
    enable_audit_log=True,
    enable_dashboard=True,
    cors_origins=["http://localhost:3000"],
)
```

### Environment Variables

```bash
OVERWATCH_ADMIN_TITLE="My Admin Panel"
OVERWATCH_SECURITY__SECRET_KEY="your-secret-key"
OVERWATCH_SECURITY__ACCESS_TOKEN_EXPIRE_MINUTES=30
OVERWATCH_PER_PAGE=25
OVERWATCH_ENABLE_AUDIT_LOG=true
```

## 🔐 Authentication & Authorization

### Built-in Authentication

Overwatch comes with a complete authentication system separate from your application's user system:

```python
# Create admin user
admin = await admin.create_admin(
    username="superadmin",
    password="secure-password",
    email="admin@example.com",
    role="super_admin"
)
```

### Roles & Permissions

- **Super Admin**: Full access to all resources
- **Admin**: Standard CRUD operations
- **Read Only**: View-only access

## 🔧 Advanced Usage

### Custom Database

Overwatch can use a separate database:

```python
config = OverwatchConfig(
    database={
        "url": "postgresql+asyncpg://overwatch:password@localhost/overwatch_db",
        "echo": False
    }
)
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **FastAPI** - The web framework that makes Overwatch possible
- **SQLAlchemy** - Powerful ORM for database operations
- **Pydantic** - Data validation and settings management

## 📞 Support

- 📖 [Documentation](https://overwatch.readthedocs.io)
- 🐛 [Issue Tracker](https://github.com/u3n-ai/overwatch/issues)
- 📧 [Email](mailto:yashdiq@lubis.dev)

---

**Overwatch** - Making admin panels in FastAPI simple and beautiful. 🚀
