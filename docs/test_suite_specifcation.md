** Initial Prompt **
You are an expert full stack software engineering with good experience in context and prompt engineering as well as AI assisted workflow.

Base on the repo, help me develop a full, self-contained test suite that can be run in the docker environment using a single command, and covers all functionalities across front and backend, as well as all APIs. Both the positive and negative test cases should be implemented so as to check for correctness as well as error handling. DIfferent inputs should also be tested, for example modifying different fields for adding or editing transactions or adding/modifying tracking items. 

For API endpoint testing, since it requires the API token, there should also be a fully integrated test sequence that starts with simulating a user registrating for a new account and obtaining the API key to acccess the various API. Only then the API token will be used to for testing all the API endpoints. At the end of the API testing, the test users should be deleted by simulating the user deleting his own account. If there were no error during the testing, the user account can be deleted without choosing to export the user data. On the other hand, choose the download user data option if any error related to storage occurred during the testing so as to help in debugging. The bottomline is, the test user should always have all his data removed from the sqlite db by the end of the testing no matter if the test passed or failed

Note that for testing LLM-related functionality, do it sparingly (i.e. throughout the whole testing no matter frontend, backend, or API, there can be at most 3 instances of actual API call to google ai for the gemini model). Also provide an convenient way for the developer to skip testing the API/functionality that calls the google gemini API. 

Write out the full instruction for a coding agent (including overview, key context, key constraints, detailed plans, etc). Append it to docs/test_suite_specification.md under the agent-generated plan section. Do not modify the initial prompt section.

**Gemini3-pro Software Testing Guide**
The goal is to maximize "confidence-per-line-of-code" while keeping the overhead low.
This guide focuses on a "Lean & Modern" stack that prioritizes speed, developer experience (DX), and reliability.
1. The 2026 Testing Stack
These tools are the industry standards for 2026: they are open-source, lightweight, and deeply integrated with the Docker/Container ecosystem.
| Layer | Recommended Tool | Why? |
|---|---|---|
| Test Runner | pytest | The undisputed standard. Modular fixtures and a massive 2026 plugin ecosystem. |
| Unit/Logic | pytest + stdlib | Python 3.13’s improved unittest.mock and typing support make it very lean. |
| Integration | Testcontainers | Managed "real" dependencies (Postgres, Redis) inside Docker. No more mocking the DB. |
| System/E2E | Playwright | Faster and more stable than Cypress/Selenium. Excellent Python 3.13 asyncio support. |
| API Testing | HTTPX | Modern, async-first alternative to requests for testing your service boundaries. |
2. Unit Testing Best Practices (Python 3.13)
Focus on pure logic and data transformations. Avoid mocking external world here; save that for integration tests.
 * Property-Based Testing: Use Hypothesis for critical business logic. It generates edge-case data you’d never think of.
 * Type-Driven Assertions: Leverage Python 3.13’s enhanced type hinting. Use isinstance and TypeGuard in your assertions to ensure your data shapes are correct at runtime.
 * Parallelization: Use pytest-xdist to run unit tests in parallel. In 2026, even small projects benefit from sub-second test runs on multi-core dev machines.
3. Integration & System Testing (The "Docker-First" Way)
Since you are using Docker, do not use "mocks" for your database or message broker. Use Testcontainers.
The Workflow:
 * Ephemeral Dependencies: Use testcontainers-python to spin up a real Postgres/Redis container only for the duration of the test.
 * Service Isolation: Define a docker-compose.test.yml that mirrors production but uses lightweight "distroless" or Alpine-based images to speed up startup.
 * Network Aliasing: Ensure your test runner can reach services via Docker network aliases (e.g., http://api:8000) to match your production config.
> 
4. Full System / E2E Testing with Playwright
E2E tests should be "thin." Focus on the "Happy Path" and Critical Failures (Auth, Checkout, Data Entry).
 * Auto-Wait: Playwright automatically waits for elements to be actionable. Use this to eliminate "flaky" tests common in older frameworks.
 * State Reuse: Authenticate once, save the storage state (cookies/local storage), and reuse it across all tests to save time.
 * Trace Viewer: In CI, always save "traces." This allows you to "time-travel" through the test execution (DOM, network, logs) when a failure occurs in the pipeline.
5. CI/CD & Docker Guidelines for 2026
Your Dockerfile and CI pipeline are part of your test suite.
 * Multi-Stage Builds: Use a test stage in your Dockerfile.
   FROM python:3.13-slim AS base
...
FROM base AS test
RUN pip install pytest httpx
CMD ["pytest"]

 * Fail Fast: Order your CI: Lint (Ruff) -> Unit Tests -> Integration Tests -> E2E.
 * Observability Hooks: Configure pytest to output JUnit XML or JSON. Modern 2026 CI agents (like GitHub Actions or GitLab Runner) use this to provide instant "Self-Healing" suggestions or AI-driven root cause analysis.
Reference Links for Your LLM/Agent
 * Pytest Documentation: https://docs.pytest.org/
 * Playwright Python: https://playwright.dev/python/docs/intro
 * Testcontainers Python: https://testcontainers-python.readthedocs.io/
 * Python 3.13 Release Notes: https://docs.python.org/3.13/whatsnew/3.13.html
 * Docker Best Practices (2026): https://docs.docker.com/build/building/best-practices/


**System Specific Test Recommendations (Gemini3-pro)**
With your specific stack (FastAPI 0.109+, React 19, and Python 3.13), we can move from general advice to a concrete, implementation-ready strategy. Since you're using uv and Vite 7, your testing loop will be exceptionally fast.
Here is the 2026 Engineering Guide for your specific architecture.
1. Modern Testing Stack (2026 Editions)
| Layer | Recommended Tool | Role in Your Stack |
|---|---|---|
| Backend Runner | pytest | Handles FastAPI, SQLAlchemy, and Python 3.13 logic. |
| Frontend Runner | Vitest 3.0+ | Blazing fast unit/component tests for Vite 7/React 19. |
| End-to-End | Playwright | Validates the full flow from React UI to the Telegram Bot. |
| API Client | HTTPX | Async client for testing FastAPI endpoints (better than requests). |
| Data Mocking | Mock Service Worker (MSW) | Mocks API calls for React/Tanstack Query components. |
2. Backend Strategy (Python 3.13 + FastAPI + SQLAlchemy)
A. The "Clean DB" Pattern (SQLite)
Since you're using SQLite, you don't need complex Docker DB setups for integration tests. Use a memory-based SQLite instance for tests to ensure zero disk I/O and instant resets.
 * Fixture Logic: Create a pytest fixture that generates a new SQLAlchemy engine/session for every test function.
 * Python 3.13 Benefit: Use the new typing.TypeAlias and improved asyncio features to keep your test signatures clean.
B. Testing Google GenAI & Telegram Bot
Never hit the real APIs in unit tests.
 * GenAI: Mock the google.generativeai.GenerativeModel.generate_content call. Assert on the prompt structure you send, not just the string response.
 * Telegram: Use python-telegram-bot’s built-in Application.process_update() to simulate incoming messages without a real bot token.
3. Frontend Strategy (React 19 + Vite 7 + Tanstack Query)
A. Testing React 19 Components
React 19's new use() hook and Actions change how we test.
 * Component Tests: Use Vitest with React Testing Library. Ensure you wrap components in a QueryClientProvider fixture to support Tanstack Query hooks.
 * Radix UI: Since Radix is headless, focus your tests on Aria-Attributes and keyboard navigation. Playwright is excellent for this.
B. The MSW (Mock Service Worker) Advantage
Instead of mocking fetch or axios, use MSW to intercept network requests at the browser level. This allows your Tanstack Query logic to run exactly as it would in production.
4. Full System Integration (Docker + uv)
The "uv-Powered" Dockerfile
Your Dockerfile should leverage uv for near-instant dependency installation in CI.
# Use multi-stage build for testing
FROM python:3.13-slim as tester
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
WORKDIR /app
COPY pyproject.toml .
RUN uv sync --frozen
# Run tests
CMD ["uv", "run", "pytest"]

5. Summary Guide for LLM Agents
 * Unit Tests: Pytest (Backend) / Vitest (Frontend). High coverage on business logic/schemas.
 * Integration: FastAPI TestClient + HTTPX. Real SQLite (in-memory).
 * E2E: Playwright. Focus on the Telegram Bot -> FastAPI -> React UI loop.
 * Mocks: MSW for Frontend, unittest.mock for GenAI.
Essential Reference Links
 * FastAPI Testing: fastapi.tiangolo.com/tutorial/testing/
 * Vitest (Vite-native testing): vitest.dev/guide/
 * Tanstack Query Testing: tanstack.com/query/latest/docs/framework/react/guides/testing
 * Python Telegram Bot Testing: github.com/python-telegram-bot/python-telegram-bot/wiki/Testing
 * uv Documentation: docs.astral.sh/uv/
 * React 19 Testing Notes: react.dev/blog/2024/12/05/react-19
Would you like me to write a specific conftest.py that sets up the FastAPI + SQLAlchemy (SQLite) + uv testing environment for you?


## Agent Instruction: Comprehensive Dockerized Test Suite

### 1. Overview
The goal is to implement a robust, fully containerized test suite for the Finance Tracker application. This suite will execute via a single Docker Compose command, instantiating a dedicated ephemeral environment that tests the entire application stack—from API endpoints to backend logic and simulated frontend interactions. The system must ensure strict data hygiene, ensuring no test data persists after execution.

### 2. Key Context
*   **Repo Structure**: Python/FastAPI backend (`api/`, `src/`), React frontend (`frontend/`), SQLite database.
*   **Existing Tests**: Unit tests exist in `tests/`. These should be reorganized.
*   **Docker**: Project uses `docker-compose.yml` for production/dev. We need a parallel `docker-compose.test.yml`.
*   **Auth Flow**: The API requires JWT authentication. The test suite must act as a real user: Register -> Get Token -> Perform Actions -> Delete Account.

### 3. Key Constraints
1.  **Single Command Execution**: Must run with `docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit`.
2.  **Strict Data Cleanup**: The test user **MUST** be deleted at the end of the session, regardless of Pass/Fail status.
3.  **Conditional Debug Export**:
    *   **Success**: Delete user directly.
    *   **Failure**: Call API to export user data (for debugging) -> Save to volume -> Delete user.
4.  **LLM Rate Limiting**:
    *   Max **3** live calls to Google Gemini API across the entire suite.
    *   Provide `--skip-llm` flag to bypass these tests.
    *   All other LLM interactions must be mocked.
5.  **Scope**: Cover positive cases (correct functionality) and negative cases (error handling, invalid inputs).

### 4. Detailed Implementation Plan

#### Phase 1: Test Infrastructure & Docker Configuration
1.  **Create `Dockerfile.test`**:
    *   Inherit from the main backend `Dockerfile` or a compatible Python image.
    *   Install test dependencies (`pytest`, `pytest-asyncio`, `httpx`, `faker`, `respx`).
    *   Set entrypoint to run pytest.
2.  **Create `docker-compose.test.yml`**:
    *   `backend`: Run the API with `DATABASE_URL=sqlite:///./data/test.db`.
    *   `test_runner`:
        *   Build from `Dockerfile.test`.
        *   Depends on `backend` (wait for health check).
        *   Mount `./tests` to `/app/tests` and `./data` to `/app/data` (for debug dumps).
        *   Environment: `API_BASE_URL=http://backend:8000`.

#### Phase 2: Pytest Fixtures (`tests/conftest.py`)
Centralize the lifecycle management logic here.
1.  **`api_client`**: Async `httpx.AsyncClient` for general API calls.
2.  **`authenticated_user` (Scope: Session or Module)**:
    *   **Setup**:
        *   Generate random username/password.
        *   POST `/api/auth/register` (Assert 200).
        *   POST `/api/auth/token` (Get Access Token).
        *   Configure client headers with `Bearer <token>`.
    *   **Yield**: The authenticated client.
    *   **Teardown**:
        *   Check test session status (did any test fail?).
        *   **If Failed**: GET `/api/configuration/export` -> Write JSON to `/app/data/debug_<timestamp>.json`.
        *   **Always**: DELETE `/api/auth/delete` (Assert 200/204) to scrub data.
3.  **LLM Mocking**:
    *   Create a fixture that patches `google.generativeai.GenerativeModel.generate_content`.
    *   Implement a counter. Allow the first 3 calls to pass through (if `--skip-llm` is not set), then return mocked responses for subsequent calls.

#### Phase 3: Test Suite Organization
Refactor the `tests/` directory:
*   `tests/unit/`: Move existing logic tests (`test_analytics.py`, `test_parser.py`, etc.) here. Run these first.
*   `tests/integration/`: Create new API-driven tests here.

**New Integration Tests to Implement:**
1.  **`test_auth_flow.py`**:
    *   Registering duplicate users (Expect 400).
    *   Login with wrong password (Expect 401).
2.  **`test_transactions_lifecycle.py`**:
    *   Create transaction (verify fields).
    *   Edit transaction (verify changes).
    *   Edit with invalid data (Expect 422).
    *   Delete transaction.
3.  **`test_analytics_api.py`**:
    *   Seed data via Transaction API.
    *   Call Analytics API and verify aggregation logic matches seeded data.
4.  **`test_tracking_items.py`**:
    *   CRUD on tracking items (e.g., specific keywords).
5.  **`test_llm_parsing.py`**:
    *   Test the `parse` endpoint.
    *   Use the `llm_limiter` fixture to ensure only 3 real calls go out.

#### Phase 4: Execution Scripts
1.  Update `docs/test_suite_specifcation.md` (this file) with the final usage instructions.
2.  The usage should be simple:
    ```bash
    # Run full suite
    docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
    
    # Run without LLM calls
    TEST_ARGS="--skip-llm" docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
    ```

### 5. Final Checklist for Agent
- [ ] Are test deps isolated in `Dockerfile.test`?
- [ ] Does `conftest.py` successfully catch failures and export data?
- [ ] Is the "Register -> Test -> Delete" loop robust against crashes?
- [ ] coverage report generated? (Optional but recommended).

### 6. System Framework and Versions**
Backend (Python)
- Language: Python 3.13 (via Dockerfile and pyproject.toml/uv)
Web Framework: FastAPI >=0.109.0
- Server: Uvicorn >=0.27.0
- ORM / Database: SQLAlchemy >=2.0.25 (using SQLite)
- Data Validation: Pydantic >=2.6.0
- Package Management: uv (installed in Dockerfile)
- AI SDK: Google GenAI >=1.56.0
- Bot Framework: Python Telegram Bot >=21.0
Frontend (React)
- Framework: React ^19.2.0
- Build Tool: Vite ^7.2.4
- Language: TypeScript ~5.9.3
- Routing: React Router DOM ^7.12.0
- Data Fetching: Tanstack Query (React Query) ^5.90.19
- Styling: Tailwind CSS ^4.1.18
- UI Components: Radix UI (Primitives)
- Visualization: Recharts ^3.6.0
Infrastructure
- Runtime Base Images: python:3.13-slim and node:20-alpine
- Web Server: Nginx (alpine)

## Finalized Instruction: Comprehensive Dockerized Test Suite

### 1. Overview
We will implement a modern, containerized test suite for the Finance Tracker application, leveraging the "Lean & Modern" stack guidelines (Pytest, HTTPX, Playwright). The suite will run via a single Docker Compose command, creating an ephemeral, isolated environment to test the full stack (Frontend + Backend + API).

### 2. Tech Stack & Architecture
*   **Test Runner**: `pytest` (running inside a Docker container).
*   **API Testing**: `httpx` (async, modern) for backend interactions.
*   **E2E/Frontend Testing**: `playwright` (headless) for critical user journeys.
*   **Database**: SQLite (file-based). We will use a dedicated `test.db` for the test session, ensuring isolation from dev/prod data.
*   **Orchestration**: `docker-compose.test.yml` to spin up the Backend, Frontend (served via Nginx or Vite preview), and the Test Runner.

### 3. Key Constraints & Requirements
1.  **Single Command**: `docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit` must trigger the entire suite.
2.  **Data Hygiene**: The test runner must handle user lifecycle:
    *   **Setup**: Register a unique test user.
    *   **Teardown**: **ALWAYS** delete the user accounts at the end of the session.
    *   **Debug**: If a test fails, export user data to `./data/debug_<timestamp>.json` *before* deletion.
3.  **External API Calls**:
    *   All external API calls (e.g., Telegram Bot, generative AI) should be mocked as much as possible to avoid network dependencies during tests.
    *   LLM Calls:
        *   Strictly limit real Google Gemini API calls to **3** max per suite run.
        *   Use `unittest.mock` to patch `google.generativeai` for the rest.
        *   Implement a Pytest fixture `llm_mock` that enforces this count and switching logic.
    *   Support a `--skip-llm` flag to bypass real calls entirely.
    *   Support a `--skip-external-api` flag to bypass real calls to all external services, including both LLM and Telegram.

### 4. Implementation Plan

#### Phase 1: Docker Configuration
1.  **`Dockerfile.test`**:
    *   Base: `python:3.13-slim`.
    *   Install: `pytest`, `pytest-asyncio`, `pytest-playwright`, `httpx`, `faker`, `respx`.
    *   Run `playwright install --with-deps chromium` to set up the browser.
    *   Entrypoint: `pytest`.
2.  **`docker-compose.test.yml`**:
    *   **`backend`**: Run the API with `DATABASE_URL=sqlite:///./data/test_db.sqlite`.
    *   **`frontend`**: Build the frontend (e.g., `nginx` serving built assets or `vite preview`) to ensure we test the production build, not dev server. Expose on port `3000` (internal).
    *   **`test_runner`**:
        *   Depends on `backend` (healthcheck: curl `/api/health`) and `frontend`.
        *   Env: `API_BASE_URL=http://backend:8000`, `FRONTEND_URL=http://frontend:3000`.
        *   Mounts: `./tests:/app/tests`, `./data:/app/data` (for debug exports).

#### Phase 2: Pytest Fixtures (`tests/conftest.py`)
1.  **`api_client`**: Async `httpx.AsyncClient` for general API calls.
2.  **`auth_user` (Session Scope)**:
    *   **Setup**: Register a new user with random creds. Retrieve JWT.
    *   **Yield**: An `httpx.AsyncClient` with the Bearer token header pre-set.
    *   **Teardown**:
        *   Check for test failures (using `pytest_runtest_makereport` hook).
        *   If failed -> Call `GET /api/configuration/export`. Save to file.
        *   **Always** -> Call `DELETE /api/auth/delete`.
3.  **`llm_context`**:
    *   A fixture that wraps `google.generativeai.GenerativeModel.generate_content`.
    *   Maintains a counter. First 3 calls -> Pass through (unless `--skip-llm`). 4th+ call -> Return mocked response.

#### Phase 3: Test Organization
Refactor `tests/` into proper layers:
*   **`tests/unit/`**: Pure logic tests (Parsing, Models). Fast, no DB/Network.
*   **`tests/integration/`**: API-level tests.
    *   `test_auth.py`: Register, Login, Invalid Creds.
    *   `test_transactions.py`: CRUD, Filters.
    *   `test_analytics.py`: Verify calculations matches seeded transaction data.
*   **`tests/e2e/`**: Playwright tests.
    *   `test_happy_path.py`: Login -> Add Transaction -> View on Analytics Chart -> Logout.

#### Phase 4: Execution & Scripts
Update `README.md` or `docs/` with the execution command.
Ensure the `data/` folder permissions allow the docker container to write the SQLite file and debug exports.

### 5. Final Checklist for Agent
- [ ] **Docker**: `docker-compose.test.yml` and `Dockerfile.test` created?
- [ ] **Depedencies**: `httpx`, `pytest-playwright` included?
- [ ] **Fixtures**: `auth_user` handles Create -> Export(on fail) -> Delete lifecycle?
- [ ] **LLM**: Mocking logic implemented with max-3-real-call limit?
- [ ] **E2E**: At least one critical flow covered by Playwright?
