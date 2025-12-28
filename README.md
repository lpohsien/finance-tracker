# Finance Tracker Telegram Bot

A Telegram bot for tracking personal finances, designed to parse UOB transaction messages forwarded via Apple Shortcuts.

## Features

*   **Automated Parsing**: Extracts transaction details from UOB SMS (PayNow, Card).
*   **Smart Categorization**: Uses keywords and Google Gemini LLM to categorize transactions.
*   **Analytics**: Provides income/expense totals, category breakdowns, and budget alerts.
*   **Data Persistence**: Saves transactions to a CSV file (easily migratable).
*   **Secure**: Whitelists users to prevent unauthorized access.

## Project Structure

```
finance-tracker/
├── src/              # Source code
├── tests/            # Unit tests
├── data/             # Data storage (CSV)
├── Dockerfile        # Docker configuration
├── bot.service       # Systemd service file
├── pyproject.toml    # Dependencies
└── README.md         # Documentation
```

## Local Development

1.  **Prerequisites**: Python 3.13+, `uv` (optional but recommended).
2.  **Clone the repository**:
    ```bash
    git clone <repo_url>
    cd finance-tracker
    ```
3.  **Install dependencies**:
    ```bash
    pip install .
    # OR with uv
    uv pip install .
    ```
4.  **Configure Environment**:
    Create a `.env` file in the root directory:
    ```ini
    TELEGRAM_BOT_TOKEN=your_telegram_bot_token
    ALLOWED_USER_IDS=123456789,987654321
    GOOGLE_API_KEY=your_gemini_api_key
    BIG_TICKET_THRESHOLD=100.0
    ```
5.  **Run the bot**:
    ```bash
    python src/main.py
    ```

## Testing

Run the test suite using `pytest`:
```bash
pytest tests/
```

## Deployment on Google Cloud Platform (GCP) Free Tier

Target: **Compute Engine e2-micro** instance.

### 1. Create VM Instance
*   Go to GCP Console -> Compute Engine -> VM Instances.
*   Click **Create Instance**.
*   **Name**: `finance-bot`
*   **Region**: `us-central1` (or other free tier regions like `us-west1`, `us-east1`).
*   **Machine Type**: `e2-micro` (2 vCPU, 1 GB memory).
*   **Boot Disk**: Standard Persistent Disk (30GB is free). OS: Debian or Ubuntu.
*   **Firewall**: Allow HTTP/HTTPS (optional, bot uses polling so no inbound ports needed).
*   Click **Create**.

### 2. Setup VM
SSH into the VM:
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip (if not latest)
sudo apt install python3-pip python3-venv git -y

# Install uv (optional, makes things faster)
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env
```

### 3. Deploy Code
```bash
# Clone repo
git clone https://github.com/lpohsien/finance-tracker.git finance-tracker
cd finance-tracker

uv sync
```

### 4. Configure Environment
Create the `.env` file:
```bash
nano .env
# Paste your environment variables
```

### 5. Setup Systemd Service
Edit the `bot.service` file to match your paths (replace `erwinli` with your username):
```bash
nano bot.service
# Update User=your_username
# Update WorkingDirectory=/home/your_username/finance-tracker
# Update ExecStart=/home/your_username/finance-tracker/venv/bin/python /home/your_username/finance-tracker/src/main.py
# Update EnvironmentFile=/home/your_username/finance-tracker/.env
```

Copy to systemd directory and enable:
```bash
sudo cp bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable bot.service
sudo systemctl start bot.service
```

### 6. Verify
Check status:
```bash
sudo systemctl status bot.service
```
View logs:
```bash
journalctl -u bot.service -f
```

## Usage

Send a message to the bot in the format:
`{Bank_Message},{ISO_Timestamp},{Remarks}`

Commands:
*   `/start`: Initialize bot.
*   `/stats`: View all-time statistics.
*   `/month`: View current month statistics.
