# Analysis Tab Specification

## 1. Transaction View

### 1.1 Overview
The Transaction View serves as the central hub for reviewing and managing transactions. It provides a tabular or list interface displaying individual transactions with powerful filtering capabilities to help users analyze their spending habits.

### 1.2 Default State
*   **Initial Load:** When the view is accessed without any active filters, it **filters by the current month**.
*   **Transactions Displayed:** All transactions belonging to the user for the current month.

### 1.3 Filtering Capabilities
The view allows users to filter visible transactions based on the following criteria. Filters are additive (AND logic).

1.  **Time Range:**
    *   Selectable ranges: Custom Date Range (Start Date, End Date), Month, Year.
2.  **Category:**
    *   Multi-select dropdown of existing user categories.
3.  **Account:**
    *   Multi-select dropdown of unique accounts found in the user's transaction history.
4.  **Type:**
    *   Multi-select dropdown of transaction types (e.g., Transfer, Card, PayNow).
5.  **Bank:**
    *   Multi-select dropdown of banks associated with the user.
6.  **Description Keywords:**
    *   Text input field for searching within the `description` field.
    *   **Search Options (Toggles):**
        *   **Match Case:** If enabled, the search is case-sensitive.
        *   **Use Regex:** If enabled, the search string is treated as a Regular Expression (e.g., `.*grab.*`).
        *   *Default:* Case-insensitive, substring match.

## 2. Export Transactions

### 2.1 Functionality
*   Users can export the currently visible transactions (based on active filters in the Transaction View) to a CSV file.
*   **Button:** "Export CSV" located near the filters or the list header.

### 2.2 CSV Structure
The exported CSV **must** strictly adhere to the system's internal data structure to ensure it can be re-imported to fully reconstruct the database state.

**Columns:**
`id`, `timestamp`, `bank`, `type`, `amount`, `description`, `account`, `category`, `raw_message`, `status`

*   **id:** UUID of the transaction.
*   **timestamp:** ISO 8601 formatted string.
*   **bank:** Name of the bank.
*   **type:** Transaction type (e.g., 'Card', 'Transfer').
*   **amount:** Numeric value (negative for expenses, positive for income).
*   **description:** Transaction description.
*   **account:** Account identifier (e.g., last 4 digits).
*   **category:** Assigned category (lowercase).
*   **raw_message:** Original raw message/data if available.
*   **status:** Current status string (e.g., "Cleared", "Manual Entry").

## 3. Import Wizard

### 3.1 Overview
A step-by-step wizard to allow users to bulk-import transactions via CSV upload. This feature is critical for restoring backups or migrating data.

### 3.2 Workflow

#### Step 1: Upload
*   User uploads a CSV file.
*   **Structure Validation:** System checks if the CSV headers match the required columns (see [2.2 CSV Structure](#22-csv-structure)).
*   **Error Handling:**
    *   **Missing Columns:** Prompt user to add missing columns.
    *   **Extra Columns:** Prompt user to remove or map extra columns (or ignore them with a warning).
    *   *System stops if structure is invalid.*

#### Step 2: Row-Level Validation & Processing
The system iterates through each row of the CSV.

1.  **UUID Generation:**
    *   If `id` column is empty, generate a new UUIDv4 using the transaction details and current time (similar to existing logic).
    *   If `id` is present, use it (checking for duplicates in DB; regenerate for the new transaction if exists).

2.  **Category Normalization:**
    *   Convert `category` value to **lowercase**.

3.  **Category Validation:**
    *   Check if the row's `category` exists in the user's defined Category List.
    *   **If Category Exists:** Proceed to import.
    *   **If Category is Missing (New Category):**
        *   *Scenario:* A category in the CSV (e.g., "subscriptions") is not in the user's config.
        *   *Prompt User:* "Category 'subscriptions' not found. Action?"
            *   **Option A: Create Category:** Automatically add "subscriptions" to the user's category list and add "subscriptions" as a keyword for itself.
            *   **Option B: Skip & Cache:** Do not import this row; mark it for the Error CSV.
        *   *Optimization:* If the user chooses "Create Category" for "subscriptions", apply this decision to all subsequent rows with "subscriptions" in the same import batch without re-prompting.

4.  **General Data Validation:**
    *   Check for valid Timestamp format.
    *   Check for valid Amount format.
    *   *Failure:* If any parsing fails, mark the error in its `status` column before **Skip & Cache**.

#### Step 3: Completion & Error Report
*   **Success Summary:** Display count of successfully imported transactions.
*   **Error Handling (Cached Failures):**
    *   If any rows were skipped due to validation errors (or user choice to skip new categories), generate an **Error CSV**.
    *   **Error CSV Format:** Same as standard CSV, but the `status` column is repurposed to contain the **Validation Error Message** (e.g., "Invalid Timestamp", "Category 'xyz' not found").
    *   **Action:** Automatically download the Error CSV or provide a "Download Failed Rows" button so the user can rectify and re-import.

## 4. Systems Constraints & Logic

*   **Reconstructability:** The export/import cycle must be lossless for core data fields. Importing an export must result in an identical database state (excluding internal timestamps like 'created_at' if not in CSV).
*   **Category Creation Side-effect:** Creating a new category during import updates the User Configuration (adds category to list, adds category name as a keyword). The user is notified of this update at the end of the import.
*   **Performance Considerations:** For large CSV files, consider batch processing and providing progress feedback to the user.
*   **Error Handling:** Robust error handling and user prompts are essential to guide users through resolving import issues.
*   **Security Considerations:** Validate and sanitize all CSV inputs to prevent injection attacks or malformed data entries.
*   **Web/Mobile Compatibility:** Ensure the import/export functionalities works seamlessly across different devices and screen sizes and are consistent with the overall UI/UX design of the application. All texts and buttons must be accessible and fit within the viewport.
*   **Dev environment:** Assume that the project is running in docker containers for both frontend and backend during development and testing. All tests and execution that interacts with the live system should be done within the docker environment to ensure consistency.