bus-ticket-api/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── __init__.py
│   │   │   │   └── auth.py
│   │   │   ├── __init__.py
│   │   │   └── router.py
│   │   ├── __init__.py
│   │   └── deps.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── database.py
│   │   └── redis_client.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── base.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── user.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── base_repository.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── user_service.py
│   ├── utils/
│   │   ├── __init__.py
│   │   └── logger.py
│   ├── tasks/
│   │   ├── __init__.py
│   │   └── celery_app.py
│   ├── main.py
│   └── __init__.py
├── migrations/
│   └── versions/
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_user.py
├── docker/
│   ├── Dockerfile
│   └── nginx/
│       └── nginx.conf
├── scripts/
│   └── entrypoint.sh
├── .env
├── .env.example
├── .gitignore
├── docker-compose.yml
├── requirements.txt
├── alembic.ini
└── README.md



# Root folder အတွင်းမှာ
mkdir -p app/api/v1/endpoints app/core app/models app/schemas app/repositories app/services app/utils app/tasks tests docker/nginx scripts


# __init__.py files တွေဖန်တီးပါ
touch app/__init__.py app/api/__init__.py app/api/v1/__init__.py app/api/v1/endpoints/__init__.py app/core/__init__.py app/models/__init__.py app/schemas/__init__.py app/repositories/__init__.py app/services/__init__.py app/utils/__init__.py app/tasks/__init__.py tests/__init__.py


# Main files တွေဖန်တီးပါ
touch app/main.py app/api/v1/router.py app/api/deps.py app/core/config.py app/core/security.py app/core/database.py app/core/redis_client.py app/models/base.py app/repositories/base_repository.py app/utils/logger.py app/tasks/celery_app.py


# Root level files
touch .env .env.example .gitignore docker-compose.yml requirements.txt alembic.ini README.md

# Docker files
touch docker/Dockerfile docker/nginx/nginx.conf scripts/entrypoint.sh
