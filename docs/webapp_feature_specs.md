**Task: Implement "Tracking" Tab**
Create a new tab called "Tracking" allowing users to manage Goals (target to reach) and Limits (cap to stay under).

1. Data Model & Configuration
Allow the user to create tracking items with the following properties:
Type: Goal or Limit.
Filter criteria: Select specific Categories and/or a combination of Account + Transaction Type (e.g., UOB + Card).
Target Amount: Numeric value.
Period: Daily, Weekly, Monthly, or Annually.
Net Disbursements: Boolean flag.

2. Calculation Logic
Calculate "Current Spending" by summing transaction amounts that match the Filter and Period.
Net Disbursements Logic: If the boolean flag is true, find transactions matching the filter that are categorized as "disbursement" with a positive amount. Subtract these amounts from the Current Spending total.

3. UI/UX Requirements
Reuse the progress bar design from the "Overview" budget display.
Visual Distinction:
Limits: Visuals should incentivize keeping the bar low (e.g., green when low, red when exceeding).
Goals: Visuals should incentivize filling the bar (e.g., incomplete is neutral, filled is success).

**Task: Modify keyword matching logic for category parsing**
Update the category parsing logic to prioritize keyword matching in the following order:

1. **Remarks Check**: Check for keywords in the transaction remarks. If a match is found, return the category immediately.
2. **Description Check**: If no match in remarks, check for keywords in the transaction description.
3. **LLM Fallback**: If no keywords match in either remarks or description, fall back to the LLM for categorization.

**Task: Delete user accounts feature**
Add functionality in the settings page to allow users to delete their account.

1. **Initiation**:
    - Add a "Delete Account" button in the Settings page.
    - Clicking the button opens a warning modal triggering the deletion flow.

2. **Warning Modal**:
    - **Message**: Clearly warn that all configurations and transactions will be permanently deleted.
    - **Actions**:
        - **Cancel**: Close modal, abort deletion.
        - **Export Data**: Export ALL transactions of the current user as CSV (using existing function) and configurations as a separate CSV.
        - **Proceed**: Move to final confirmation.

3. **Final Confirmation**:
    - Require a second explicit confirmation (e.g., "Are you absolutely sure?").
    - **On Confirm**: 
        - Log the user out immediately.
        - Delete all user data from the database.
    - **On Cancel/Close**: Abort deletion.