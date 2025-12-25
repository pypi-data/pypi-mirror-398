# Tunnel V4

A modern tunnel system built on Cloudflare Workers and Durable Objects.

## Features

- 🚀 **Remote Terminal** - SSH-like terminal access to your servers
- 📡 **SOCKS5 Proxy** - Secure proxy through your nodes
- ⚡ **Command Execution** - Run commands remotely
- 🔒 **Secure** - End-to-end encrypted connections
- 🌍 **Global** - Powered by Cloudflare's edge network

## Installation

```bash
pip install mp-tunnel
```

## Quick Start

### Start Agent on Your Server

```bash
# Basic usage
tunnel agent --id my-server @all

# With custom tags
tunnel agent --id my-server --tags env=prod,region=us @all

# Specific services only
tunnel agent --id my-server @term @socks5
```

### Use CLI to Connect

```bash
# List nodes
tunnel list

# Remote terminal
tunnel term --node my-server

# Execute command
tunnel exec --node my-server "uptime"

# SOCKS5 proxy
tunnel socks5 --node my-server --port 1080
```

## Configuration

### Environment Variables

- `TUNNEL_WORKER_URL` - Override default Worker URL
- `TUNNEL_ENV` - Environment (dev/prod)
- `TUNNEL_DEBUG` - Enable debug logging

### Custom Worker URL

```bash
export TUNNEL_WORKER_URL="wss://your-worker.workers.dev"
tunnel agent --id my-server @all
```

## Services

### Built-in Services

- `@all` - All services (exec, term, socks5)
- `@exec` - Remote command execution
- `@term` - Remote terminal
- `@socks5` - SOCKS5 proxy

### Port Forwarding

```bash
# Forward local service
tunnel agent --id my-server myapi:8080
```

## Development

```bash
# Clone repository
git clone https://github.com/yourusername/tunnel-v4.git
cd tunnel-v4

# Install in development mode
export TUNNEL_DEV=1
pip install -e .

# Run agent (development uses tunnel4 command)
tunnel4 agent --id test @all
```

## License

MIT License

## Links

- Documentation: https://github.com/yourusername/tunnel-v4/docs
- Issues: https://github.com/yourusername/tunnel-v4/issues
