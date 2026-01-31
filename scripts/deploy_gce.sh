#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Finance Tracker Deployment Setup...${NC}"

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

# 3. HTTPS Init
echo -e "${GREEN}Step 3: Initializing Certificate (Port 80 Mode)...${NC}"

# Stop any running containers
sudo docker-compose -f docker-compose.prod.yml down

# Start Nginx in Init Mode
sudo docker-compose -f docker-compose.prod.yml -f docker-compose.init.yml up -d nginx

echo "Waiting for Nginx to start..."
sleep 5

# Run Certbot
echo -e "${GREEN}Requesting Certificate from Let's Encrypt...${NC}"
sudo docker-compose -f docker-compose.prod.yml run --rm --entrypoint "certbot" certbot certonly \
    --webroot --webroot-path /var/www/certbot \
    -d "$DOMAIN_NAME" \
    --email "$EMAIL" \
    --agree-tos --no-eff-email

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Certificate obtained successfully!${NC}"
else
    echo -e "${RED}Certbot failed. Please check the logs and your domain settings.${NC}"
    exit 1
fi

# 4. Start Production
echo -e "${GREEN}Step 4: Starting Production Stack...${NC}"
sudo docker-compose -f docker-compose.prod.yml down
sudo docker-compose -f docker-compose.prod.yml up -d

echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "Your app should be live at: https://$DOMAIN_NAME"
