# TaskHub API - Task Management System

## 1. Giới thiệu tổng quan

TaskHub là hệ thống quản lý công việc (Task Management API) được xây dựng trên nền tảng FastAPI theo kiến trúc phân tầng (Layered Architecture). Dự án được thiết kế theo mô hình phát triển tăng trưởng (incremental delivery), trong đó khung ứng dụng và cấu trúc hệ thống được thiết lập chuẩn hoá ngay từ giai đoạn đầu.

**Trạng thái hiện tại: Giai đoạn 7 — Caching, Background Task, Config, Docker, Logging.** Đã tích hợp thành công Redis async cache bọc quanh API `GET /projects/{id}/tasks` với cơ chế cache invalidation tự động khi có thay đổi (tạo/sửa/xoá task, gán/bỏ label), background task gửi email notification khi task được assign, cấu hình tập trung fail-fast bằng `pydantic-settings`, đóng gói multi-stage `Dockerfile`, cấu hình multi-service với `docker-compose.yml` (App + PostgreSQL + Redis), và logging có cấu trúc. Toàn bộ bộ test Ngày 1–7 pass 100% (41 tests).

## 2. Công nghệ sử dụng

- **Web Framework**: FastAPI (>= 0.111.0)
- **ASGI Server**: Uvicorn
- **ORM & Database**: SQLAlchemy 2.x (async), Alembic migration engine, SQLite async (`aiosqlite`) mặc định cho dev/test, PostgreSQL (`asyncpg`) cho production/Docker
- **Caching**: Redis async client (`redis.asyncio`)
- **Background Processing**: FastAPI `BackgroundTasks`
- **Data Validation & Configuration**: Pydantic v2 & `pydantic-settings` (`BaseSettings` fail-fast validation)
- **Authentication & Security**: JWT (`python-jose`), password hashing (`passlib` + bcrypt)
- **Containerization**: Docker (multi-stage build), Docker Compose
- **Testing Framework**: Pytest, pytest-asyncio, HTTPX
- **Runtime Environment**: Python >= 3.10

## 3. DB Schema (9 bảng)

| # | Bảng | Mô tả |
|---|---|---|
| 1 | `users` | id, email, full_name, hashed_password, role, is_active, created_at |
| 2 | `workspaces` | id, name, owner_id, created_at |
| 3 | `workspace_members` | workspace_id, user_id, role (OWNER/EDITOR/VIEWER) |
| 4 | `projects` | id, workspace_id, name, description, status, created_at |
| 5 | `tasks` | id, project_id, assignee_id, title, description, status, priority, due_date, created_by, created_at |
| 6 | `labels` | id, project_id, name, color, created_at |
| 7 | `task_labels` | task_id, label_id |
| 8 | `comments` | id, task_id, author_id, content, created_at |
| 9 | `refresh_tokens` | id, token, user_id, revoked, expires_at *(Ngày 3)* |

**Enums:** `UserRole`, `WorkspaceMemberRole`, `ProjectStatus`, `TaskStatus`, `TaskPriority` (xem `app/models/enums.py`).

**Quan hệ chính:** User 1—N Workspace · User 1—N RefreshToken · Workspace N—N User (qua workspace_members) · Workspace 1—N Project · Project 1—N Task/Label · Task N—N Label (qua task_labels) · Task 1—N Comment.

## 4. Cấu trúc ứng dụng (Layered Architecture)

```
taskhub/
├── alembic/                     # Alembic migration scripts
│   ├── env.py                   # Async migration runner
│   └── versions/                # init schema + refresh_tokens (Ngày 3)
├── alembic.ini
├── Dockerfile                   # (Ngày 7) Multi-stage Docker build
├── docker-compose.yml           # (Ngày 7) Container orchestration (App + Postgres + Redis)
├── .env.example                 # (Ngày 7) Sample environment variables
├── .env                         # (Ngày 7) Local environment variables
├── app/
│   ├── main.py                  # lifespan (Redis init/close Ngày 7) + exception handler + LoggingMiddleware
│   ├── core/                    # config (fail-fast Ngày 7), logging (Ngày 7), exceptions (AppException), security
│   ├── middleware/
│   │   └── logging_middleware.py  # log method/path/status/latency (Ngày 4)
│   ├── api/v1/
│   │   ├── router.py            # auth, users, workspaces, projects, tasks, labels, comments
│   │   ├── deps.py              # get_db, get_current_user, require_workspace_role, require_project_access
│   │   └── endpoints/           # auth, users, workspaces, projects, tasks (background email Ngày 7), labels, comments
│   ├── db/
│   │   ├── base.py
│   │   ├── session.py           # AsyncSession engine
│   │   └── redis.py             # (Ngày 7) Redis async client & cache invalidation
│   ├── schemas/                 # auth, user, workspace, project, task, label, common (PaginatedResponse), comment
│   ├── models/                  # 9 ORM models + enums
│   ├── repositories/            # BaseRepository[T] & specialized repos
│   ├── services/
│   │   ├── project_service.py
│   │   ├── task_service.py      # (Ngày 7) Redis caching & invalidation cho list_tasks
│   │   ├── label_service.py     # (Ngày 7) Invalidate cache khi gán/bỏ label
│   │   ├── comment_service.py
│   │   └── workspace_service.py
│   └── tasks/
│       └── email_tasks.py       # (Ngày 7) Background email task module
├── tests/
│   ├── conftest.py
│   ├── day01/test_labels.py
│   ├── day02/test_labels_db.py
│   ├── day03/test_auth.py
│   ├── day04/                   # RBAC + logging middleware
│   ├── day05/test_project_task.py
│   ├── day06/test_label_comment_filter.py
│   └── day07/                   # (Ngày 7) Cache invalidation & background email tests
├── docs/                        # Logs & trace output từ Ngày 1 tới Ngày 7
├── requirements.txt
├── pyproject.toml
└── README.md
```

## 5. Hướng dẫn khởi tạo môi trường & Cấu hình (Ngày 7)

### 5.1. Virtual environment & Dependencies

Trải nghiệm phát triển cục bộ (Windows PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

### 5.2. Cấu hình Fail-Fast (`pydantic-settings`)

Hệ thống đọc biến môi trường từ tập tin `.env`. Các biến bắt buộc (`DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`) phải có giá trị, nếu thiếu ứng dụng sẽ **fail-fast** (dừng khởi động lập tức):

```env
PROJECT_NAME="TaskHub API"
ENV="development"
DATABASE_URL="sqlite+aiosqlite:///./taskhub.db"
REDIS_URL="redis://localhost:6379/0"
JWT_SECRET="taskhub-dev-secret-change-in-production"
JWT_ACCESS_EXPIRE_MIN=30
JWT_REFRESH_EXPIRE_DAYS=7
```

## 6. Alembic Migration

```bash
# Chạy migration
python -m alembic upgrade head

# Tạo migration mới khi chỉnh sửa ORM Models
python -m alembic revision --autogenerate -m "mo ta thay doi"
python -m alembic upgrade head
```

## 7. Chạy ứng dụng & Đóng gói Docker (Ngày 7)

### 7.1. Chạy Cục bộ (Local Dev)

```bash
# Đảm bảo Redis đang chạy (tuỳ chọn: qua Docker hoặc Redis local)
uvicorn app.main:app --reload --port 8000
```

- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

### 7.2. Chạy Toàn bộ Stack bằng Docker Compose

Đóng gói toàn bộ ứng dụng (`app`), cơ sở dữ liệu (`db` PostgreSQL 16), và bộ đệm (`redis` 7) với healthcheck đầy đủ:

```bash
docker compose up -d --build
```

Kiểm tra trạng thái các container:
```bash
docker compose ps
```

## 8. API Endpoints chính

Gốc đường dẫn: `/api/v1`

### Auth & User (Ngày 3)
- `POST /api/v1/auth/register` — Đăng ký tài khoản
- `POST /api/v1/auth/login` — Đăng nhập (nhận JWT TokenPair)
- `POST /api/v1/auth/refresh` — Token rotation (cặp token mới)
- `POST /api/v1/auth/logout` — Thu hồi refresh token
- `GET/PATCH /api/v1/users/me` — Thông tin profile
- `POST /api/v1/users/me/change-password` — Đổi mật khẩu

### Workspace & RBAC (Ngày 4)
- `POST /api/v1/workspaces` — Tạo workspace (creator = OWNER)
- `GET /api/v1/workspaces/{id}` — Chi tiết workspace
- `POST/DELETE /api/v1/workspaces/{id}/members` — Quản lý thành viên workspace (OWNER only)

### Project (Ngày 5)
- `POST/GET /api/v1/workspaces/{id}/projects` — Quản lý project
- `GET/PATCH /api/v1/workspaces/{workspace_id}/projects/{id}` — Chi tiết/cập nhật project (+ archive)

### Task, Redis Cache & Background Tasks (Ngày 5 + 6 + 7)
- `POST /api/v1/projects/{id}/tasks` — Tạo task mới (invalidate cache project)
- `GET /api/v1/projects/{id}/tasks` — Danh sách task có filter (`status`, `priority`, `assignee_id`) & pagination (`page`, `limit`). **Bọc Redis Cache** key pattern `tasks:{project_id}:{status}:{priority}:{assignee_id}:{page}:{limit}` (TTL 60s).
- `PATCH /api/v1/tasks/{id}` — Cập nhật task (invalidate cache project). Nếu gán `assignee_id` mới → tự động kích hoạt **Background Task** gửi email notification.
- `DELETE /api/v1/tasks/{id}` — Xoá task (invalidate cache project).

### Task Label & Comment (Ngày 6 + 7)
- `POST/DELETE /api/v1/tasks/{id}/labels/{label_id}` — Gán/bỏ label (invalidate cache project).
- `POST /api/v1/tasks/{task_id}/comments` — Viết bình luận.
- `DELETE /api/v1/comments/{id}` — Xoá bình luận (chỉ tác giả hoặc workspace OWNER/ADMIN).

## 9. Kiểm thử (Automated Tests)

Chạy toàn bộ bộ test tích hợp từ Ngày 1 đến Ngày 7:

```bash
python -m pytest tests/day01 tests/day02 tests/day03 tests/day04 tests/day05 tests/day06 tests/day07 -v
```

**Kết quả kiểm thử Ngày 7**: **41 passed** (100% pass rate).
Logs và traces kiểm chứng lưu vết tại: `docs/day-07-cache-background-config-docker-logging/test-output/`.
