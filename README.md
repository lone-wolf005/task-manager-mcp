# MCP Task Manager

A secure Model Context Protocol (MCP) server for managing tasks and notes with OAuth 2.0 authentication via Scalekit.

## Features

- 🔐 **OAuth 2.0 Authentication** - Secure authentication using Scalekit
- 📝 **Notes Management** - Create and list personal notes
- ✅ **Task Management** - Create and track tasks with completion status
- 👥 **Role-Based Access Control** - Fine-grained permissions system
- 📊 **Analytics** - View usage statistics (admin only)
- 🔌 **MCP Protocol** - Compatible with MCP clients like Claude Desktop

## Architecture

The server implements a role-based permission system with the following components:

- **Users** - Authenticated via Scalekit OAuth
- **Roles** - Groups of permissions (e.g., admin, user)
- **Permissions** - Granular access controls (e.g., `notes_create`, `tasks_read`)
- **Resources** - Notes and tasks owned by users

## Prerequisites

- Python 3.13+
- PostgreSQL database (Neon DB recommended)
- Scalekit account with OAuth configured

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd mcp-task-manager
```

2. Install dependencies using uv:

```bash
uv sync
```

3. Create a `.env` file with your configuration:

```env
SCALEKIT_ENVIRONMENT_URL=https://your-environment.scalekit.dev
SCALEKIT_CLIENT_ID=your_client_id
SCALEKIT_CLIENT_SECRET=your_client_secret
SCALEKIT_RESOURCE_ID=your_resource_id
MCP_RESOURCE_URL=http://localhost:9000/mcp
DATABASE_URL=postgresql://user:password@host/database
```

4. Initialize the database:

```bash
# The database tables will be created automatically on first run
# Make sure your PostgreSQL database exists
```

## Running the Server

Start the server:

```bash
uv run python main.py
```

The server will start on `http://localhost:9000`

## MCP Client Configuration

### Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "task-manager": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "http://localhost:9000/mcp"]
    }
  }
}
```

## Available Tools

### Notes

- **`create_note`** - Create a new note
  - Parameters: `content` (string)
  - Permission: `notes_create`

- **`list_notes`** - List all your notes
  - Permission: `notes_read`

### Tasks

- **`create_task`** - Create a new task
  - Parameters: `title` (string)
  - Permission: `tasks_create`

- **`list_tasks`** - List all your tasks
  - Permission: `tasks_read`

### Analytics

- **`analytics`** - View system statistics
  - Permission: `analytics_read`
  - Returns: Total users and tasks count

## Permissions System

The server uses a role-based access control system:

1. **Users** are assigned **Roles**
2. **Roles** have **Permissions**
3. **Tools** require specific **Permissions**

### Default Permissions

- `notes_create` - Create notes
- `notes_read` - Read notes
- `tasks_create` - Create tasks
- `tasks_read` - Read tasks
- `analytics_read` - View analytics

## API Endpoints

### OAuth Metadata

- `GET /.well-known/oauth-protected-resource/mcp` - OAuth resource metadata

### MCP Protocol

- `POST /mcp` - MCP protocol endpoint for tool calls and resource access

## Database Schema

The application uses the following database tables:

- `users` - User accounts linked to Scalekit
- `roles` - Permission groups
- `permissions` - Individual access rights
- `user_roles` - User-role assignments
- `role_permissions` - Role-permission assignments
- `notes` - User notes
- `tasks` - User tasks

## Development

### Project Structure

```
mcp-task-manager/
├── main.py              # FastAPI application and MCP server
├── config.py            # Configuration management
├── database.py          # Database connection setup
├── models.py            # SQLAlchemy models
├── users.py             # User management
├── permissions.py       # Permission checking
├── tools.py             # MCP tool implementations
├── scalekit_auth.py     # Scalekit OAuth integration
├── pyproject.toml       # Project dependencies
└── .env                 # Environment variables
```

### Adding New Tools

1. Define the tool function in [`tools.py`](tools.py)
2. Add required permissions to the database
3. Register the tool with the MCP server

Example:

```python
@mcp.tool()
def my_new_tool(param: str):
    token = get_access_token()
    user_id = get_or_create_user(token)

    if not has_permission(user_id, "my_permission"):
        return "Access denied"

    # Tool implementation
    return "Success"
```

## Security Considerations

- All sensitive configuration is stored in environment variables
- OAuth tokens are validated on every request
- Database sessions are properly managed and closed
- Role-based access control prevents unauthorized access
- SQL injection protection via SQLAlchemy ORM

## Troubleshooting

### Common Issues

1. **SQLAlchemy Session Errors**
   - Ensure database sessions are properly closed
   - Check that user objects aren't accessed after session closure

2. **Permission Denied**
   - Verify user has required roles and permissions
   - Check that permissions are properly assigned to roles

3. **OAuth Errors**
   - Verify Scalekit configuration in `.env`
   - Check that the resource ID matches your Scalekit setup

4. **Connection Issues**
   - Ensure the server is running on the correct port
   - Verify MCP client configuration matches server URL

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here]
