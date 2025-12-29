# Systemd Service Files

This directory contains systemd service unit files for running kryten-playlist as a system service.

## Installation

1. Copy the service file to systemd directory:
```bash
sudo cp systemd/kryten-playlist.service /etc/systemd/system/
```

2. Reload systemd daemon:
```bash
sudo systemctl daemon-reload
```

3. Enable the service to start on boot:
```bash
sudo systemctl enable kryten-playlist
```

4. Start the service:
```bash
sudo systemctl start kryten-playlist
```

## Service Management

Check service status:
```bash
sudo systemctl status kryten-playlist
```

View logs:
```bash
sudo journalctl -u kryten-playlist -f
```

Stop the service:
```bash
sudo systemctl stop kryten-playlist
```

Restart the service:
```bash
sudo systemctl restart kryten-playlist
```

## Configuration

The service expects:
- Installation directory: `/opt/kryten-playlist`
- Configuration file: `/etc/kryten/playlist/config.json`
- User/Group: `kryten`
- Log directory: `/var/log/kryten-playlist`

Make sure to create these directories and the kryten user before starting the service.
