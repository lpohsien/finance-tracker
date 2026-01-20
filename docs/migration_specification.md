<!-- 
This specification is optimized for automated coding agents. 
Instructions are precise. Follow file paths, json schemas, and library choices strictly.
-->

# Project Specification: Finance Tracker Web Application Migration

## 1. Overview
The goal is to transform the current Telegram-based Finance Tracker into a modern, full-stack web application. The core business logic (parsing, analytics, storage) will be preserved, while the interface will shift from CLI-style chat commands to a responsive, minimalistic web UI (Desktop & Mobile) and a robust RESTful API.

## 2. Architecture

### 2.1. Tech Stack
- **General Tooling**:
    - **uv**: Use `uv` for high-performance Python package management and virtual environment handling.
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
    - **Database**: SQLite (moving to `data/finance.db`) for all data persistence. This replaces the existing CSV file-based storage to improve concurrency, query performance, and data integrity.
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
│   ├── models.py       # Pydantic models & DB Schemas
│   └── dependencies.py # Dependency injection (e.g. get_current_user)
├── frontend/           # New: React Application
├── scripts/            # New: Migration and utility scripts
│   └── migrate_csv_to_sql.py
├── src/                # Existing core logic (refactored for reusability)
│   ├── analytics.py    # Existing
│   ├── parser.py       # Existing
│   ├── storage.py      # Existing (Refactored to use SQL)
│   └── ...
├── data/               # Persistent data storage (finance.db)
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
    - **Input (JSON strict)**:
        ```json
        {
          "bank_message": "string (raw SMS text)",
          "bank_name": "string (e.g. 'UOB')",
          "timestamp": "ISO8601 string",
          "remarks": "string (optional)"
        }
        ```
    - **Logic**:
        - **API Level**: This endpoint **strictly requires structured JSON input**.
        - **Clients (Frontend/Shortcut)**: Must parse raw text inputs into this JSON structure *before* sending.
            - *Frontend*: If using "Smart Parse" text box, JS logic splits the comma-separated string `msg,bank,time,remark` into the JSON fields.
            - *Shortcut*: The Shortcut must construct this JSON object from its inputs.
        - **Backend Logic**: Passes fields to `TransactionParser`. The parser should be updated to handle pre-separated components via a new method (e.g., `parse_structured_data`) while reusing existing regex logic for the `bank_message` content.
    - **Output**: Returns parsed transaction details and budget alerts. The response should include a simple `text_summary` field for Siri/Shortcuts to speak out.

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
    - **Constraint**: The generated CSV **must be fully compatible** with the legacy CSV format (field names, order, formatting) used in the original `src/analytics.py`. This ensures users can still use offline scripts or tools designed for the CSV version.

## 4. Frontend Specifications

The frontend should be a Single Page Application (SPA).

### 4.1. Design Philosophy
- **Aesthetic**: Modern, Clean, Dark/Light mode support.
- **Tooling**:
    - **Vite**: Fast build tool.
    - **npm/pnpm**: Frontend package management.
    - **Tailwind CSS**: Utility-first CSS framework.
    - **shadcn/ui**: Accessible, unopinionated component library.

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
    - Budget Overview/Alerts.
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
4.  Implement `POST /api/transactions/parse` to ensure parser logic works via HTTP, so as to enable integration with Apple Shortcuts.

### Phase 2: Core Frontend
1.  Scaffold React app.
2.  Build Auth screens and state management.
3.  Build Dashboard with dummy data, then connect to API.

### Phase 3: Advanced Features & Compatibility
1.  Implement settings (Budgets/Categories).
2.  Implement Export functionality.
3.  Test Apple Shortcut integration against `POST /api/transactions/parse`.

## 6. Storage Migration Strategy
- **`src/storage.py`**: **Major Refactor Required**.
    - Transition from CSV read/write to **SQLAlchemy** (async preferred) or raw **SQLite** patterns.
    - **Models**: structured tables for `User`, `Transaction`, `Budget`, `Category` are required.
    - **Interface**: The class interface (`add_transaction`, `get_transactions`, etc.) should remain similar to minimize disruption to `main.py` consumers, but the internal implementation will change entirely.
- **Migration Script (`scripts/migrate_csv_to_sql.py`)**:
    - A standalone script is required.
    - **Logic**: It must iterate through `data/<user_id>/transactions.csv` and `config.json` files.
    - **Action**: Insert parsed data into the new SQLite database (`data/finance.db`).
    - **Idempotency**: The script should be idempotent (safe to run multiple times).
- **`src/analytics.py`**: Refactor to support data fetching from the new SQL backend (or modifying the SQL query to return data in the shape `AnalyticsEngine` expects).
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

- **Prerequisites**: Instructions to install `uv` (Python), Node.js, and Docker.
- **Local Development**:
    - Quick start for setting up the development environment usinng either host or docker.
    - **Backend**: Creating the virtual environment and installing dependencies using `uv` (`uv venv`, `uv pip install -r requirements.txt`), and running the FastAPI dev server.
    - **Frontend**: Installing node modules (`npm install`) and running the Vite dev server (`npm run dev`).
    - **Database**: Instructions on how to initialize the SQLite database or run migrations via the `scripts/` folder.
- **Production Build**: How to build the frontend and serve it via FastAPI.

## 9. Infrastructure Migration & Docker Workflow
To support a seamlessly containerized workflow for both development and deployment:

### 9.1. Environment Variables (`.env`)
The application must support the following configuration via `.env` file or environment injection:
- `SECRET_KEY`: (Required) For JWT signing.
- `ALGORITHM`: (Default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: (Default: 30)
- `DATABASE_URL`: (Default: `sqlite:///./data/finance.db`)
- `CORS_ORIGINS`: Comma-separated list of allowed origins (e.g. `http://localhost:5173,https://myapp.com`).

### 9.2. Dependency Management
-   **Backend**: Update the `pyproject.toml` (standard for `uv` and modern python) to define backend dependencies. Generate a `requirements.txt` only if strictly needed by PaaS, otherwise use `uv` in Docker.
-   **Frontend**: Ensure `package.json` and `package-lock.json` are in the root of the `frontend/` directory.

### 9.3. Docker Configuration (`Dockerfile`)
Implement a multi-stage build strategy in a single `Dockerfile` at the project root:
1.  **Stage 1: Frontend Build (Node.js)**
    -   Base image: `node:20-alpine`
    -   Copy `frontend/package*.json` -> `npm ci`
    -   Copy `frontend/` source code -> `npm run build` (outputs to `frontend/dist/`)
2.  **Stage 2: Backend Runtime (Python)**
    -   Base image: `python:3.13-slim`
    -   Install `uv`: `pip install uv`
    -   Copy `pyproject.toml` -> `uv pip install --system -r pyproject.toml` (or requirements.txt)
    -   Copy backend code (`api/`, `src/`) to `/app`.
    -   **Critical**: Copy the build artifacts from Stage 1 (`/app/frontend/dist`) to `/app/static`.
    -   Entrypoint: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`

### 9.4. Local Development via Docker Compose
Create a `docker-compose.yml` to spin up the full stack locally:
-   **Service: `frontend`**: Image `node:20-alpine`, Command `npm run dev`, Volumes `./frontend:/app`.
-   **Service: `backend`**: Image `python:3.13-slim`, Command `uvicorn api.main:app --reload`, Volumes `./src:/app/src`, `./data:/app/data`.
-   **Proxy**: Configure Vite proxy or Nginx to route `/api` requests to `backend`.
-   **Ignore Files**: Update `.dockerignore` (exclude `node_modules`, `__pycache__`, `venv`).

