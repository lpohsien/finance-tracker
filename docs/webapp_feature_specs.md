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
Modify the logic to check if any keywords is found in remarks first. If a matching catergory can already be determined, return the category right away. If not, then check using the description only. Fall back to LLM if both fails