#!/bin/bash
set -e

# Ensure we are running from the project root
cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Finance Tracker Deployment Setup...${NC}"
echo -e "Project Root: $PROJECT_ROOT"

# 1. Install Docker & Docker Compose
echo -e "${GREEN}Step 1: Checking/Installing Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo "Docker not found. Installing..."
    sudo apt-get update
    # User noted preference for docker.io
    sudo apt-get install -y docker.io docker-compose
    sudo usermod -aG docker $USER
    echo -e "${GREEN}Docker installed. NOTE: You may need to log out and log back in for group changes to take effect if you run docker without sudo.${NC}"
else
    echo "Docker is already installed."
fi

# Ensure docker-compose exists
if ! command -v docker-compose &> /dev/null; then
     echo "docker-compose not found. Installing..."
     sudo apt-get install -y docker-compose
fi

# 2. Configuration Prompts
echo -e "${GREEN}Step 2: Configuration${NC}"

if [ -f .env ]; then
    echo ".env file already exists. Skipping generation."
    read -p "Do you want to regenerate the .env file? (y/n) " regenerate
    if [[ "$regenerate" == "y" ]]; then
        rm .env
    fi
fi

if [ ! -f .env ]; then
    read -p "Enter your deSEC Domain Name (e.g., tracker.example.dedyn.io): " DOMAIN_NAME
    read -p "Enter your Email for Let's Encrypt: " EMAIL
    read -p "Enter Telegram Bot Token: " TELEGRAM_BOT_TOKEN
    read -p "Enter Allowed User IDs (comma separated): " ALLOWED_USER_IDS
    read -p "Enter deSEC Token: " DESEC_TOKEN
    
    # Generate keys
    echo "Generating secrets..."
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || echo "manual_change_this_$(date +%s)")
    ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>/dev/null || echo "")

    if [ -z "$ENCRYPTION_KEY" ]; then
        echo -e "${RED}Warning: Could not generate Fernet key (cryptography not installed). Using placeholder.${NC}"
        ENCRYPTION_KEY="CHANGE_ME_TO_VALID_FERNET_KEY"
    fi

    cat << EOF > .env
DOMAIN_NAME=$DOMAIN_NAME
LETSENCRYPT_EMAIL=$EMAIL
TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN
ALLOWED_USER_IDS=$ALLOWED_USER_IDS
START_KEY=start
SECRET_KEY=$SECRET_KEY
ENCRYPTION_KEY=$ENCRYPTION_KEY
DESEC_TOKEN=$DESEC_TOKEN
EOF
    echo ".env file created."
else
    # Source the env file to get variables needed for certbot
    export $(grep -v '^#' .env | xargs)
    EMAIL=$LETSENCRYPT_EMAIL
fi

# Read variables back if they weren't just set (case where .env existed)
if [ -z "$DOMAIN_NAME" ]; then
    DOMAIN_NAME=$(grep DOMAIN_NAME .env | cut -d '=' -f2)
fi
if [ -z "$EMAIL" ]; then
    EMAIL=$(grep LETSENCRYPT_EMAIL .env | cut -d '=' -f2)
fi
if [ -z "$DESEC_TOKEN" ]; then
    DESEC_TOKEN=$(grep DESEC_TOKEN .env | cut -d '=' -f2)
fi

# 3. Setup Certbot Credentials
echo -e "${GREEN}Step 3: Configuring deSEC DNS Challenge...${NC}"
mkdir -p certbot/secrets
cat << EOF > certbot/secrets/desec.ini
dns_desec_token = $DESEC_TOKEN
EOF
chmod 600 certbot/secrets/desec.ini

# 4. Update DNS IP (DynDNS)
echo -e "${GREEN}Step 4: Updating DNS IP Address...${NC}"
# Use the Token header method to avoid exposing credentials in process list if possible, or basic auth.
# basic auth: curl --user <domain>:<token> https://update.dedyn.io/
# token auth: curl https://update.dedyn.io/?hostname=<domain> --header "Authorization: Token <token>"
# We will use Basic Auth as it is the most robust across curl versions for this API.

# Check if we have curl
if ! command -v curl &> /dev/null; then
    echo "curl not found. Installing..."
    sudo apt-get install -y curl
fi

echo "Updating IP for $DOMAIN_NAME..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --user "$DOMAIN_NAME:$DESEC_TOKEN" "https://update.dedyn.io/")

if [ "$HTTP_STATUS" -eq 200 ]; then
    echo -e "${GREEN}DNS IP updated successfully.${NC}"
else
    echo -e "${RED}Failed to update DNS IP. HTTP Status: $HTTP_STATUS${NC}"
    echo -e "${RED}Check your DOMAIN_NAME and DESEC_TOKEN.${NC}"
    # Continue anyway, as the IP might already be correct
fi

# 5. Request Certificate (DNS Mode)
echo -e "${GREEN}Step 5: Requesting Certificate via DNS Challenge (No Nginx required yet)...${NC}"

# Rebuild certbot image to include the plugin
sudo docker-compose -f docker-compose.prod.yml build certbot

# Add --dns-desec-propagation-seconds to 180 and try certonly
sudo docker-compose -f docker-compose.prod.yml run --rm --entrypoint "certbot" certbot certonly \
    --authenticator dns-desec \
    --dns-desec-credentials /etc/letsencrypt/secrets/desec.ini \
    --dns-desec-propagation-seconds 180 \
    -d "$DOMAIN_NAME" \
    --email "$EMAIL" \
    --agree-tos --no-eff-email

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Certificate obtained successfully!${NC}"
else
    echo -e "${RED}Certbot failed. Please check the logs and your token.${NC}"
    echo -e "${RED}Possible Issue: NXDOMAIN looking up TXT for _acme-challenge.${DOMAIN_NAME}${NC}"
    echo -e "${RED}Solution: Ensure your domain '${DOMAIN_NAME}' is correctly registered in deSEC and your local machine or GCE instance can resolve it.${NC}"
    echo -e "${RED}Try running: 'nslookup ${DOMAIN_NAME}' or 'host -t NS ${DOMAIN_NAME}' to verify DNS.${NC}"
    exit 1
fi

# 6. Start Production
echo -e "${GREEN}Step 6: Starting Production Stack...${NC}"
sudo docker-compose -f docker-compose.prod.yml down
sudo docker-compose -f docker-compose.prod.yml up -d

echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "Your app should be live at: https://$DOMAIN_NAME"
