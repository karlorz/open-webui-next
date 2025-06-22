# Open WebUI Demo Mode

This guide explains how to run Open WebUI in demo/guest mode, where users can create chats and interact with the AI without requiring authentication or user registration.

## What is Demo Mode?

Demo mode allows Open WebUI to run without authentication, enabling:

- **Anonymous access** - No login required
- **Guest chat creation** - Users can start chatting immediately
- **Fresh environment** - Database resets on each restart
- **No user management** - Simplified operation for demonstrations

## Quick Start

### Method 1: Using the Demo Launcher Script

The easiest way to start demo mode:

```bash
./start-demo.sh
```

This script will:

1. Clean up any existing demo containers
2. Build and start the demo environment
3. Provide access instructions

### Method 2: Using Docker Compose Directly

```bash
# Start the demo environment
docker-compose -f docker-compose.demo.yaml up --build -d

# Stop the demo environment (and reset data)
docker-compose -f docker-compose.demo.yaml down -v
```

### Method 3: Manual Backend Setup

If you prefer to run the backend manually:

```bash
cd backend
./start-demo.sh
```

## Access

Once started, Open WebUI will be available at:

- **URL**: http://localhost:3000
- **No login required** - Users will be automatically authenticated
- **Ready to chat** - Users can immediately create new chats

## Configuration

### Environment Variables

The demo mode uses these key environment variables:

```bash
WEBUI_AUTH=False              # Disables authentication
WEBUI_NAME="Open WebUI Demo"  # Sets the application name
DEFAULT_USER_ROLE=admin       # Sets default user permissions
DEMO_MODE=true               # Enables demo-specific features
```

### Customization

You can customize the demo by modifying `docker-compose.demo.yaml`:

```yaml
environment:
  - 'WEBUI_NAME=My Custom Demo'
  - 'DEFAULT_MODELS=["llama2", "codellama"]' # Set default models
  - 'WEBUI_AUTH=False' # Keep auth disabled
```

## Important Notes

### Data Persistence

- **Data is reset** on each restart in demo mode
- All chats, users, and settings are temporary
- Use regular mode for persistent data

### Security Considerations

- **Demo mode is not suitable for production**
- No authentication means anyone can access the instance
- Consider network restrictions for public demos

### Model Requirements

- Ollama service must be running
- Models need to be pulled before use:
  ```bash
  docker exec ollama-demo ollama pull llama2
  docker exec ollama-demo ollama pull codellama
  ```

## Troubleshooting

### Common Issues

1. **Port already in use**:

   ```bash
   # Change port in docker-compose.demo.yaml
   ports:
     - "3001:8080"  # Use port 3001 instead
   ```

2. **Docker not running**:

   ```bash
   # Start Docker service
   sudo systemctl start docker  # Linux
   # Or start Docker Desktop on macOS/Windows
   ```

3. **Permission issues**:
   ```bash
   # Make scripts executable
   chmod +x start-demo.sh
   chmod +x backend/start-demo.sh
   ```

### Logs

View demo logs:

```bash
# View all logs
docker-compose -f docker-compose.demo.yaml logs -f

# View only Open WebUI logs
docker-compose -f docker-compose.demo.yaml logs -f open-webui-demo
```

## Stopping Demo Mode

To stop and clean up the demo environment:

```bash
# Using the compose file
docker-compose -f docker-compose.demo.yaml down -v

# Or if using the launcher script, it shows the stop command
```

The `-v` flag ensures all demo data is removed.

## Converting to Regular Mode

To switch from demo mode to regular mode with authentication:

1. Stop the demo environment
2. Use the regular docker-compose.yaml file
3. Set `WEBUI_AUTH=True` or remove the environment variable
4. Start the regular environment

```bash
# Stop demo
docker-compose -f docker-compose.demo.yaml down -v

# Start regular mode
docker-compose up -d
```

## Files Created for Demo Mode

The demo mode implementation includes:

- `start-demo.sh` - Main demo launcher script
- `docker-compose.demo.yaml` - Demo-specific Docker Compose configuration
- `Dockerfile.demo` - Demo-optimized Docker image
- `backend/start-demo.sh` - Backend demo startup script
- `DEMO.md` - This documentation file

## Support

For issues with demo mode:

1. Check the troubleshooting section above
2. Review logs using the commands provided
3. Ensure Docker and Docker Compose are properly installed
4. Verify port availability

Demo mode provides a quick way to showcase Open WebUI's capabilities without the complexity of user management.
