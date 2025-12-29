# Installation Guide

## Prerequisites

- Python 3.10 or higher
- Poetry (Python package manager)
- NATS server (running and accessible)
- Git

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/grobertson/kryten-playlist.git
cd kryten-playlist
```

### 2. Install Dependencies

```bash
poetry install
```

### 3. Configure the Service

Copy the example configuration:

```bash
cp config.example.json config.json
```

Edit `config.json` with your settings:

```json
{
  "nats_url": "nats://localhost:4222",
  "nats_subject_prefix": "cytube",
  "service_name": "kryten-playlist"
}
```

### 4. Run the Service

**Development mode:**

```bash
poetry run kryten-playlist --config config.json --log-level DEBUG
```

**Using startup script (PowerShell):**

```powershell
.\start-playlist.ps1
```

**Using startup script (Bash):**

```bash
./start-playlist.sh
```

## Production Installation

### System User Setup

Create a dedicated system user:

```bash
sudo useradd -r -s /bin/false -d /opt/kryten-playlist kryten
```

### Installation Directory

```bash
sudo mkdir -p /opt/kryten-playlist
sudo chown kryten:kryten /opt/kryten-playlist
```

### Configuration Directory

```bash
sudo mkdir -p /etc/kryten/playlist
sudo chown kryten:kryten /etc/kryten/playlist
sudo cp config.example.json /etc/kryten/playlist/config.json
sudo chown kryten:kryten /etc/kryten/playlist/config.json
sudo chmod 600 /etc/kryten/playlist/config.json
```

Edit the configuration:

```bash
sudo nano /etc/kryten/playlist/config.json
```

### Log Directory

```bash
sudo mkdir -p /var/log/kryten-playlist
sudo chown kryten:kryten /var/log/kryten-playlist
```

### Install Application

```bash
cd /opt/kryten-playlist
sudo -u kryten git clone https://github.com/grobertson/kryten-playlist.git .
sudo -u kryten poetry install --no-dev
```

### Systemd Service

Install the systemd service:

```bash
sudo cp systemd/kryten-playlist.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable kryten-playlist
sudo systemctl start kryten-playlist
```

Check service status:

```bash
sudo systemctl status kryten-playlist
sudo journalctl -u kryten-playlist -f
```

## Updating

### Development

```bash
git pull
poetry install
```

### Production

```bash
cd /opt/kryten-playlist
sudo systemctl stop kryten-playlist
sudo -u kryten git pull
sudo -u kryten poetry install --no-dev
sudo systemctl start kryten-playlist
```

## Troubleshooting

### Check NATS Connection

Ensure NATS server is running:

```bash
# Check if NATS is listening
netstat -tuln | grep 4222
```

### View Logs

```bash
# Systemd service logs
sudo journalctl -u kryten-playlist -f

# Check for errors
sudo journalctl -u kryten-playlist --since "1 hour ago" | grep -i error
```

### Test Configuration

```bash
# Validate JSON syntax
python -m json.tool config.json

# Test connection manually
poetry run kryten-playlist --config config.json --log-level DEBUG
```

### Permissions Issues

Ensure correct ownership:

```bash
sudo chown -R kryten:kryten /opt/kryten-playlist
sudo chown -R kryten:kryten /etc/kryten/playlist
sudo chown -R kryten:kryten /var/log/kryten-playlist
```

## Uninstalling

### Stop and Disable Service

```bash
sudo systemctl stop kryten-playlist
sudo systemctl disable kryten-playlist
sudo rm /etc/systemd/system/kryten-playlist.service
sudo systemctl daemon-reload
```

### Remove Files

```bash
sudo rm -rf /opt/kryten-playlist
sudo rm -rf /etc/kryten/playlist
sudo rm -rf /var/log/kryten-playlist
```

### Remove User

```bash
sudo userdel kryten
```
