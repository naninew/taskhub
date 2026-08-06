# TaskHub API - Task Management System

> **Hệ thống Quản lý Công việc (Task Management API)** xây dựng bằng **FastAPI**, tuân thủ kiến trúc phân tầng (**Layered Architecture**), tích hợp **SQLAlchemy 2.x (Async)**, **Alembic**, **Redis Async Cache**, **Background Tasks**, **JWT Authentication & RBAC**, **Docker Multi-Stage Build**, và **Pydantic v2 Fail-Fast Configuration**.

---

## 1. Giới thiệu Tổng quan & Trạng thái Hệ thống

**Trạng thái Dự án: HOÀN THÀNH NGÀY 8/8 — Review, Refactor & Optimization (100% Pass Rate).**

Dự án đã trải qua 8 ngày phát triển tăng trưởng (incremental delivery), xây dựng từ skeleton ban đầu tới hệ thống quản lý công việc hoàn chỉnh:
- **14/14 Hạng mục Bắt buộc** hoàn thành 100% (xem `PROGRESS.md`).
- **45/45 Automated Integration Tests** pass 100% (xem `tests/day01` -> `tests/day08`).
- **Code Quality**: `ruff check .` pass **0 lỗi**, `mypy app` pass **0 error**.
- **Refactor & DRY**: Gom logic phân quyền lặp lại ở `deps.py` và `label_service.py`, chuyển đổi toàn bộ exception thô về dạng `AppException` chuẩn (`{code, message, detail}`).
- **Performance**: Giải quyết triệt me vấn đề N+1 query bằng `selectinload` quan hệ `assignee` và `task_labels`; nâng cao tốc độ phản hồi qua Redis Async Cache (TTL 60s) kèm cơ chế tự động xoá đệm (Cache Invalidation).

---

## 2. Công nghệ Sử dụng

- **Web Framework**: FastAPI (>= 0.111.0)
- **ASGI Server**: Uvicorn
- **ORM & Database**: SQLAlchemy 2.x (async), Alembic migration engine, SQLite async (`aiosqlite`) mặc định cho dev/test, PostgreSQL (`asyncpg`) cho production/Docker
- **Caching**: Redis async client (`redis.asyncio`)
- **Background Processing**: FastAPI `BackgroundTasks`
- **Data Validation & Configuration**: Pydantic v2 & `pydantic-settings` (`BaseSettings` fail-fast validation)
- **Authentication & Security**: JWT Token Pair & Rotation (`python-jose`), password hashing (`passlib` + bcrypt)
- **Code Quality & Type Safety**: Ruff (linter/formatter), Mypy (static type checker)
- **Containerization**: Docker (multi-stage build python:3.12-slim), Docker Compose v2 (App + PostgreSQL 16 + Redis 7)
- **Testing Framework**: Pytest, pytest-asyncio, HTTPX

---

## 3. Cấu trúc Cơ sở Dữ liệu (9 Bảng)

| # | Bảng | Mô tả |
|---|---|---|
| 1 | `users` | id, email, full_name, hashed_password, role, is_active, created_at |
| 2 | `workspaces` | id, name, owner_id, created_at |
| 3 | `workspace_members` | workspace_id, user_id, role (`OWNER`, `EDITOR`, `VIEWER`) |
| 4 | `projects` | id, workspace_id, name, description, status (`ACTIVE`, `ARCHIVED`), created_at |
| 5 | `tasks` | id, project_id, assignee_id, title, description, status (`TODO`, `IN_PROGRESS`, `IN_REVIEW`, `DONE`), priority (`LOW`, `MEDIUM`, `HIGH`, `URGENT`), due_date, created_by, created_at |
| 6 | `labels` | id, project_id, name, color, created_at |
| 7 | `task_labels` | task_id, label_id |
| 8 | `comments` | id, task_id, author_id, content, created_at |
| 9 | `refresh_tokens` | id, token, user_id, revoked, expires_at |

**Enums:** `UserRole`, `WorkspaceMemberRole`, `ProjectStatus`, `TaskStatus`, `TaskPriority` (xem `app/models/enums.py`).

**Quan hệ chính:**
- User 1—N Workspace · User 1—N RefreshToken
- Workspace N—N User (qua `workspace_members`)
- Workspace 1—N Project · Project 1—N Task/Label
- Task N—N Label (qua `task_labels`) · Task 1—N Comment

---

## 4. Cấu trúc Ứng dụng (Layered Architecture)

```
taskhub/
├── alembic/                     # Alembic migration scripts & async runner
│   └── versions/                # Migration files (init schema & refresh_tokens)
├── alembic.ini                  # Cấu hình Alembic DB URL
├── Dockerfile                   # Multi-stage Docker build (builder/runner, non-root)
├── docker-compose.yml           # Multi-service stack (App + Postgres 16 + Redis 7)
├── .env.example                 # Biến môi trường mẫu
├── .env                         # Biến môi trường local
├── pyproject.toml               # Cấu hình Ruff, Mypy & Pytest
├── requirements.txt             # Danh sách dependencies
├── CHANGELOG.md                 # Nhật ký thay đổi append-only Ngày 1 -> 8
├── PROGRESS.md                  # Checklist 14 hạng mục bắt buộc (100% completed)
├── README.md                    # Tài liệu tổng quan dự án
├── app/
│   ├── main.py                  # FastAPI instance, lifespan (Redis), exception handler, middleware
│   ├── core/                    # Config (fail-fast), logging, exceptions, security (JWT/bcrypt)
│   ├── middleware/
│   │   └── logging_middleware.py# Logging request method, path, status, latency_ms
│   ├── api/v1/
│   │   ├── router.py            # Mount 7 router module
│   │   ├── deps.py              # Dependency injection: DB session, Current User, DRY RBAC verifiers
│   │   └── endpoints/           # 7 APIRouter endpoints (auth, users, workspaces, projects, tasks, labels, comments)
│   ├── db/
│   │   ├── base.py              # DeclarativeBase SQLAlchemy
│   │   ├── session.py           # AsyncSession engine & sessionmaker
│   │   └── redis.py             # Client Redis async & cache invalidation helpers
│   ├── schemas/                 # Pydantic v2 schemas (Auth, User, Workspace, Project, Task, Label, Comment, Common)
│   ├── models/                  # 9 ORM models SQLAlchemy 2.x
│   ├── repositories/            # BaseRepository[T] generic CRUD & specialized repositories (eager loading optimized)
│   ├── services/                # Business logic services (Auth, User, Workspace, Project, Task, Label, Comment)
│   └── tasks/
│       └── email_tasks.py       # Background email notification task
├── tests/                       # 45 test cases tích hợp phân chia từ Ngày 1 đến 8
│   ├── conftest.py              # Fixture DB SQLite in-memory & HTTP Client
│   ├── day01/                   # Tests Core Label in-memory
│   ├── day02/                   # Tests SQLAlchemy DB & Alembic
│   ├── day03/                   # Tests Auth JWT & User management
│   ├── day04/                   # Tests Workspace RBAC & Logging middleware
│   ├── day05/                   # Tests Project & Task CRUD + State Machine
│   ├── day06/                   # Tests Label-Task assignment, Comment & Filter/Pagination
│   ├── day07/                   # Tests Redis Cache Invalidation & Background Tasks
│   └── day08/                   # Tests OpenAPI schema, Refactored RBAC & N+1 Optimization
└── docs/                        # Bằng chứng thật & test output logs (Ngày 1 -> 8)
```

---

## 5. Hướng dẫn Khởi tạo & Cấu hình Môi trường

### 5.1. Cài đặt Virtual Environment & Dependencies

Trên Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

### 5.2. Biến môi trường Fail-Fast (`.env`)

Tạo tập tin `.env` từ `.env.example`. Các biến môi trường bắt buộc sẽ được kiểm tra **fail-fast** qua `pydantic-settings`:

```env
PROJECT_NAME="TaskHub API"
ENV="development"
DATABASE_URL="sqlite+aiosqlite:///./taskhub.db"
REDIS_URL="redis://localhost:6379/0"
JWT_SECRET="taskhub-dev-secret-change-in-production"
JWT_ACCESS_EXPIRE_MIN=30
JWT_REFRESH_EXPIRE_DAYS=7
```

---

## 6. Alembic Migration

Thực thi migration để cập nhật cấu trúc cơ sở dữ liệu lên phiên bản mới nhất:

```bash
# Thao tác upgrade cơ sở dữ liệu
python -m alembic upgrade head

# (Tuỳ chọn) Tạo migration tự động khi chỉnh sửa ORM Models
python -m alembic revision --autogenerate -m "describe changes"
python -m alembic upgrade head
```

---

## 7. Chạy Ứng dụng & Docker Container

### 7.1. Chạy Cục bộ (Local Development)

```bash
# Đảm bảo Redis service đang khởi chạy trên port 6379
uvicorn app.main:app --reload --port 8000
```

- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **OpenAPI JSON**: [http://127.0.0.1:8000/api/v1/openapi.json](http://127.0.0.1:8000/api/v1/openapi.json)

### 7.2. Chạy toàn bộ Stack bằng Docker Compose

Khởi động đồng thời 3 container (`app`, `db` PostgreSQL 16 alpine, `redis` 7 alpine) với healthcheck đầy đủ:

```bash
docker compose up -d --build
```

Kiểm tra trạng thái container:
```bash
docker compose ps
```

---

## 8. Danh sách API Endpoints

Đường dẫn gốc (Prefix): `/api/v1`

### Authentication (`/auth`)
- `POST /api/v1/auth/register` — Đăng ký tài khoản người dùng
- `POST /api/v1/auth/login` — Đăng nhập (trả về cặp JWT Token)
- `POST /api/v1/auth/refresh` — Token Rotation (cấp cặp token mới và thu hồi token cũ)
- `POST /api/v1/auth/logout` — Đăng xuất (thu hồi Refresh Token)

### User Management (`/users`)
- `GET /api/v1/users/me` — Xem thông tin cá nhân hiện tại
- `PATCH /api/v1/users/me` — Cập nhật tên/email cá nhân
- `POST /api/v1/users/me/change-password` — Đổi mật khẩu (xác thực mật khẩu cũ)

### Workspace & RBAC (`/workspaces`)
- `POST /api/v1/workspaces` — Tạo workspace mới (tự động gán người tạo = OWNER)
- `GET /api/v1/workspaces/{id}` — Xem chi tiết workspace (yêu cầu là member)
- `POST /api/v1/workspaces/{id}/members` — Mời thành viên bằng email (Chỉ Workspace OWNER)
- `DELETE /api/v1/workspaces/{id}/members/{user_id}` — Xoá thành viên (Chỉ Workspace OWNER)

### Projects (`/workspaces/{workspace_id}/projects`)
- `POST /api/v1/workspaces/{id}/projects` — Tạo dự án trong workspace (OWNER/EDITOR)
- `GET /api/v1/workspaces/{id}/projects` — Danh sách dự án (Hỗ trợ `?include_archived=true`)
- `GET /api/v1/workspaces/{workspace_id}/projects/{id}` — Chi tiết dự án
- `PATCH /api/v1/workspaces/{workspace_id}/projects/{id}` — Cập nhật tên/mô tả dự án (OWNER/EDITOR)
- `PATCH /api/v1/workspaces/{workspace_id}/projects/{id}/archive` — Chuyển trạng thái dự án sang ARCHIVED

### Tasks, Cache & Background Email (`/projects/{id}/tasks` & `/tasks/{id}`)
- `POST /api/v1/projects/{id}/tasks` — Tạo công việc mới (Xoá Redis Cache)
- `GET /api/v1/projects/{id}/tasks` — Lọc & Phân trang công việc (`status`, `priority`, `assignee_id`, `page`, `limit`). **Bọc Redis Cache (TTL 60s)**.
- `PATCH /api/v1/tasks/{id}` — Cập nhật công việc (State Machine status, assign member, priority...). Tự động gửi **Background Email Notification** nếu đổi người thực hiện và xoá Redis Cache.
- `DELETE /api/v1/tasks/{id}` — Xoá công việc (Xoá Redis Cache)

### Task Labels (`/projects/{id}/labels` & `/tasks/{id}/labels/{label_id}`)
- `POST /api/v1/projects/{id}/labels` — Tạo nhãn mới trong dự án
- `GET /api/v1/projects/{id}/labels` — Danh sách nhãn của dự án
- `GET /api/v1/projects/{id}/labels/{label_id}` — Chi tiết nhãn
- `PATCH /api/v1/projects/{id}/labels/{label_id}` — Cập nhật tên/màu nhãn
- `DELETE /api/v1/projects/{id}/labels/{label_id}` — Xoá nhãn
- `POST /api/v1/tasks/{id}/labels/{label_id}` — Gán nhãn vào công việc (OWNER/EDITOR)
- `DELETE /api/v1/tasks/{id}/labels/{label_id}` — Gỡ nhãn khỏi công việc (OWNER/EDITOR)

### Comments (`/tasks/{id}/comments` & `/comments/{id}`)
- `POST /api/v1/tasks/{id}/comments` — Viết bình luận trên công việc
- `DELETE /api/v1/comments/{id}` — Xoá bình luận (Tác giả, ADMIN hoặc Workspace OWNER)

---

## 9. Kiểm thử Tự động & Chất lượng Code

### 9.1. Chạy Toàn bộ Test Suite

Chạy 45 bài test tích hợp phủ toàn bộ các Ngày 1 -> Ngày 8:

```bash
python -m pytest tests/ -v
```

### 9.2. Kiểm tra Linting & Static Typing

```bash
# Kiểm tra linter Ruff
python -m ruff check .

# Kiểm tra static typing Mypy
python -m mypy app
```

**Bằng chứng và log kết quả chi tiết**: Được lưu vết đầy đủ trong thư mục `docs/day-08-review-refactor-optimization/test-output/`.
