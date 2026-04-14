#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
#  LMS – One-Click EC2 Deployment Script
#  Run this ON the EC2 instance after cloning the project.
#  Usage:  chmod +x deploy.sh && ./deploy.sh
# ═══════════════════════════════════════════════════════════════════════════════

set -e  # Exit on any error

# ── Color helpers ─────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

info()    { echo -e "${CYAN}[INFO]${NC}  $1"; }
success() { echo -e "${GREEN}[OK]${NC}    $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# ── Pre-checks ────────────────────────────────────────────────────────────────
info "Starting LMS deployment..."

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

if [ ! -f "manage.py" ]; then
    error "manage.py not found. Run this script from the project root."
fi

# ── Step 1: System dependencies ───────────────────────────────────────────────
info "Installing system dependencies..."
sudo apt update -qq
sudo apt install -y python3 python3-pip python3-venv nginx > /dev/null 2>&1
success "System dependencies installed."

# ── Step 2: Python virtual environment ────────────────────────────────────────
info "Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
success "Python environment ready."

# ── Step 3: Environment file ──────────────────────────────────────────────────
if [ ! -f ".env" ]; then
    warn ".env file not found. Creating from template..."
    cp .env.example .env

    # Generate a new Django secret key
    NEW_SECRET=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
    sed -i "s|generate-a-strong-random-key-here|${NEW_SECRET}|g" .env

    # Detect public IP and set ALLOWED_HOSTS
    PUBLIC_IP=$(curl -s http://checkip.amazonaws.com 2>/dev/null || echo "")
    if [ -n "$PUBLIC_IP" ]; then
        sed -i "s|your-ec2-public-ip,your-domain.com|${PUBLIC_IP},localhost|g" .env
        success "Auto-detected public IP: ${PUBLIC_IP}"
    else
        warn "Could not detect public IP. Edit .env manually."
    fi

    warn "IMPORTANT: Edit .env to set your email credentials:"
    warn "  nano ${PROJECT_DIR}/.env"
    echo ""
else
    success ".env file already exists."
fi

# ── Step 4: Database & static files ──────────────────────────────────────────
info "Running database migrations..."
python manage.py migrate --noinput
success "Database migrated."

info "Collecting static files..."
python manage.py collectstatic --noinput > /dev/null 2>&1
success "Static files collected to staticfiles/."

# ── Step 5: Create media directory ────────────────────────────────────────────
mkdir -p media/courses/thumbnails media/courses/content media/assignments/submissions
success "Media directories created."

# ── Step 6: Gunicorn systemd service ──────────────────────────────────────────
info "Configuring Gunicorn service..."

SERVICE_FILE="/etc/systemd/system/lms.service"
sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=LMS Django Gunicorn Daemon
After=network.target

[Service]
User=$(whoami)
Group=www-data
WorkingDirectory=${PROJECT_DIR}
EnvironmentFile=${PROJECT_DIR}/.env
ExecStart=${PROJECT_DIR}/venv/bin/gunicorn \\
    --access-logfile - \\
    --error-logfile ${PROJECT_DIR}/gunicorn-error.log \\
    --workers 3 \\
    --bind unix:${PROJECT_DIR}/lms.sock \\
    core.wsgi:application
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl start lms
sudo systemctl enable lms > /dev/null 2>&1
success "Gunicorn service started and enabled."

# ── Step 7: Nginx configuration ──────────────────────────────────────────────
info "Configuring Nginx..."

# Get server_name
PUBLIC_IP="13.51.173.49"

sudo tee /etc/nginx/sites-available/lms > /dev/null <<EOF
server {
    listen 80;
    server_name ${PUBLIC_IP};

    client_max_body_size 50M;

    location /static/ {
        alias ${PROJECT_DIR}/staticfiles/;
    }

    location /media/ {
        alias ${PROJECT_DIR}/media/;
    }

    location / {
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_pass http://unix:${PROJECT_DIR}/lms.sock;
    }
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/lms /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test and restart
sudo nginx -t
sudo systemctl restart nginx
success "Nginx configured and restarted."

# ── Step 8: Firewall ─────────────────────────────────────────────────────────
info "Configuring firewall..."
sudo ufw allow 'Nginx Full' > /dev/null 2>&1
sudo ufw allow OpenSSH > /dev/null 2>&1
echo "y" | sudo ufw enable > /dev/null 2>&1
success "Firewall configured (HTTP, HTTPS, SSH allowed)."

# ── Step 9: Fix permissions ──────────────────────────────────────────────────
sudo chmod 755 /home/$(whoami)
sudo chown -R $(whoami):www-data "$PROJECT_DIR"
success "Permissions set."

# ── Done! ─────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅  LMS DEPLOYMENT COMPLETE!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  🌐  Your site is live at:  ${CYAN}http://${PUBLIC_IP}${NC}"
echo ""
echo -e "  📝  Next steps:"
echo -e "    1. Edit .env with your email credentials:"
echo -e "       ${YELLOW}nano ${PROJECT_DIR}/.env${NC}"
echo -e "    2. Create an admin superuser:"
echo -e "       ${YELLOW}source venv/bin/activate && python manage.py createsuperuser${NC}"
echo -e "    3. (Optional) Load sample data:"
echo -e "       ${YELLOW}python manage.py seed_data${NC}"
echo -e "    4. Restart after .env changes:"
echo -e "       ${YELLOW}sudo systemctl restart lms${NC}"
echo ""
echo -e "  📋  Service commands:"
echo -e "    Status:   ${YELLOW}sudo systemctl status lms${NC}"
echo -e "    Logs:     ${YELLOW}sudo journalctl -u lms -f${NC}"
echo -e "    Restart:  ${YELLOW}sudo systemctl restart lms && sudo systemctl restart nginx${NC}"
echo ""
