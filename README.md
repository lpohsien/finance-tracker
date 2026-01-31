# Finance Tracker Web App

A modern, full-stack finance tracker application featuring a React frontend, FastAPI backend, and Telegram Bot integration.

## Features

- **Dashboard**: Visual overview of income, expenses, and budget status.
- **Transactions**: Add, view, filter, and delete transactions.
- **Smart Parse**: Paste bank SMS/Notifications to automatically extract details (Regex + LLM).
- **Telegram Bot**: Continue using the existing bot alongside the web app.
- **Apple Shortcuts**: Integrate with Siri/Shortcuts via API Token.
- **Secure**: JWT Authentication and encrypted API Key storage.

## Tech Stack

- **Frontend**: React, TypeScript, Vite, Tailwind CSS, shadcn/ui, TanStack Query.
- **Backend**: FastAPI, SQLAlchemy (SQLite), Pydantic.
- **Deployment**: Docker (Multi-stage build).

## Prerequisites

- Docker & Docker Compose
- Python 3.13+ (for local dev)
- Node.js 20+ (for local dev)

## Quick Start (Docker)

1. **Clone the repo**
2. **Set up Environment**:
   Create a `.env` file (see `.env.example`).
   ```bash
   SECRET_KEY=your_secret_key
   ENCRYPTION_KEY=your_fernet_key # Generate via python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```
3. **HTTPS Setup**:
   The application requires HTTPS in Docker. You must generate certificates before running.
   ```bash
   mkdir -p certs
   openssl req -x509 -newkey rsa:4096 -keyout certs/key.pem -out certs/cert.pem -days 365 -nodes -subj '/CN=localhost'
   ```

4. **Run**:
   ```bash
   docker-compose up --build -d
   ```
   - Web App: `https://localhost` (Accept the self-signed certificate warning)
   - API Docs: `https://localhost/docs`

## Local Development

### Backend

1. Install `uv`: `pip install uv`
2. Create venv: `uv venv` && `source .venv/bin/activate`
3. Install deps: `uv pip install -e .[backend]`
4. Run:
   ```bash
   uvicorn api.main:app --reload
   ```

### Frontend

1. `cd frontend`
2. `npm install`
3. `npm run dev`

## Migration

To migrate legacy CSV data to the new SQLite database:

1. Ensure the server is stopped or DB is accessible.
2. Run the migration script:
   ```bash
   python scripts/migrate_csv_to_sql.py
   ```
   This will scan `data/` for user folders (e.g. `12345/`) and import them into `finance.db`.

## Apple Shortcuts Setup

1. Log in to the Web App.
2. Go to **Settings**.
3. Click "Generate Export Token".
4. Copy the token.
5. In your Shortcut:
   - URL: `https://<your-domain>/api/transactions/parse`
   - Method: POST
   - Headers: `Authorization: Bearer <your-token>`
   - Body (JSON):
     ```json
     {
       "bank_message": "Shortcut Input",
       "bank_name": "UOB",
       "timestamp": "Current Date (ISO)",
       "remarks": "Optional"
     }
     ```
