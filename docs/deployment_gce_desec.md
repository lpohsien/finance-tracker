# Deployment Guide: GCE + deSEC + HTTPS

This guide covers deploying the Finance Tracker to Google Compute Engine (GCE) using deSEC for DNS and Let's Encrypt for automatic HTTPS.

## Prerequisites

1.  **Google Cloud Platform Account**: With billing enabled.
2.  **deSEC.io Account**: For free, secure DNS.

---

## Step 1: Create GCE Virtual Machine

1.  Go to **Google Cloud Console** > **Compute Engine** > **VM instances**.
2.  Click **Create Instance**.
    *   **Name**: `finance-tracker`
    *   **Region**: Choose one close to you (e.g., `us-central1` or `asia-southeast1`).
    *   **Machine type**: `e2-micro` (Free tier eligible) or `e2-small`.
    *   **Boot disk**: Click "Change" -> Select **Ubuntu** -> **Ubuntu 22.04 LTS**.
    *   **Firewall**: **Check** both "Allow HTTP traffic" and "Allow HTTPS traffic".
3.  Click **Create**.

### Set Static IP
1.  Go to **VPC network** > **IP addresses**.
2.  Find the IP address of your new instance.
3.  Click "Reserve" (or promote to static) to ensure it doesn't change on reboot.

---

## Step 2: Setup DNS (deSEC)

1.  Log in to [deSEC.io](https://desec.io/).
2.  Create a new domain (e.g., `my-finance-app.desec.io`) or use a custom domain.
3.  Update the domain by calling `curl --user <(sub)domain>:<deSEC_token> https://update.dedyn.io/`, where `<deSEC_token>` is your deSEC API token obtained in step 2.


---

## Step 3: Server Setup

SSH into your GCE VM (click "SSH" in the Google Cloud Console).

### 1. Install Docker & Docker Compose
```bash
# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

# Install Docker:
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

### 2. Prepare Project
Clone your repository (you may need to set up SSH keys or use HTTPS with a token).
```bash
git clone https://github.com/YOUR_USERNAME/finance-tracker.git
cd finance-tracker
```

### 3. Configure Environment
Create the `.env` file with your production secrets.
```bash
nano .env
```
Paste your configuration (ensure `DOMAIN_NAME` is set):
```env
TELEGRAM_BOT_TOKEN=
ALLOWED_USER_IDS=
START_KEY=
SECRET_KEY=
ENCRYPTION_KEY=
DESEC_TOKEN=
DOMAIN_NAME=
```

---

## Step 4: HTTPS Setup (First Run)

Because Nginx needs the certificates to start, but Certbot needs Nginx to verify the domain, we need a 2-step initialization.

### 1. Request the Initial Certificate
We'll use a temporary certbot command to get the first certificate.

```bash
# 1. Start Nginx temporarily to handle the ACME challenge
# We use the prod config which handles the challenge in port 80
docker-compose -f docker-compose.prod.yml up -d nginx

# 2. Run Certbot to get the certificate
# Replace email and domain with yours
sudo docker-compose -f docker-compose.prod.yml run --rm certbot certonly --webroot --webroot-path /var/www/certbot -d your-domain.desec.io --email your-email@example.com --agree-tos --no-eff-email
```

*If the above succeeds, you will see a "Congratulations" message.*

### 2. Start the Full Application
Now that certificates exist, restart everything.

```bash
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d
```

Your app should now be live at `https://your-domain.desec.io`!

---

## Automatic Renewal
The `certbot` service in `docker-compose.prod.yml` runs checks every 12 hours and will automatically renew certificates before they expire. Nginx reloads every 6 hours (configured in command) to pick up new certs.
