# TaskHub API - Task Management System

## 1. Giới thiệu tổng quan

TaskHub là hệ thống quản lý công việc (Task Management API) được xây dựng trên nền tảng FastAPI theo kiến trúc phân tầng (Layered Architecture). Dự án được thiết kế theo mô hình phát triển tăng trưởng (incremental delivery), trong đó khung ứng dụng và cấu trúc hệ thống được thiết lập chuẩn hoá ngay từ giai đoạn đầu.

**Trạng thái hiện tại: Giai đoạn 6 — Label, Comment, Filtering & Pagination.** Đã hoàn thành gán/bỏ label cho task, Comment CRUD trên task (phân quyền tác giả / workspace OWNER), nâng cấp `GET /projects/{id}/tasks` hỗ trợ filter (`status`, `priority`, `assignee_id`) và phân trang (`page`, `limit`) trả về schema generic `PaginatedResponse[TaskRead]`. Regression test Ngày 1–5 vẫn pass 100%.

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

**Quan hệ chính:** User 1—N Workspace · User 1—N RefreshToken · Workspace N—N User (qua workspace_members) · Workspace 1—N Project · Project 1—N Task/Label · Task N—N Label (qua task_labels) · Task 1—N Comment.

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
│   │   ├── router.py            # auth, users, workspaces, projects, tasks, labels, comments (Ngày 6)
│   │   ├── deps.py              # get_db, get_current_user, require_workspace_role, require_project_access, get_comment_service (Ngày 6)
│   │   └── endpoints/           # auth, users, workspaces, projects, tasks (Ngày 6 filter/page), labels (Ngày 6 task label), comments (Ngày 6)
│   ├── schemas/                 # auth, user, workspace, project, task, label, common (PaginatedResponse Ngày 6), comment (Ngày 6)
│   ├── models/                  # 9 ORM models + enums
│   ├── repositories/
│   │   ├── base.py              # BaseRepository[T] generic async CRUD
│   │   ├── project_repository.py
│   │   ├── task_repository.py       # list_tasks_filtered (Ngày 6)
│   │   ├── task_label_repository.py # (Ngày 6)
│   │   ├── comment_repository.py    # (Ngày 6)
│   │   └── workspace_repository.py
│   ├── services/
│   │   ├── project_service.py
│   │   ├── task_service.py      # list_tasks filter & pagination (Ngày 6)
│   │   ├── label_service.py     # assign/remove label cho task (Ngày 6)
│   │   ├── comment_service.py   # create & delete comment permissions (Ngày 6)
│   │   └── workspace_service.py
│   └── db/
├── tests/
│   ├── conftest.py
│   ├── day01/test_labels.py
│   ├── day02/test_labels_db.py
│   ├── day03/test_auth.py
│   ├── day04/                   # RBAC + logging middleware (Ngày 4)
│   ├── day05/test_project_task.py  # Project & Task CRUD (Ngày 5)
│   └── day06/test_label_comment_filter.py # Label task, Comment, Filter & Pagination (Ngày 6)
├── docs/
│   ├── day-01-core-setup-architecture/test-output/
│   ├── day-02-database-sqlalchemy-alembic/test-output/
│   ├── day-03-auth-user/test-output/
│   ├── day-04-workspace-rbac-middleware/test-output/
│   ├── day-05-project-task-crud/test-output/
│   └── day-06-label-comment-filter-pagination/test-output/
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

### Project (Ngày 5)

| HTTP Method | Endpoint | Mô tả | Auth / RBAC |
|---|---|---|---|
| POST | `/api/v1/workspaces/{id}/projects` | Tạo project | Bearer + OWNER/EDITOR |
| GET | `/api/v1/workspaces/{id}/projects` | Danh sách project | Bearer + member |
| GET | `/api/v1/workspaces/{workspace_id}/projects/{id}` | Chi tiết project | Bearer + member |
| PATCH | `/api/v1/workspaces/{workspace_id}/projects/{id}` | Cập nhật project | Bearer + OWNER/EDITOR |
| PATCH | `/api/v1/workspaces/{workspace_id}/projects/{id}/archive` | Archive project | Bearer + OWNER/EDITOR |

### Task & Filtering/Pagination (Ngày 5 + Nâng cấp Ngày 6)

| HTTP Method | Endpoint | Mô tả | Auth / RBAC |
|---|---|---|---|
| POST | `/api/v1/projects/{id}/tasks` | Tạo task | Bearer + OWNER/EDITOR |
| GET | `/api/v1/projects/{id}/tasks` | Danh sách task (filter status, priority, assignee_id + pagination page, limit) | Bearer + member |
| PATCH | `/api/v1/tasks/{id}` | Cập nhật task (assign, status, priority, due_date) | Bearer + OWNER/EDITOR |
| DELETE | `/api/v1/tasks/{id}` | Xoá task | Bearer + OWNER/EDITOR |

**Business rules Task:**
- Tạo task mặc định `status=TODO`, `priority=MEDIUM`.
- `assignee_id` phải là thành viên workspace chứa project → nếu không → `409 Conflict`.
- `GET /projects/{id}/tasks` nhận query parameters: `status`, `priority`, `assignee_id`, `page` (mặc định 1), `limit` (mặc định 20). Trả về response dạng `PaginatedResponse[TaskRead]` chứa `items`, `total`, `page`, `limit`.

### Task Label (Ngày 6)

| HTTP Method | Endpoint | Mô tả | Auth / RBAC |
|---|---|---|---|
| POST | `/api/v1/projects/{project_id}/labels` | Tạo Label cho project | Bearer + member |
| GET | `/api/v1/projects/{project_id}/labels` | Danh sách Label | Bearer + member |
| POST | `/api/v1/tasks/{task_id}/labels/{label_id}` | Gán label vào task | Bearer + OWNER/EDITOR |
| DELETE | `/api/v1/tasks/{task_id}/labels/{label_id}` | Bỏ label khỏi task | Bearer + OWNER/EDITOR |

### Comment (Ngày 6)

| HTTP Method | Endpoint | Mô tả | Auth / RBAC |
|---|---|---|---|
| POST | `/api/v1/tasks/{task_id}/comments` | Thêm comment trên task | Bearer + member |
| DELETE | `/api/v1/comments/{comment_id}` | Xoá comment | Bearer + Tác giả comment / Workspace OWNER / ADMIN |

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

## 10. RBAC (Ngày 4 + Ngày 5 + Ngày 6)

### `require_workspace_role` (Ngày 4)

Dependency factory trong `app/api/v1/deps.py`:

```python
Depends(require_workspace_role(WorkspaceMemberRole.OWNER))
```

### `require_project_access` (Ngày 5)

Tra `project_id` → lấy `workspace_id` → kiểm tra membership + role:

```python
Depends(require_project_access(WorkspaceMemberRole.OWNER, WorkspaceMemberRole.EDITOR))
```

### Comment Authorization Rules (Ngày 6)
- Xoá comment: Tác giả của comment HOẶC người dùng có vai trò `OWNER` trong workspace chứa task (hoặc hệ thống ADMIN) mới có quyền xoá. Ngược lại trả `403 Forbidden`.

## 11. Kiểm thử

```bash
# Regression Ngày 1–6
python -m pytest tests/day01 tests/day02 tests/day03 tests/day04 tests/day05 tests/day06 -v

# Xuất log
python -m pytest tests/day01 tests/day02 tests/day03 tests/day04 tests/day05 tests/day06 -v > docs/day-06-label-comment-filter-pagination/test-output/20260803-pytest.log
```

Kết quả test mới nhất: **39 passed** (7 day01 + 8 day02 + 12 day03 + 5 day04 + 4 day05 + 3 day06). Log chi tiết tại `docs/day-06-label-comment-filter-pagination/test-output/`.

## 12. Bàn giao cho Ngày 7

- `GET /projects/{id}/tasks` đã có response schema ổn định (`PaginatedResponse[TaskRead]`).
- Ngày 7 sẽ bọc Redis cache quanh `list_tasks` với TTL 60s và thực hiện invalidate cache khi tạo/sửa/xoá task hoặc gán/bỏ label.
