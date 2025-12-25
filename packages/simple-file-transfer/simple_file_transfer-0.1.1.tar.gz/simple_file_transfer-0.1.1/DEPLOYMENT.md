# Deployment Guide

## Digital Ocean Deployment

### Prerequisites

1. Install `doctl` (Digital Ocean CLI):
```bash
snap install doctl
doctl auth init
```

2. Get your SSH key ID:
```bash
doctl compute ssh-key list
```

### Quick Deploy

Replace `<your-ssh-key-id>` with your SSH key ID from above:

```bash
doctl compute droplet create sfts-droplet \
  --region fra1 \
  --size s-1vcpu-1gb \
  --image ubuntu-22-04-x64 \
  --ssh-keys <your-ssh-key-id> \
  --user-data '#cloud-config
runcmd:
  - apt-get update
  - apt-get install -y python3-pip
  - pip3 install simple-file-transfer
  - sft serve --port 12345 &
' \
  --wait
```

### Get Droplet IP

```bash
doctl compute droplet list
```

### Configure Firewall

```bash
doctl compute firewall create \
  --name sft-firewall \
  --inbound-rules "protocol:tcp,ports:12345,sources:addresses:0.0.0.0/0" \
  --outbound-rules "protocol:tcp,ports:all,destinations:addresses:0.0.0.0/0"
```

### Use the Service

```bash
export SFT_SERVICE=<droplet-ip>:12345
sft upload ./myfile.txt 1h
```

## Docker Deployment

### Build and Run

```bash
docker build -t sft-server .
docker run -d -p 12345:12345 -v /data/sft:/data --name sft-server sft-server
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'
services:
  sft:
    build: .
    ports:
      - "12345:12345"
    volumes:
      - sft-data:/data
    restart: unless-stopped

volumes:
  sft-data:
```

Run:
```bash
docker-compose up -d
```

## Manual Installation

### On Server

```bash
pip install simple-file-transfer
sft serve --port 12345
```

### With systemd

Create `/etc/systemd/system/sft.service`:

```ini
[Unit]
Description=Simple File Transfer Service
After=network.target

[Service]
Type=simple
User=sft
WorkingDirectory=/opt/sft
Environment="SFT_STORAGE_DIR=/var/lib/sft"
ExecStart=/usr/local/bin/sft serve --port 12345
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable sft
sudo systemctl start sft
```

## Security Considerations

1. **Use HTTPS**: Put the service behind a reverse proxy (nginx/caddy) with SSL
2. **Firewall**: Restrict access to specific IPs if possible
3. **Storage Limits**: Monitor disk usage and set up cleanup policies
4. **Rate Limiting**: Consider adding rate limiting for production use

## Monitoring

Check server health:
```bash
curl http://your-server:12345/health
```

View logs (Docker):
```bash
docker logs sft-server
```

View logs (systemd):
```bash
sudo journalctl -u sft -f
```
