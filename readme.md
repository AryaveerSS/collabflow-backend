# CollabFlow Backend

> Production-style real-time team collaboration backend — FastAPI, PostgreSQL, Redis, WebSockets, Docker

---

## What is CollabFlow?

CollabFlow is a scalable backend platform for team collaboration — think Jira meets Trello, built from scratch with production engineering principles. It enables teams to create workspaces, manage projects, assign and track tasks, collaborate through comments, and receive live updates — all through a clean, versioned REST API with real-time WebSocket support.

This is not a tutorial project. It is built the way real backend systems are built — with layered architecture, JWT auth, role-based access control, Redis caching, async background jobs, database migrations, and Docker-based deployment.

---

## Tech Stack

| Layer | Technology |
|---|---|
| API Framework | FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy (async) |
| Migrations | Alembic |
| Real-Time | WebSockets + Redis Pub/Sub |
| Caching & Sessions | Redis |
| Auth | JWT (access + refresh tokens) |
| Validation | Pydantic v2 |
| Background Jobs | AsyncIO / Celery (planned) |
| Containerization | Docker + Docker Compose |
| Testing | Pytest + HTTPX |

---

## Core Features

### Authentication & Authorization
- User registration and login with hashed passwords (bcrypt)
- JWT access tokens + refresh token rotation
- Secure logout with token blacklisting via Redis
- Role-based access control (RBAC) — Owner, Admin, Member, Viewer

### Workspace Management
- Create and manage team workspaces
- Invite members via email
- Role assignment per workspace
- Workspace-level settings and permissions

### Project Management
- Multiple projects per workspace
- Project status tracking (Active, Archived, Completed)
- Deadline management
- Team assignment to projects

### Task Management
- Full task lifecycle — create, assign, update, delete
- Priority levels — Low, Medium, High, Critical
- Status state machine — TODO → IN_PROGRESS → REVIEW → COMPLETED
- Due dates, labels, and tags
- Task dependencies and subtasks
- Advanced filtering, sorting, and pagination

### Real-Time Collaboration
- WebSocket connections per workspace/project
- Live task status updates broadcast to all connected clients
- Typing indicators on comments
- Online/offline presence tracking
- Redis Pub/Sub for multi-instance broadcasting

### Comments & Discussions
- Threaded comments on tasks
- @mentions with notification triggers
- Edit and delete with history tracking
- File attachments on comments

### Notification System
- In-app notifications for task assignments, mentions, deadline reminders
- WebSocket push notifications (instant delivery)
- Notification read/unread state management
- Background job processing for scheduled reminders

### Activity & Audit Trail
- Every action logged — task created, status changed, member invited, etc.
- Per-workspace and per-project activity feeds
- Useful for team transparency and debugging

### File Uploads
- Secure multipart file upload
- File type validation
- Attachment linking to tasks and comments
- Local storage in dev, cloud-ready in production

### Production API Design
- Versioned API routes (`/api/v1/...`)
- Pagination on all list endpoints
- Consistent error response format
- Request/response logging middleware
- Rate limiting middleware

---

## Project Structure

```
collabflow-backend/
├── app/
│   ├── main.py                  # FastAPI app entry point
│   ├── config.py                # Settings and env loading
│   │
│   ├── core/
│   │   ├── security.py          # Password hashing
│   │   ├── database.py          # SQLAlchemy engine and session
│   │   ├── websocket_manager.py # WebSocket connection manager
│   │   └── permissions.py       # RBAC logic
│   │
│   ├── auth/                    # Authentication module
│   ├── users/                   # User management module
│   ├── workspaces/              # Workspace module
│   ├── projects/                # Project module
│   ├── tasks/                   # Task management + WebSocket
│   ├── comments/                # Comments and discussions
│   ├── notifications/           # Notifications + background jobs
│   ├── activity/                # Audit trail
│   ├── middleware/              # Logging, rate limiting
│   └── utils/                  # Pagination, helpers, logger
│
├── migrations/                  # Alembic DB migrations
├── tests/                       # Unit and integration tests
├── uploads/                     # Local file storage (dev)
├── docker-compose.yml
├── requirements.txt
└── .env
```

Each feature module follows the same internal pattern:

```
feature/
├── model.py        # SQLAlchemy ORM model
├── schema.py       # Pydantic request/response schemas
├── routes.py       # FastAPI route handlers
├── service.py      # Business logic
└── repository.py   # Database queries
```

---

## Getting Started

### Prerequisites
- Docker and Docker Compose
- Python 3.11+

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/collabflow-backend.git
cd collabflow-backend
```

### 2. Set up environment variables

```bash
cp .env.example .env
# Edit .env with your values
```

### 3. Start services with Docker

```bash
docker-compose up -d
```

This starts:
- FastAPI app on `http://localhost:8000`
- PostgreSQL on port `5432`
- Redis on port `6379`

### 4. Run database migrations

```bash
alembic upgrade head
```

### 5. Access the API docs

```
http://localhost:8000/docs       # Swagger UI
http://localhost:8000/redoc      # ReDoc
```

---

## API Overview

### Auth
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/auth/register` | Register a new user |
| POST | `/api/v1/auth/login` | Login and get tokens |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| POST | `/api/v1/auth/logout` | Logout and blacklist token |

### Users
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/users/me` | Get current user profile |
| PATCH | `/api/v1/users/me` | Update profile |

### Workspaces
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/workspaces/` | Create workspace |
| GET | `/api/v1/workspaces/` | List user's workspaces |
| POST | `/api/v1/workspaces/{id}/invite` | Invite member |

### Projects
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/projects/` | Create project |
| GET | `/api/v1/projects/?workspace_id=` | List projects |
| PATCH | `/api/v1/projects/{id}` | Update project |
| DELETE | `/api/v1/projects/{id}` | Archive project |

### Tasks
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/tasks/` | Create task |
| GET | `/api/v1/tasks/?project_id=&page=1&priority=HIGH` | List tasks (paginated, filtered) |
| PATCH | `/api/v1/tasks/{id}` | Update task |
| PATCH | `/api/v1/tasks/{id}/status` | Update task status |
| DELETE | `/api/v1/tasks/{id}` | Delete task |

### WebSocket
| Endpoint | Description |
|---|---|
| `ws://localhost:8000/ws/{workspace_id}` | Real-time workspace events |

---

## Environment Variables

```env
# App
APP_NAME=CollabFlow
DEBUG=true
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/collabflow

# Redis
REDIS_URL=redis://localhost:6379

# JWT
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# File Upload
MAX_FILE_SIZE_MB=10
UPLOAD_DIR=uploads/
```

---

## Running Tests

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/
```

---

## Architecture Decisions

**Why FastAPI?** Async-first, automatic OpenAPI docs, Pydantic integration, and Python type hints make it the cleanest modern Python web framework.

**Why feature-based modules?** Co-locating model, schema, service, and routes per feature means you never hunt across folders when working on one domain. Scales better as the codebase grows.

**Why Redis Pub/Sub for WebSockets?** A single server instance can manage WebSocket connections, but once you scale horizontally, you need a message broker to broadcast events across instances. Redis Pub/Sub solves this cleanly.

**Why Alembic?** Raw SQL migrations don't scale. Alembic gives version-controlled, reversible schema changes that work with SQLAlchemy models.

**Why the repository pattern?** Keeping DB queries in `repository.py` separate from business logic in `service.py` makes unit testing possible without a real database — you can mock the repository layer.

---

## Roadmap

- [x] JWT Auth with refresh tokens
- [x] RBAC permissions
- [x] Workspace and project management
- [x] Full task lifecycle with state machine
- [x] Real-time WebSocket updates
- [x] Redis Pub/Sub for horizontal scaling
- [x] Comment system with @mentions
- [x] Notification system
- [x] Activity audit trail
- [x] File uploads
- [x] Pagination, filtering, search
- [x] Docker deployment
- [ ] Email notifications (SMTP integration)
- [ ] Celery + Redis Queue for background jobs
- [ ] OAuth2 (Google login)
- [ ] Admin dashboard API
- [ ] S3 file storage integration
- [ ] Rate limiting per user/workspace

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

> Built to demonstrate production backend engineering — not just another CRUD app.
