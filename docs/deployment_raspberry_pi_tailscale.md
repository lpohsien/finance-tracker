# Raspberry Pi Deployment with Tailscale (No Port Forwarding)

This guide deploys Finance Tracker to Raspberry Pi using Docker and publishes it through Tailscale. The app listens on localhost only, and Tailscale proxies traffic to it.

## Why this profile

- No router port forwarding required.
- Reduced attack surface: backend binds to `127.0.0.1:8000` only.
- Supports pull-and-run from prebuilt images to save Pi storage and CPU.

## Files added for this flow

- `docker-compose.pi.yml`
- `scripts/deploy_pi_tailscale.sh`

## 1. Prepare Raspberry Pi

Use Raspberry Pi OS 64-bit if possible.

```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose rsync curl
sudo usermod -aG docker $USER
# Log out and log back in after this command for group changes to apply.
```

Why this package name differs on some Pi images:
- `docker-compose-plugin` is typically provided by Docker's upstream apt repository.
- Raspberry Pi OS default apt repositories often provide `docker.io` + `docker-compose` (legacy binary) instead.

Check what you have:

```bash
docker compose version || docker-compose --version
```

Check free disk:

```bash
df -h /
```

For low storage setups (~7 GB), prefer prebuilt image pull (Section 3) instead of building on Pi.

## 2. Configure environment on Pi

On the Pi, create deployment directory and environment file manually.

```bash
mkdir -p /opt/finance-tracker/data
cd /opt/finance-tracker
cat > .env << 'EOF'
SECRET_KEY=change_me
ENCRYPTION_KEY=change_me
CORS_ORIGINS=https://your-device.your-tailnet.ts.net
EOF
```

Do not store `.env` in Git.

## 3. Prebuild image (recommended)

### Option A0: GitHub Actions auto-publish to GHCR (recommended)

This repository includes a workflow at `.github/workflows/publish-ghcr.yml` that:
- runs on every push,
- builds multi-arch image (`linux/amd64`, `linux/arm64`),
- pushes to `ghcr.io/<owner>/finance-tracker`,
- and sets the GHCR package visibility to public.

One-time setup in GitHub repository settings (Optional, recommended if you want to ensure the image is public to void GHCR private repo limits. See implemention in `.github/workflows/publish-ghcr.yml` for details):
1. Go to **Settings > Secrets and variables > Actions**.
2. Add secret `GHCR_ADMIN_TOKEN`.
3. Use a PAT from the image owner account with package admin capability.
4. Typical scopes: `write:packages` (and `delete:packages` if your policy requires it).

After that, each push publishes fresh image tags automatically.

### Option A: GitHub Container Registry (recommended)

GHCR is typically the easiest free option for public images with good retention and no Docker Hub pull-rate constraints for many use cases.

From your dev machine (or CI):

```bash
export IMAGE=ghcr.io/<github-username-or-org>/finance-tracker:latest
docker login ghcr.io -u <github-username>
docker buildx create --use --name multiarch-builder || true
docker buildx build \
  --platform linux/arm64,linux/amd64 \
  -t "$IMAGE" \
  --push .
```

### Option B: Docker Hub

```bash
export IMAGE=docker.io/<dockerhub-user>/finance-tracker:latest
docker login
docker buildx create --use --name multiarch-builder || true
docker buildx build \
  --platform linux/arm64,linux/amd64 \
  -t "$IMAGE" \
  --push .
```

## 4. Deploy to Pi

### A. Run directly on Pi (pull-and-run)

```bash
cd ~/finance-tracker
# Ensure code exists here (git clone or one-time sync)
./scripts/deploy_pi_tailscale.sh --mode local --image ghcr.io/lpohsien/finance-tracker:latest
```

### B. Deploy from laptop to Pi (safe sync)

This sync mode explicitly does NOT copy `.env` or anything under `data/`.

```bash
./scripts/deploy_pi_tailscale.sh \
  --mode remote \
  --pi-host pi@<pi-lan-ip> \
  --pi-path /opt/finance-tracker \
  --image ghcr.io/<owner>/finance-tracker:latest
```

## 5. Publish with Tailscale

Install and connect Tailscale on Pi:

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

### Private access only (tailnet users)

```bash
sudo tailscale serve --bg 8000
```

### Public internet access (Funnel)

```bash
sudo tailscale funnel --bg 8000
```

Check status:

```bash
tailscale serve status
```

You should see a `https://<device>.<tailnet>.ts.net` URL.

Notes:
- First use may prompt you in browser to enable HTTPS/Funnel permissions.
- Funnel availability depends on your Tailscale plan and ACL/nodeAttrs policy.

## 6. Security notes

- `docker-compose.pi.yml` binds backend to localhost only.
- Keep app auth enabled (do not expose anonymous endpoints).
- Restrict who can use Funnel in Tailscale ACL policy where possible.
- Rotate `SECRET_KEY` and `ENCRYPTION_KEY` if leaked.

## 7. Operations

Update image on Pi:

```bash
cd /opt/finance-tracker
export FINANCE_TRACKER_IMAGE=ghcr.io/<owner>/finance-tracker:latest
if docker compose version >/dev/null 2>&1; then
  docker compose -f docker-compose.pi.yml pull
  docker compose -f docker-compose.pi.yml up -d
else
  docker-compose -f docker-compose.pi.yml pull
  docker-compose -f docker-compose.pi.yml up -d
fi
```

Clean old Docker cache/images when storage is tight:

```bash
docker system prune -af --volumes
```

Use with care: this removes unused images/volumes.
