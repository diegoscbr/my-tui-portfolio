#!/bin/bash
# Run on the VPS as root: bash provision.sh
set -e

# Install Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs python3 python3-pip python3-venv git

# Clone repo
git clone https://github.com/YOUR_USERNAME/my-tui-portfolio.git /app
cd /app

# Install Python deps for pre-rendering
python3 -m venv /app/.venv
/app/.venv/bin/pip install ascii_magic pillow

# Pre-render frames (one-time)
/app/.venv/bin/python prerender.py

# Install Node deps
npm install --production

# Generate SSH host key
mkdir -p .ssh
ssh-keygen -t ed25519 -f .ssh/host_key -N ""

# Install as systemd service
cat > /etc/systemd/system/portfolio.service << EOF
[Unit]
Description=diego.boats terminal portfolio
After=network.target

[Service]
WorkingDirectory=/app
ExecStart=/usr/bin/node src/server.js
Restart=always
User=root

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable portfolio
systemctl start portfolio

echo "Done. Run: systemctl status portfolio"
