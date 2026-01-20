# Project Specification: Finance Tracker Web Application Migration

## 1. Overview
The goal is to transform the current Telegram-based Finance Tracker into a modern, full-stack web application. The core business logic (parsing, analytics, storage) will be preserved, while the interface will shift from CLI-style chat commands to a responsive, minimalistic web UI (Desktop & Mobile) and a robust RESTful API.

## 2. Architecture

### 2.1. Tech Stack
- **Frontend**: 
    - **Core**: React.js (via **Vite**) - Configured as a **Static Single Page Application (SPA)**.
    - **Language**: **TypeScript** (Strict mode) for type safety and better developer experience.
    - **Styling**: **Tailwind CSS** for utility-first styling.
    - **Components**: **shadcn/ui** (based on Radix UI) for accessible, mobile-first, and aesthetic components without the bloat of heavy component libraries.
    - **State Management**: React Query (TanStack Query) for handling async API state snappily.
    - **Deployment Strategy**: The frontend will be built into static assets (HTML/JS/CSS) and served via Nginx or the FastAPI static file mount, eliminating the need for a Node.js runtime process on the server (low RAM usage for GCP Free Tier).
- **Backend API**: Python FastAPI. It is modern, high-performance, and auto-generates Swagger documentation. It aligns well with the existing Python codebase.
- **Authentication**: JWT (JSON Web Tokens) with a secure password hashing mechanism (e.g., `passlib`, `bcrypt`).
- **Storage**:
    - **Database**: SQLite (or PostgreSQL) for all data persistence. This replaces the existing CSV file-based storage to improve concurrency, query performance, and data integrity.
        - `users` table: handling authentication (`username`, `password_hash`, `user_uuid`).
        - `transactions` table: storing transaction records linked to `user_uuid`.
        - `configuration` table: storing user settings (budgets, categories, keywords).

### 2.2. Folder Structure
The project structure will evolve:
```text
finance-tracker/
├── api/                # New: FastAPI application
│   ├── main.py         # Entry point
│   ├── auth.py         # Authentication logic
│   ├── routers/        # API Endpoints
│   └── dependencies.py # Dependency injection (e.g. get_current_user)
├── frontend/           # New: React Application
├── src/                # Existing core logic (refactored for reusability)
│   ├── analytics.py    # Existing
│   ├── parser.py       # Existing
│   ├── storage.py      # Existing
│   └── ...
├── data/               # Persistent data storage
└── docs/
```

## 3. Functional Requirements & API Mapping

The web application must expose the following features via REST endpoints. All endpoints requiring user context must be protected via JWT Authentication.

### 3.1. Authentication & User Management
- **Register**: `POST /auth/register`
    - Input: Username, Password
    - Action: Creates a new user entry and initializes their `data/<user_id>` directory (reuse `StorageManager.initialize_user_config`).
- **Login**: `POST /auth/token`
    - Input: Username, Password
    - Output: Access Token (JWT)
- **Get Export Token**: `GET /auth/export-token`
    - **Description**: Utility endpoint for power users (e.g. Apple Shortcuts).
    - **Action**: Returns the current valid JWT token in plaintext or a simple JSON wrapper, allowing the user to copy-paste it into external tools like Apple Shortcuts.

### 3.2. Transaction Management (Core)
Replaces `handle_message`, `/delete`, `/clear`.

- **Parse & Add Transaction**: `POST /api/transactions/parse`
    - **Description**: This is the primary endpoint for the Web UI "Quick Add" and the **Apple Shortcut** integration.
    - **Input**:
        - `bank_message` (string): The raw transaction text from the bank.
        - `bank_name` (string): e.g., "PayNow", "UOB", "DBS".
        - `timestamp` (string): ISO format timestamp or similar.
        - `remarks` (string, optional): User provided remarks.
    - **Logic**:
        - **API Level**: This endpoint **strictly requires structured JSON input**. It basically shifts the responsibility of "splitting the comma-separated string" to the client (Frontend or Shortcut).
        - **Frontend Responsibility**: If the user uses the "Smart Parse" text box in the Web UI (entering a comma-separated string like `msg,bank,time,remark`), the Frontend must parse/split this string into the JSON fields before sending it to this API.
    - **Requirement**: The response format must be friendly for display in Apple Shortcuts (e.g., a simple text summary field like `text_summary` in the JSON response, or just a clear success message).
        - **Apple Shortcut Responsibility**: The Shortcut must be updated to construct this JSON object from its inputs instead of concatenating them into a string.
        - **Backend Logic**: The backend passes these structured fields to the `TransactionParser`. The `TransactionParser` logic may need a new method (e.g., `parse_structured_data`) or an update to `parse_message` to handle pre-separated components, while retaining the regex/keyword logic for the `bank_message` content itself.
    - **Output**: Parsed transaction details and any budget alerts.

- **Manual Add Transaction**: `POST /api/transactions`
    - **Input**: JSON object with fields (amount, category, type, description, bank, timestamp).
    - **Logic**: Direct save avoiding parser heuristics if user inputs manually.

- **List Transactions**: `GET /api/transactions`
    - **Query Params**: `year`, `month`, `limit`, `offset`.
    - **Output**: List of transactions (JSON).

- **Delete Transaction**: `DELETE /api/transactions/{id}`
    - **Logic**: Reuse `StorageManager.delete_transaction`.

- **Clear All**: `DELETE /api/transactions`
    - **Logic**: Reuse `StorageManager.delete_all_transactions`.

### 3.3. Analytics & Stats
Replaces `/stats`, `/daily`.
The `AnalyticsEngine` in `src/analytics.py` must be refactored to either query the SQLite database directly for efficiency, or accept a list of transaction objects populated from a DB query for backward compatibility with logic.

- **Monthly Stats**: `GET /api/stats/monthly`
    - **Query Params**: `year`, `month`.
    - **Output**: JSON containing Total Income, Expense, Disbursed, Net, and Category Breakdown (sorted).

- **Daily Breakdown**: `GET /api/stats/daily`
    - **Query Params**: `year`, `month`.
    - **Output**: Daily spending vs daily budget limit (if set). Useful for charts/graphs on the frontend.

### 3.4. Budget & Configuration
Replaces `/viewbudget`, `/setbudget`, `/resetbudget`.

- **Get Budgets**: `GET /api/budgets`
    - **Output**: Current user config (budgets + big ticket threshold).

- **Set Budget**: `POST /api/budgets`
    - **Input**: `{"category": "transport", "amount": 500}` or `{"category": "threshold", "amount": 2000}`.
    - **Logic**: Reuse `StorageManager.update_user_budget`.

- **Reset Budgets**: `POST /api/budgets/reset`

### 3.5. Category & Keyword Management
Replaces `/viewcat`, `/addcat`, `/delcat`, `/viewkeys`, `/addkey`, `/delkey`.

- **Get Categories**: `GET /api/categories`
- **Modify Categories**: `POST /api/categories` (Add), `DELETE /api/categories` (Remove).
- **Get Keywords**: `GET /api/keywords`
- **Modify Keywords**: `POST /api/keywords` (Add), `DELETE /api/keywords` (Remove).

### 3.6. Data Export
Replaces `/export`.

- **Export CSV**: `GET /api/export` (optional, default all).
    - **Output**: Downloadable CSV file stream.
    - **Constraint**: The generated CSV **must be fully compatible** with the legacy CSV format (field names, order, formatting) used in the original `src/analytics.py`. This ensures users can still use offline scripts or tools designed for the CSV version
    - **Output**: Downloadable CSV file stream.

## 4. Frontend Specifications

The frontend should be a Single Page Application (SPA).

### 4.1. Design Philosophy
- **Aesthetic**: Modern, Clean, Dark/Light mode support.
- **Tooling**:
    - **uv**: Use `uv` (a modern, high-performance Python package installer) for all Python package management and virtual environment handling.

- **Minimalistic**: Avoid clutter. Key metrics should be visible at a glance.
- **Snappy**: Optimistic UI updates (update UI immediately before API confirms) where safe.
- **Responsive**:
    - **Desktop**: Dashboard view with side-by-side charts and transaction tables.
    - **Mobile**: Bottom navigation bar or hamburger menu. "Add Transaction" FAB (Floating Action Button).

### 4.2. Key Views/Pages
1.  **Auth Page**: Login / Register forms.
2.  **Dashboard (Home)**:
    - Summary Cards (Income, Expense, Remaining Budget).
    - Charts: Pie chart (Categories), Bar chart (Daily spending).
    - Recent Transactions list (Current month).
3.  **Transactions**:
    - Full list with filtering (Date, Category, Search).
    - Edit/Delete actions.
4.  **Analysis**
    - Charts and Graphs for deeper insights (Monthly trends, Category comparisons, custom date ranges).
    - Table to view transaction records with sorting and filtering capabilities (and custom date ranges).
        -  Allow user to visualize spending trends over time.
        - Allow user to export current view as CSV.
        - Add functionality for user to input a prompt and have LLM analyze their spending habits and provide suggestions based on current view, with reference to the input prompt. 
5.  **Add Transaction**:
    - **Tab 1: Smart Parse**: Text area to paste bank SMS/Text.
    - **Tab 2: Manual**: Form fields (Amount, Date, Category dropdown, Description).
6.  **Settings**:
    - Budget configuration (editable table/inputs).
    - Category & Keyword management (Tag editor interface).

## 5. Implementation Strategy

### Phase 1: Backend API Setup
1.  Initialize FastAPI project structure.
2.  Implement `AuthService` (User DB management).
3.  Wrap existing `StorageManager` logic into API dependencies.
4.  Implement `POST /api/transactions/parse` to verify parser logic works via HTTP.

### Phase 2: Core Frontend
1.  Scaffold React app.
2.  Build Auth screens and state management.
3.  Build Dashboard with dummy data, then connect to API.

### Phase 3: Advanced Features & Compatibility
1.  Implement settings (Budgets/Categories).
2.  Implement Export functionality.
3.  Test Apple Shortcut integration against `POST /api/transactions/parse`.

## 6. Migration of storage.py`**: **Major Refactor Required**. Transition from CSV read/write to SQL Alchemy (or raw SQLite) patterns. Must include a migration script to import existing `.csv` transaction files into the new SQLite schema. The class interface should remain similar if possible to minimize disruption, but internal implementation will change entirely.
- **`src/analytics.py`**: Refactor to support data fetching from the new SQL backend.
- **`src/bot_interface.py`**: This file will be *deprecated* or kept as a separate entry point if dual-support (Telegram + Web) is desired. The core logic inside `handle_message`, `stats_commands`, etc., should be extracted into service functions if not already clean, so both the Bot and the API can call them.
- **`src/auth.py` (New)**: Implement User model and auth flow. Needs to handle the generation of unique IDs for new web users that are compatible with the folder structure (string-based IDs).

## 7. Configuration for Apple Shortcuts
The User should be able to create a Shortcut that:
1.  Accepts "Shortcut Input" (Text, or multiple inputs).
2.  Constructs a Dictionary/JSON with keys: `bank_message`, `bank_name`, `timestamp`, `remarks`.
3.  Get Contents of URL `https://<deployed-domain>/api/transactions/parse`.
    - Method: POST.
    - Headers: `Authorization: Bearer <token>`, `Content-Type: application/json`.
    - Body: File/JSON (The constructed dictionary).


## 8. Documentation Requirements (README.md)
The project `README.md` must be completely updated to reflect the new architecture. It should include clear, step-by-step guides for:

- **Prerequisites**: Instructions to install `uv` (Python), Node.js, or Docker.
    - **Backend**: Creating the virtual environment and installing dependencies using `uv` (`uv venv`, `uv pip install -r requirements.txt`), and running the FastAPI dev server.
    - **Frontend**: Installing node modules (`npm install`) and running the Vite dev server (`npm run dev`).
    - **Database**: Instructions on how to initialize the SQLite database or run migrations.

- **Local Development (Host)**:
    - **Backend**: Creating the virtual environment, installing dependencies (`pip install -r requirements.txt`), and running the FastAPI dev server (`uvicorn api.main:app --reload`).
    - **Frontend**: Installing node modules (`npm install`) and running the Vite dev server (`npm run dev`).
    - **Database**: Instructions on how to initialize the SQLite database or run migrations.

- **Local Development (Docker)**:
    - Provide a comprehensive `Dockerfile` supporting a multi-stage build (Node build -> Python runtime).
    - Ensure the Docker setup handles both frontend (npm build) and backend (python packages via `uv`) dependencies efficiently.

- **GCP Deployment (Free Tier Optimization)**:
    - **Build Process**: Building the static React assets (`npm run build`) and configuring FastAPI to serve the `dist/` folder as a static mount
    - **Build Process**: Building the static React assets (`npm run build`) and configuring FastAPI to serve the `dist/` folder as a static mount (this avoids running a separate Node server in production).
    - **Dockerfile**: Updating the `Dockerfile` to perform a multi-stage build:
        1.  **Stage 1 (Node)**: Build React app to static files.
        2.  **Stage 2 (Python)**: Copy static files to FastAPI directory and install Python dependencies.
    - **Deploy**: Instructions for deploying the single container to Google Cloud Run or App Engine.
    - **Environment Variables**: Listing all required env vars (SECRET_KEY, DATABASE_URL, ALLOWED_ORIGINS) and how to set them in the GCP console.

## 9. Infrastructure Migration & Docker Workflow
To support a seamlessly containerized workflow for both development and deployment, the codebase structure must be updated:

1.  **Dependency Specification**:
    -   **Backend**: Update the `pyproject.toml` (standard for `uv` and modern python) to define backend dependencies. Generate a `requirements.txt` from it for Docker compatibility if needed, or use `uv` directly in Docker.
    -   **Frontend**: Ensure `package.json` and `package-lock.json` are in the root of the `frontend/` directory.

2.  **Docker Configuration (`Dockerfile`)**:
    Implement a multi-stage build strategy in a single `Dockerfile` at the project root:
    -   **Stage 1: Frontend Build (Node.js)**
        -   Base image: `node:20-alpine` (or similar lightweight)
        -   Copy `frontend/package*.json` -> `npm ci`
        -   Copy `frontend/` source code -> `npm run build` (outputs to `frontend/dist/`)
    -   **Stage 2: Backend Runtime (Python)**
        -   Base image: `python:3.13-slim` (or 3.12)
        -   Install `uv`: `pip install uv`
        -   Copy `pyproject.toml` / `requirements.txt` -> `uv pip install --system -r requirements.txt`
        -   Copy backend code (`api/`, `src/`) to `/app`.
        -   **Critical**: Copy the build artifacts from Stage 1 (`/app/frontend/dist`) to `/app/static` (or where FastAPI serves static files).
        -   Entrypoint: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`

3.  **Local Development via Docker Compose (`docker-compose.yml`)**:
    Create a `docker-compose.yml` to spin up the full stack locally without installing Python/Node on the host (optional but recommended):
    -   **Service: `frontend`**:
        -   Image: `node:20-alpine`
        -   Command: `npm run dev -- --host`
        -   Volumes: `./frontend:/app` (for hot reloading)
    -   **Service: `backend`**:
        -   Image: `python:3.11-slim`
        -   Command: `uvicorn api.main:app --reload --host 0.0.0.0`
        -   Volumes: `./src:/app/src`, `./api:/app/api`, `./data:/app/data` (persistence)
    -   **Proxy/Network**: Ensure frontend requests to `/api` are proxied to the backend service.

4.  **Ignore Files**:
    -   Update `.dockerignore` to exclude `node_modules`, `__pycache__`, `.git`, `venv`, etc., preventing context bloat.

