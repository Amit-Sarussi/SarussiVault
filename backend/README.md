# LAN File Server (FastAPI)

Minimal FastAPI backend that exposes filesystem operations under a fixed sandbox root and serves the built frontend.

## Run
- Install deps: `pip install fastapi uvicorn`.
- Start server (from `backend/`): `uvicorn main:app --host 0.0.0.0 --port 8000`.
- Open `http://<host>:8000` from the LAN.

## Frontend build
- Place the Vite build output inside `backend/static/` (e.g., `index.html` and the `assets/` folder).
- Static files are mounted at `/` with SPA routing enabled.

## Path sandboxing
- All requests are resolved relative to `ROOT_DIR = /srv/files` (see `security.py`).
- Absolute paths, `..`, and any resolution that escapes the root are rejected.
- Symlinks that would leave the root are blocked when paths are resolved.

## API highlights
- `GET /api/list?path=dir` — list directory entries.
- `GET /api/file?path=file` — stream a file.
- `POST /api/upload?path=dir` — multipart upload, no overwrite.
- `POST /api/mkdir` — create a directory `{ "path": "parent", "name": "child" }`.
- `DELETE /api/delete?path=target` — delete file or directory (recursive for dirs).
- `POST /api/move` — rename/move `{ "src": "old", "dst": "new" }`, no overwrite.

## Notes
- The root directory is created at startup if missing.
- Errors are normalized to JSON; stack traces are not exposed.
- The backend is intended for trusted LAN environments only; no auth is provided.
