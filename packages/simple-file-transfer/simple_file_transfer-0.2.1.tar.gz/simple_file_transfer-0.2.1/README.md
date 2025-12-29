# Simple File Transfer (SFT)

A simple, temporary file transfer service for sharing files between machines.

## Installation

```bash
pip install simple-file-transfer
```

## Quick Start

### Server Setup

```bash
pip install simple-file-transfer
sft serve --port 12345
```

### Upload a File (Machine A)

```bash
sft upload ./my-file.tgz 1h
```

Output:
```
Uploaded my-file.tgz 5GB sha256:...
The file will be deleted in 1h (2025-01-01 00:01:00)
To download your file, enter: sft download 763298
```

### Download a File (Machine B)

```bash
sft download 763298
```

Output:
```
File downloaded my-file.tgz 5GB sha256:...
The file will be deleted in 55min (2025-01-01 00:01:00)
```

## Configuration

By default, SFT connects to `sft.pzjj.org:12345`. To use a different server, set the `SFT_SERVICE` environment variable:

```bash
export SFT_SERVICE=your-server.com:12345
```

Or use the `--service` flag:

```bash
sft upload --service your-server.com:12345 ./file.txt 1h
```

## Time Formats

Supported time formats for expiry:
- `1h` - 1 hour
- `30m` - 30 minutes
- `2d` - 2 days
- `1w` - 1 week

## Docker Deployment

```bash
docker build -t sft-server .
docker run -p 12345:12345 -v /data/sft:/data sft-server
```

## Features

- Simple CLI interface
- Automatic file expiry
- SHA256 checksums for integrity
- Minimal dependencies
- Easy deployment
For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

