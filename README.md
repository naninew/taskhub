# TaskHub API - Task Management System

## 1. Giới thiệu tổng quan

TaskHub là hệ thống quản lý công việc (Task Management API) được xây dựng trên nền tảng FastAPI theo kiến trúc phân tầng (Layered Architecture). Dự án được thiết kế theo mô hình phát triển tăng trưởng (incremental delivery), trong đó khung ứng dụng và cấu trúc hệ thống được thiết lập chuẩn hoá ngay từ giai đoạn đầu.

**Trạng thái hiện tại: Giai đoạn 4 — Workspace, RBAC & Middleware/Exception Handling.** Đã hoàn thành Workspace CRUD cơ bản (tạo/lấy), invite/remove member với phân quyền OWNER/EDITOR/VIEWER, global exception handler JSON thống nhất, middleware log request. Regression test Ngày 1–3 vẫn pass.

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
| 3 | `workspace_members` | workspace_id, user_id, role (OWNER/EDITOR/VIEWER) |
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
│   ├── main.py                  # lifespan + exception handler + LoggingMiddleware (Ngày 4)
│   ├── core/                    # config, logging, exceptions (AppException), security
│   ├── middleware/
│   │   └── logging_middleware.py  # log method/path/status/latency (Ngày 4)
│   ├── api/v1/
│   │   ├── router.py            # auth, users, workspaces, labels
│   │   ├── deps.py              # get_db, get_current_user, require_workspace_role (Ngày 4)
│   │   └── endpoints/           # auth, users, workspaces (Ngày 4), labels
│   ├── schemas/                 # auth, user, workspace (Ngày 4), label
│   ├── models/                  # 9 ORM models + enums
│   ├── repositories/
│   │   ├── base.py              # BaseRepository[T] generic async CRUD
│   │   ├── workspace_repository.py          # (Ngày 4)
│   │   ├── workspace_member_repository.py     # (Ngày 4)
│   │   └── ...
│   ├── services/
│   │   ├── workspace_service.py # create/invite/remove member (Ngày 4)
│   │   └── ...
│   └── db/
├── tests/
│   ├── conftest.py
│   ├── day01/test_labels.py
│   ├── day02/test_labels_db.py
│   ├── day03/test_auth.py
│   └── day04/                   # RBAC + logging middleware (Ngày 4)
├── docs/
│   ├── day-01-core-setup-architecture/test-output/
│   ├── day-02-database-sqlalchemy-alembic/test-output/
│   ├── day-03-auth-user/test-output/
│   └── day-04-workspace-rbac-middleware/test-output/
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
# Chạy migration (schema Ngày 2 + refresh_tokens Ngày 3)
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

Mỗi request được ghi log dạng: `Request: method=... path=... status_code=... latency_ms=...` (Ngày 4).

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

### Workspace (Ngày 4)

| HTTP Method | Endpoint | Mô tả | Auth / RBAC |
|---|---|---|---|
| POST | `/api/v1/workspaces` | Tạo workspace (creator → OWNER) | Bearer |
| GET | `/api/v1/workspaces/{id}` | Chi tiết workspace | Bearer + member |
| POST | `/api/v1/workspaces/{id}/members` | Mời member (email + role) | Bearer + OWNER |
| DELETE | `/api/v1/workspaces/{id}/members/{user_id}` | Xoá member | Bearer + OWNER |

**Business rules Workspace:**
- Người tạo workspace tự động là OWNER trong `workspace_members`.
- Chỉ OWNER được mời/xoá member.
- Workspace phải luôn có ít nhất 1 OWNER — không xoá được OWNER cuối cùng → `409 Conflict`.
- EDITOR/VIEWER không có quyền quản lý member → `403 Forbidden`.

### Label (Ngày 1+2)

| HTTP Method | Endpoint | Mô tả |
|---|---|---|
| POST | `/api/v1/projects/{project_id}/labels` | Tạo Label |
| GET | `/api/v1/projects/{project_id}/labels` | Danh sách Label |
| GET | `/api/v1/projects/{project_id}/labels/{label_id}` | Chi tiết Label |
| PATCH | `/api/v1/projects/{project_id}/labels/{label_id}` | Cập nhật Label |
| DELETE | `/api/v1/projects/{project_id}/labels/{label_id}` | Xoá Label |

**Business rule Label:** Tên Label không được trùng trong cùng project → `400 Bad Request`.

## 9. Exception Handling (Ngày 4)

Mọi lỗi nghiệp vụ kế thừa `AppException` trả JSON thống nhất:

```json
{
  "code": "FORBIDDEN",
  "message": "Insufficient workspace role",
  "detail": "Required role(s): ['OWNER']."
}
```

| Exception | HTTP Status |
|---|---|
| `NotFoundException` | 404 |
| `ForbiddenException` | 403 |
| `ConflictException` | 409 |
| `UnauthorizedException` | 401 |

Auth endpoints (Ngày 3) vẫn dùng `HTTPException` FastAPI mặc định — không thay đổi logic auth/label.

## 10. RBAC — `require_workspace_role` (Ngày 4)

Dependency factory trong `app/api/v1/deps.py`:

```python
Depends(require_workspace_role(WorkspaceMemberRole.OWNER))
Depends(require_workspace_role(WorkspaceMemberRole.OWNER, WorkspaceMemberRole.EDITOR, WorkspaceMemberRole.VIEWER))
```

Ngày 5 sẽ tái sử dụng cho Project/Task — ví dụ VIEWER chỉ đọc, EDITOR được tạo/sửa task.

## 11. Kiểm thử

```bash
# Regression Ngày 1–4
python -m pytest tests/day01 tests/day02 tests/day03 tests/day04 -v

# Xuất log
python -m pytest tests/day01 tests/day02 tests/day03 tests/day04 -v > docs/day-04-workspace-rbac-middleware/test-output/YYYYMMDD-pytest.log
```

Kết quả test mới nhất: **32 passed** (7 day01 + 8 day02 + 12 day03 + 5 day04). Log chi tiết tại `docs/day-04-workspace-rbac-middleware/test-output/`.

## 12. Bàn giao cho Ngày 5

- `require_workspace_role(*roles)` sẵn sàng cho Project/Task CRUD trong workspace.
- `AppException` + global handler dùng chung cho lỗi nghiệp vụ mới.
- `LoggingMiddleware` ghi log mọi request — có thể mở rộng thêm correlation ID ở Ngày 7.
