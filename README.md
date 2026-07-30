# TaskHub API - Task Management System

## 1. Giới thiệu tổng quan

TaskHub là hệ thống quản lý công việc (Task Management API) được xây dựng trên nền tảng FastAPI theo kiến trúc phân tầng (Layered Architecture). Dự án được thiết kế theo mô hình phát triển tăng trưởng (incremental delivery), trong đó khung ứng dụng và cấu trúc hệ thống được thiết lập chuẩn hoá ngay từ giai đoạn đầu.

**Trạng thái hiện tại: Giai đoạn 3 — Authentication & User Management.** Đã hoàn thành JWT auth (access + refresh token), logout revoke thật sự qua bảng `refresh_tokens`, user profile CRUD, dependency `get_current_user` sẵn sàng cho RBAC Ngày 4. Regression test Ngày 1–2 vẫn pass.

## 2. Công nghệ sử dụng

- Web Framework: FastAPI (>= 0.111.0)
- ASGI Server: Uvicorn
- ORM: SQLAlchemy 2.x (async)
- Migration: Alembic
- Database: SQLite async (`aiosqlite`) mặc định; PostgreSQL (`asyncpg`) qua biến môi trường
- Data Validation & Serialization: Pydantic v2
- Configuration Management: pydantic-settings
- Authentication: JWT (`python-jose`), password hashing (`passlib` + bcrypt)
- Testing Framework: Pytest, pytest-asyncio, HTTPX
- Runtime Environment: Python >= 3.10

## 3. DB Schema (9 bảng)

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
| 9 | `refresh_tokens` | id, token, user_id, revoked, expires_at *(Ngày 3)* |

**Enums:** `UserRole`, `WorkspaceMemberRole`, `ProjectStatus`, `TaskStatus`, `TaskPriority` (xem `app/models/enums.py`).

**Quan hệ chính:** User 1—N Workspace · User 1—N RefreshToken · Workspace N—N User (qua workspace_members) · Workspace 1—N Project · Project 1—N Task/Label · Task N—N Label · Task 1—N Comment.

## 4. Cấu trúc ứng dụng (Layered Architecture)

```
taskhub/
├── alembic/                     # Alembic migration scripts
│   ├── env.py                   # Async migration runner
│   └── versions/                # init schema + refresh_tokens (Ngày 3)
├── alembic.ini
├── app/
│   ├── main.py
│   ├── core/                    # config, logging, exceptions, security (JWT/bcrypt)
│   ├── api/v1/
│   │   ├── router.py            # auth, users, labels
│   │   ├── deps.py              # get_db, get_current_user, service factories
│   │   └── endpoints/           # auth.py, users.py, labels.py (+ stubs ngày sau)
│   ├── schemas/                 # auth.py, user.py, label.py
│   ├── models/                  # 9 ORM models + enums
│   ├── repositories/
│   │   ├── base.py              # BaseRepository[T] generic async CRUD
│   │   ├── label_repository.py
│   │   ├── user_repository.py   # (Ngày 3)
│   │   └── refresh_token_repository.py  # (Ngày 3)
│   ├── services/
│   │   ├── label_service.py
│   │   ├── auth_service.py      # (Ngày 3)
│   │   └── user_service.py      # (Ngày 3)
│   └── db/
│       ├── base.py              # DeclarativeBase
│       └── session.py           # async engine + sessionmaker
├── tests/
│   ├── conftest.py              # DB test fixtures (in-memory SQLite)
│   ├── day01/test_labels.py     # Regression API Label
│   ├── day02/test_labels_db.py  # DB session, BaseRepository, LabelRepository
│   └── day03/test_auth.py       # Auth E2E: register→login→me→refresh→logout
├── docs/
│   ├── day-01-core-setup-architecture/test-output/
│   ├── day-02-database-sqlalchemy-alembic/test-output/
│   └── day-03-auth-user/test-output/
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

### 5.2. Cấu hình Database & JWT

Mặc định dùng SQLite async (không cần cài DB server):
```
DATABASE_URL=sqlite+aiosqlite:///./taskhub.db
SECRET_KEY=your-production-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
```

PostgreSQL (tuỳ chọn):
```
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/taskhub
```

## 6. Alembic Migration

```bash
# Chạy migration (bao gồm bảng refresh_tokens Ngày 3)
python -m alembic upgrade head

# Tạo migration mới (khi thay đổi models)
python -m alembic revision --autogenerate -m "mo ta thay doi"
python -m alembic upgrade head
```

## 7. Chạy ứng dụng

```bash
uvicorn app.main:app --reload --port 8000
```

- Swagger UI: http://127.0.0.1:8000/docs (có nút **Authorize** Bearer token)
- ReDoc: http://127.0.0.1:8000/redoc

## 8. API Endpoints

Gốc đường dẫn: `/api/v1`

### Auth (Ngày 3)

| HTTP Method | Endpoint | Mô tả |
|---|---|---|
| POST | `/api/v1/auth/register` | Đăng ký tài khoản mới |
| POST | `/api/v1/auth/login` | Đăng nhập — nhận access + refresh token |
| POST | `/api/v1/auth/refresh` | Đổi refresh token lấy cặp token mới |
| POST | `/api/v1/auth/logout` | Logout — revoke refresh token trong DB |

### User (Ngày 3)

| HTTP Method | Endpoint | Mô tả | Auth |
|---|---|---|---|
| GET | `/api/v1/users/me` | Lấy profile user hiện tại | Bearer |
| PATCH | `/api/v1/users/me` | Cập nhật profile (full_name, email) | Bearer |
| POST | `/api/v1/users/me/change-password` | Đổi mật khẩu (yêu cầu mật khẩu cũ) | Bearer |

### Label (Ngày 1+2)

| HTTP Method | Endpoint | Mô tả |
|---|---|---|
| POST | `/api/v1/projects/{project_id}/labels` | Tạo Label |
| GET | `/api/v1/projects/{project_id}/labels` | Danh sách Label |
| GET | `/api/v1/projects/{project_id}/labels/{label_id}` | Chi tiết Label |
| PATCH | `/api/v1/projects/{project_id}/labels/{label_id}` | Cập nhật Label |
| DELETE | `/api/v1/projects/{project_id}/labels/{label_id}` | Xoá Label |

**Business rule Label:** Tên Label không được trùng trong cùng project → `400 Bad Request`.

**Auth flow:** Refresh token được lưu DB; logout đánh dấu `revoked=True` — gọi refresh sau logout trả `401`.

## 9. Kiểm thử

```bash
# Regression Ngày 1 + 2 + test mới Ngày 3
python -m pytest tests/day01 tests/day02 tests/day03 -v

# Xuất log
python -m pytest tests/day01 tests/day02 tests/day03 -v > docs/day-03-auth-user/test-output/YYYYMMDD-pytest.log
```

Kết quả test mới nhất: **27 passed** (7 day01 + 8 day02 + 12 day03). Log chi tiết tại `docs/day-03-auth-user/test-output/`.

## 10. Bàn giao cho Ngày 4

- `get_current_user` đã sẵn sàng trong `app/api/v1/deps.py` — Ngày 4 dùng để xây `get_current_active_user`, `require_workspace_role(...)` cho RBAC workspace.
