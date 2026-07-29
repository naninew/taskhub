# TaskHub API - Task Management System

## 1. Giới thiệu tổng quan

TaskHub là hệ thống quản lý công việc (Task Management API) được xây dựng trên nền tảng FastAPI theo kiến trúc phân tầng (Layered Architecture). Dự án được thiết kế theo mô hình phát triển tăng trưởng (incremental delivery), trong đó khung ứng dụng và cấu trúc hệ thống được thiết lập chuẩn hoá ngay từ giai đoạn đầu.

Trạng thái hiện tại: Giai đoạn 1 - Core Setup & Architecture. Đã hoàn thành cấu trúc ứng dụng phân tầng, khởi tạo FastAPI lifespan, triển khai resource Label in-memory và tích hợp bộ kiểm thử tự động pytest.

## 2. Công nghệ sử dụng

- Web Framework: FastAPI (>= 0.111.0)
- ASGI Server: Uvicorn
- Data Validation & Serialization: Pydantic v2
- Configuration Management: pydantic-settings
- Testing Framework: Pytest, pytest-asyncio, HTTPX
- Runtime Environment: Python >= 3.10

## 3. Cấu trúc ứng dụng (Layered Architecture)

Dự án áp dụng mô hình kiến trúc phân tầng tách biệt giữa các thành phần xử lý:

```
taskhub/
├── app/
│   ├── main.py                  # Khởi tạo ứng dụng FastAPI và lifespan handler
│   ├── core/                    # Cấu hình hệ thống, logging, custom exceptions
│   │   ├── config.py
│   │   ├── logging.py
│   │   ├── exceptions.py
│   │   └── security.py
│   ├── api/                     # Tầng giao diện API (Routing & Dependencies)
│   │   └── v1/
│   │       ├── router.py        # Router tổng hợp cho API v1
│   │       ├── deps.py          # Dependency injection (get_db stub, services)
│   │       └── endpoints/       # Các controller theo tài nguyên (labels.py)
│   ├── schemas/                 # Pydantic v2 Data Transfer Objects (label.py)
│   ├── repositories/            # Tầng giao tiếp dữ liệu (label_repository.py)
│   ├── services/                # Tầng nghiệp vụ xử lý logic (label_service.py)
│   ├── models/                  # ORM models (cho các giai đoạn tiếp theo)
│   ├── db/                      # Quản lý kết nối database
│   ├── middleware/              # Middleware xử lý request/response
│   └── tasks/                   # Quản lý tác vụ chạy ngầm
├── tests/                       # Thư mục chứa các kịch bản kiểm thử tự động
│   └── day01/
│       └── test_labels.py       # Integration tests cho Label CRUD
├── requirements.txt             # Danh sách gói phụ thuộc của dự án
├── pyproject.toml               # Cấu hình công cụ và pytest
└── README.md                    # Tài liệu kỹ thuật của dự án
```

## 4. Hướng dẫn khởi tạo môi trường (Virtual Environment)

### 4.1. Khởi tạo môi trường ảo Python

Truy cập vào thư mục gốc của dự án và khởi tạo môi trường ảo `venv`:

Trên Linux / macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Trên Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Trên Windows (Command Prompt):
```cmd
python -m venv .venv
.\.venv\Scripts\activate.bat
```

### 4.2. Cài đặt các gói phụ thuộc

Cập nhật `pip` và cài đặt các thư viện phụ thuộc từ file `requirements.txt`:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## 5. Hướng dẫn chạy ứng dụng (Deployment & Development)

### 5.1. Khởi chạy máy chủ phát triển (Development Server)

Sử dụng `uvicorn` để khởi chạy máy chủ phát triển ở cổng 8000:
```bash
uvicorn app.main:app --reload --port 8000
```

### 5.2. Truy cập tài liệu giao diện API

Sau khi máy chủ khởi chạy thành công, truy cập các địa chỉ sau để xem tài liệu chi tiết:
- Swagger UI Document: http://127.0.0.1:8000/docs
- ReDoc Document: http://127.0.0.1:8000/redoc
- OpenAPI Schema JSON: http://127.0.0.1:8000/api/v1/openapi.json

## 6. Danh mục API Endpoints (Giai đoạn 1 - Label Resource)

Gốc đường dẫn API: `/api/v1`

| HTTP Method | Endpoint | Mô tả | Mã trả về |
|---|---|---|---|
| GET | `/` | Kiểm tra trạng thái ứng dụng | 200 OK |
| POST | `/api/v1/projects/{project_id}/labels` | Tạo mới Label cho project | 201 Created |
| GET | `/api/v1/projects/{project_id}/labels` | Truy vấn danh sách Label của project | 200 OK |
| GET | `/api/v1/projects/{project_id}/labels/{label_id}` | Truy vấn chi tiết Label theo ID | 200 OK / 404 Not Found |
| PATCH | `/api/v1/projects/{project_id}/labels/{label_id}` | Cập nhật thông tin Label | 200 OK / 400 Bad Request / 404 Not Found |
| DELETE | `/api/v1/projects/{project_id}/labels/{label_id}` | Xoá Label khỏi project | 200 OK / 404 Not Found |

### Quy định nghiệp vụ (Business Logic Rules):
- Tên của Label trong cùng một project không được phép trùng lặp. Mọi thao tác khởi tạo hoặc cập nhật vi phạm quy định này sẽ nhận phản hồi mã lỗi `400 Bad Request`.
- Các truy vấn tới `label_id` không tồn tại trong project sẽ trả về mã lỗi `404 Not Found`.

## 7. Quy trình thực thi kiểm thử tự động (Testing)

Dự án tích hợp kịch bản kiểm thử tự động toàn bộ luồng CRUD bằng `pytest` và `httpx.AsyncClient`.

Chạy toàn bộ bài test:
```bash
pytest tests/day01 -v
```

Xuất kết quả kiểm thử ra file log lưu trữ:
```bash
pytest tests/day01 -v > docs/day-01-core-setup-architecture/test-output/20260729-pytest.log
```