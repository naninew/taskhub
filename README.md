# TaskHub API - Task Management System

## 1. Giới thiệu tổng quan

TaskHub là hệ thống quản lý công việc (Task Management API) được xây dựng trên nền tảng FastAPI theo kiến trúc phân tầng (Layered Architecture). Dự án được thiết kế theo mô hình phát triển tăng trưởng (incremental delivery), trong đó khung ứng dụng và cấu trúc hệ thống được thiết lập chuẩn hoá ngay từ giai đoạn đầu.

**Trạng thái hiện tại: Giai đoạn 2 — Database: SQLAlchemy 2.x & Alembic.** Đã hoàn thành 8 ORM models, `BaseRepository[T]` generic, Alembic migration, chuyển Label repository từ in-memory sang DB thật, regression test Ngày 1 vẫn pass.

## 2. Công nghệ sử dụng

- Web Framework: FastAPI (>= 0.111.0)
- ASGI Server: Uvicorn
- ORM: SQLAlchemy 2.x (async)
- Migration: Alembic
- Database: SQLite async (`aiosqlite`) mặc định; PostgreSQL (`asyncpg`) qua biến môi trường
- Data Validation & Serialization: Pydantic v2
- Configuration Management: pydantic-settings
- Testing Framework: Pytest, pytest-asyncio, HTTPX
- Runtime Environment: Python >= 3.10

## 3. DB Schema (8 bảng)

| # | Bảng | Mô tả |
|---|---|---|
| 1 | `users` | id, email, full_name, hashed_password, role, is_active, created_at |
| 2 | `workspaces` | id, name, owner_id, created_at |
| 3 | `workspace_members` | workspace_id, user_id, role |
| 4 | `projects` | id, workspace_id, name, description, status, created_at |
| 5 | `tasks` | id, project_id, assignee_id, title, description, status, priority, due_date, created_by, created_at |
| 6 | `labels` | id, project_id, name, color, created_at |
| 7 | `task_labels` | task_id, label_id |
| 8 | `comments` | id, task_id, author_id, content, created_at |

**Enums:** `UserRole`, `WorkspaceMemberRole`, `ProjectStatus`, `TaskStatus`, `TaskPriority` (xem `app/models/enums.py`).

**Quan hệ chính:** User 1—N Workspace · Workspace N—N User (qua workspace_members) · Workspace 1—N Project · Project 1—N Task/Label · Task N—N Label · Task 1—N Comment.

## 4. Cấu trúc ứng dụng (Layered Architecture)

```
taskhub/
├── alembic/                     # Alembic migration scripts
│   ├── env.py                   # Async migration runner
│   └── versions/                # Migration files (init schema)
├── alembic.ini
├── app/
│   ├── main.py
│   ├── core/                    # config, logging, exceptions, security
│   ├── api/v1/
│   │   ├── router.py
│   │   ├── deps.py              # get_db() → AsyncSession thật
│   │   └── endpoints/           # labels.py (+ stubs cho ngày sau)
│   ├── schemas/                 # Pydantic v2 DTOs
│   ├── models/                  # 8 SQLAlchemy ORM models + enums
│   ├── repositories/
│   │   ├── base.py              # BaseRepository[T] generic async CRUD
│   │   └── label_repository.py  # SQLAlchemy (thay in-memory Ngày 1)
│   ├── services/
│   └── db/
│       ├── base.py              # DeclarativeBase
│       └── session.py           # async engine + sessionmaker
├── tests/
│   ├── conftest.py              # DB test fixtures (in-memory SQLite)
│   ├── day01/test_labels.py     # Regression API Label
│   └── day02/test_labels_db.py  # DB session, BaseRepository, LabelRepository
├── docs/day-02-database-sqlalchemy-alembic/test-output/
├── requirements.txt
├── pyproject.toml
└── README.md
```

## 5. Hướng dẫn khởi tạo môi trường

### 5.1. Virtual environment

Trên Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

### 5.2. Cấu hình Database

Mặc định dùng SQLite async (không cần cài DB server):
```
DATABASE_URL=sqlite+aiosqlite:///./taskhub.db
```

PostgreSQL (tuỳ chọn):
```
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/taskhub
```

## 6. Alembic Migration

```bash
# Tạo/chạy migration
python -m alembic upgrade head

# Tạo migration mới (khi thay đổi models)
python -m alembic revision --autogenerate -m "mo ta thay doi"
python -m alembic upgrade head
```

## 7. Chạy ứng dụng

```bash
uvicorn app.main:app --reload --port 8000
```

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## 8. API Endpoints (Label — Giai đoạn 1+2)

Gốc đường dẫn: `/api/v1`

| HTTP Method | Endpoint | Mô tả |
|---|---|---|
| POST | `/api/v1/projects/{project_id}/labels` | Tạo Label |
| GET | `/api/v1/projects/{project_id}/labels` | Danh sách Label |
| GET | `/api/v1/projects/{project_id}/labels/{label_id}` | Chi tiết Label |
| PATCH | `/api/v1/projects/{project_id}/labels/{label_id}` | Cập nhật Label |
| DELETE | `/api/v1/projects/{project_id}/labels/{label_id}` | Xoá Label |

**Business rule:** Tên Label không được trùng trong cùng project → `400 Bad Request`.

## 9. Kiểm thử

```bash
# Regression Ngày 1 + test mới Ngày 2
python -m pytest tests/day01 tests/day02 -v

# Xuất log
python -m pytest tests/day01 tests/day02 -v > docs/day-02-database-sqlalchemy-alembic/test-output/20260730-pytest.log
```

Kết quả test mới nhất: **15 passed** (7 day01 + 8 day02). Log chi tiết tại `docs/day-02-database-sqlalchemy-alembic/test-output/`.
