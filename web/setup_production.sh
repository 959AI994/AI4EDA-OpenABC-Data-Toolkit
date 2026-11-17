#!/bin/bash
# AI4EDA Web Interface - Production Deployment Setup Script
# This script helps you set up the production environment

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Configure the portable examples for this machine before installing anything.
for CONFIG in ai4eda-web.service nginx-ai4eda.conf; do
    if [ ! -f "$CONFIG" ]; then
        echo "Copy $CONFIG.example to $CONFIG and edit its paths/user/host first."
        exit 1
    fi
done

echo "======================================================================"
echo "AI4EDA Web Interface - Production Deployment Setup"
echo "======================================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Error: This script must be run with sudo${NC}"
    echo "Usage: sudo ./setup_production.sh"
    exit 1
fi

echo "Step 1: Installing Nginx..."
if command -v nginx &> /dev/null; then
    echo -e "${GREEN}✓ Nginx is already installed${NC}"
else
    apt update
    apt install -y nginx
    echo -e "${GREEN}✓ Nginx installed successfully${NC}"
fi
echo ""

echo "Step 2: Configuring Nginx..."
# Copy nginx configuration
cp nginx-ai4eda.conf /etc/nginx/sites-available/ai4eda
# Enable the site
ln -sf /etc/nginx/sites-available/ai4eda /etc/nginx/sites-enabled/ai4eda
# Remove default site if exists
rm -f /etc/nginx/sites-enabled/default
# Test nginx configuration
nginx -t
echo -e "${GREEN}✓ Nginx configured successfully${NC}"
echo ""

echo "Step 3: Setting up Systemd service..."
# Copy systemd service file
cp ai4eda-web.service /etc/systemd/system/ai4eda-web.service
# Reload systemd
systemctl daemon-reload
# Enable the service
systemctl enable ai4eda-web
echo -e "${GREEN}✓ Systemd service configured${NC}"
echo ""

echo "Step 4: Configuring firewall..."
if command -v ufw &> /dev/null; then
    ufw allow 80/tcp
    ufw allow 443/tcp
    echo -e "${GREEN}✓ Firewall configured (UFW)${NC}"
elif command -v firewall-cmd &> /dev/null; then
    firewall-cmd --permanent --add-service=http
    firewall-cmd --permanent --add-service=https
    firewall-cmd --reload
    echo -e "${GREEN}✓ Firewall configured (firewalld)${NC}"
else
    echo -e "${YELLOW}⚠ No firewall detected. Please manually allow ports 80 and 443${NC}"
fi
echo ""

echo "Step 5: Starting services..."
# Stop any running gunicorn process
if [ -f "gunicorn.pid" ]; then
    PID=$(cat gunicorn.pid)
    if kill -0 $PID 2>/dev/null; then
        kill $PID
        echo "Stopped running gunicorn process"
    fi
    rm -f gunicorn.pid
fi

# Start the systemd service
systemctl start ai4eda-web
systemctl reload nginx
echo -e "${GREEN}✓ Services started${NC}"
echo ""

echo "======================================================================"
echo "                   Production Deployment Complete!"
echo "======================================================================"
echo ""
echo "Your AI4EDA web interface is now running in production mode."
echo ""
echo "Access URLs:"
echo "  - Local:   http://localhost"
echo "  - Network: http://YOUR_SERVER_HOST"
echo ""
echo "Management Commands:"
echo "  - Check status:  sudo systemctl status ai4eda-web"
echo "  - Stop service:  sudo systemctl stop ai4eda-web"
echo "  - Start service: sudo systemctl start ai4eda-web"
echo "  - Restart:       sudo systemctl restart ai4eda-web"
echo "  - View logs:     sudo journalctl -u ai4eda-web -f"
echo ""
echo "Nginx Commands:"
echo "  - Check status:  sudo systemctl status nginx"
echo "  - Reload config: sudo systemctl reload nginx"
echo "  - View logs:     sudo tail -f /var/log/nginx/access.log"
echo ""
echo "HTTPS Setup (Optional):"
echo "  If you have a domain name, you can enable HTTPS:"
echo "  1. Update server_name in /etc/nginx/sites-available/ai4eda"
echo "  2. Run: sudo apt install certbot python3-certbot-nginx"
echo "  3. Run: sudo certbot --nginx -d your-domain.com"
echo ""
echo "======================================================================"
