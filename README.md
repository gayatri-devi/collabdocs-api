# CollabDocs API

Backend API for CollabDocs, a collaborative document platform where users create workspaces, invite collaborators, write and version documents, leave threaded comments, and control access with role-based permissions. API only; Postman is the client.

Built with Django, Django REST Framework and PostgreSQL.

**Demo video:** _add Loom / Google Drive link here_

## Team

| Name | Responsibility |
|------|----------------|
|      |                |

## Project structure

```
collabdocs-api/
├── config/                  # settings, root urls, wsgi/asgi
├── apps/
│   ├── core/                # request logging middleware, permissions, query param helpers
│   ├── users/               # custom User model, registration
│   ├── workspaces/          # Workspace, WorkspaceMember
│   ├── documents/           # Document, DocumentVersion, Tag, Comment, signals, services
│   └── audit/               # AuditLog
├── CollabDocs.postman_collection.json
├── requirements.txt
├── .env.example
└── manage.py
```

## Setup

Requirements: Python 3.11+ and PostgreSQL 14+.

1. Clone the repository and create a virtual environment:

   ```bash
   git clone <repo-url>
   cd collabdocs-api
   python -m venv venv
   source venv/bin/activate        # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Create the PostgreSQL database and user:

   ```sql
   CREATE DATABASE collabdocs;
   CREATE USER collabdocs_user WITH PASSWORD 'your-password';
   GRANT ALL PRIVILEGES ON DATABASE collabdocs TO collabdocs_user;
   ALTER DATABASE collabdocs OWNER TO collabdocs_user;
   ```

3. Copy the example environment file and fill in your values:

   ```bash
   cp .env.example .env
   ```

   | Variable | Description |
   |----------|-------------|
   | `DJANGO_SECRET_KEY` | Any long random string |
   | `DJANGO_DEBUG` | `True` for local development |
   | `DJANGO_ALLOWED_HOSTS` | Comma separated hosts |
   | `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT` | Database connection |

## Apply migrations

```bash
python manage.py migrate
```

Optionally create an admin user for the Django admin at `/admin/`:

```bash
python manage.py createsuperuser
```

## Run the server

```bash
python manage.py runserver
```

The API is served at `http://127.0.0.1:8000/api/`. Every request is logged to the console by the custom middleware:

```
[2026-10-04 14:02:11] POST /api/documents/ -> 201 (12.68 ms)
```

## Authentication

Token authentication. Register (`POST /api/users/`) or log in (`POST /api/auth/token/`) to get a token, then send:

```
Authorization: Token <your-token>
```

The Postman collection stores the token automatically after Register or Login.

## Endpoints

| Area | Method | Endpoint | Notes |
|------|--------|----------|-------|
| Users | POST | `/api/users/` | Register, returns token |
| Users | POST | `/api/auth/token/` | Log in |
| Users | GET | `/api/users/` | `?search=`, `?created_after=` |
| Users | GET / PUT | `/api/users/{id}/` | Only your own account can be edited |
| Users | GET | `/api/users/me/` | Current user |
| Workspaces | POST / GET | `/api/workspaces/` | Create is atomic (workspace + admin member + audit log) |
| Workspaces | GET / PUT / DELETE | `/api/workspaces/{id}/` | DELETE archives (`is_active=false`) |
| Workspaces | GET / POST | `/api/workspaces/{id}/members/` | Duplicate member returns 409 |
| Workspaces | GET | `/api/workspaces/{id}/stats/` | Aggregation endpoint |
| Documents | POST / GET | `/api/documents/` | Filters: `workspace`, `status`, `tag`, `created_by`, `search`, `created_after`, `created_before` |
| Documents | GET / PUT / PATCH / DELETE | `/api/documents/{id}/` | Every save creates a new version |
| Documents | GET | `/api/documents/{id}/versions/` | Version history |
| Documents | GET / POST | `/api/documents/{id}/tags/` | Body: `{"tags": ["python"]}` |
| Documents | GET | `/api/documents/summary/` | Aggregation endpoint |
| Comments | POST / GET | `/api/comments/` | Filters: `document`, `author`, `top_level`, `search` |
| Comments | GET / PUT / DELETE | `/api/comments/{id}/` | Author only for edits |
| Comments | GET | `/api/comments/{id}/replies/` | Threaded replies |
| Tags | POST / GET | `/api/tags/` | `?name=`, `?min_documents=` |
| Audit Logs | GET | `/api/audit-logs/` | Filters: `action`, `model_name`, `object_id`, `actor`, dates |

## Roles

| Role | Read | Create / edit documents | Manage workspace & members |
|------|------|-------------------------|----------------------------|
| admin | yes | yes | yes |
| editor | yes | yes | no |
| viewer | yes | no | no |

Any member can comment. The workspace creator is added as `admin` automatically.

## Implementation notes

- **Transactions:** workspace creation, document create/update (with version), member add, and tag changes run inside `transaction.atomic()`, and the matching `AuditLog` is written in the same block.
- **Versioning:** `version_number = document.versions.count() + 1`, computed inside the atomic block with the document row locked (`select_for_update`).
- **Signals:** `apps/documents/signals.py` writes an `AuditLog` on every `Document` save; connected in `DocumentsConfig.ready()`. Django sets `_state.adding` to `False` before `post_save` runs, so a `pre_save` receiver records `instance._state.adding` and the `post_save` receiver reads it back to decide between `created` and `updated`.
- **Rollback demo:** with `DJANGO_DEBUG=True`, add `?simulate_failure=true` to a document create or update. The request raises after the document, version and audit log are written, and the response confirms that everything was rolled back. Check the list and audit log endpoints to confirm nothing was saved.
- **Error codes:** 400 for validation errors, 403 for role violations, 404 for missing objects, 409 for duplicate workspace members.

## Postman

Import `CollabDocs.postman_collection.json`. Folders: Users, Workspaces, Documents, Comments, Tags, Audit Logs. Run requests roughly top to bottom; IDs are saved into collection variables as you go. Change `base_url` if your server is not on `http://127.0.0.1:8000`.
