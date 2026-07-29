# Bus Ticket API

Bus Ticket API သည် FastAPI အခြေခံပြီး PostgreSQL, Redis, Celery, JWT Authentication, Role-Based Access Control (RBAC) နှင့် Admin Panel ကို ပေါင်းထည့်ထားသော Backend Service ဖြစ်ပါတယ်။

## Project Overview

ဒီ Project ကို Bus Ticket Booking System အတွက် API Layer အနေနဲ့ အသုံးပြုနိုင်ပြီး အဓိက လုပ်ဆောင်ချက်များမှာ-

- User Authentication နှင့် Authorization
- Role / Permission Management
- Admin Dashboard Integration
- Database Migration Support
- Async Database Connection
- Redis based task queue / background jobs

## Tech Stack

- Python 3.11+
- FastAPI
- SQLAlchemy
- PostgreSQL
- Redis
- Celery
- Alembic
- Pydantic
- Docker / Docker Compose

## Project Folder Structure

```text
bus-ticket-api/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── auth.py
│   │   │   │   ├── permissions.py
│   │   │   │   ├── roles.py
│   │   │   │   └── users.py
│   │   │   ├── router.py
│   │   │   └── __init__.py
│   │   ├── deps.py
│   │   └── __init__.py
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── redis_client.py
│   │   ├── rbac.py
│   │   ├── security.py
│   │   └── __init__.py
│   ├── models/
│   │   ├── base.py
│   │   ├── permission.py
│   │   ├── role.py
│   │   ├── role_permission.py
│   │   ├── user.py
│   │   ├── user_role.py
│   │   └── __init__.py
│   ├── repositories/
│   │   ├── base_repository.py
│   │   ├── user_repository.py
│   │   └── __init__.py
│   ├── schemas/
│   │   ├── permission.py
│   │   ├── role.py
│   │   ├── user.py
│   │   └── __init__.py
│   ├── services/
│   │   ├── permission_service.py
│   │   ├── role_service.py
│   │   ├── user_service.py
│   │   └── __init__.py
│   ├── tasks/
│   │   ├── celery_app.py
│   │   └── __init__.py
│   ├── utils/
│   │   ├── logger.py
│   │   └── __init__.py
│   ├── admin.py
│   ├── main.py
│   └── __init__.py
├── migrations/
│   └── versions/
├── docker/
│   ├── Dockerfile
│   └── nginx/
│       └── nginx.conf
├── scripts/
│   └── entrypoint.sh
├── tests/
├── alembic.ini
├── docker-compose.yml
├── Makefile
├── requirements.txt
└── README.md
```

## Project Documentation

### 1. Application Structure

- app/main.py
  - FastAPI application entrypoint
  - Middleware, router registration, startup/shutdown events
- app/api/
  - API routing and endpoint definitions
  - Versioned routing under v1
- app/core/
  - Shared application configuration, security helpers, DB and Redis connections
- app/models/
  - SQLAlchemy ORM models for users, roles, permissions and associations
- app/schemas/
  - Pydantic request/response models
- app/services/
  - Business logic layer
- app/repositories/
  - Data access layer for database operations
- app/tasks/
  - Celery background job setup

### 2. Request Flow

1. Client sends request to FastAPI endpoint
2. Router forwards request to corresponding endpoint
3. Service layer handles business logic
4. Repository layer interacts with database
5. Response is returned as JSON schema defined in Pydantic models

### 3. Authentication and Authorization

- JWT-based authentication support is included in the core security layer
- RBAC logic is handled through role and permission modules
- Protected routes can be enforced through dependency-based access control

### 4. Database & Migrations

- PostgreSQL is used as the primary database
- Alembic is used for migrations
- Migration files are stored under migrations/versions

### 5. Environment Configuration

Project အတွက် required environment variables အများစုကို .env file မှာ သတ်မှတ်ရပါမယ်။

Core variables include:

- DATABASE_URL
- SECRET_KEY
- POSTGRES_USER
- POSTGRES_PASSWORD
- POSTGRES_DB
- REDIS_URL
- SMTP_HOST / SMTP_USER / SMTP_PASSWORD

## Setup Instructions

### Prerequisites

- Python 3.11+
- PostgreSQL
- Redis
- Docker (optional)

### Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run Application

```bash
uvicorn app.main:app --reload
```

### Run with Docker

```bash
docker-compose up --build
```

### Run Migrations

```bash
alembic upgrade head
```

### Run Tests

```bash
pytest
```

## API Documentation

Development environment မှာ API documentation ကို ဒီ URL မှာ ကြည့်နိုင်ပါတယ်:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Notes

- This project is structured with clear separation between API, service, repository, and model layers.
- For new features, follow the existing pattern: endpoint -> service -> repository -> model.
- Keep business rules in services and database access in repositories.
