# X (Twitter) MCP server

[![smithery badge](https://smithery.ai/badge/@rafaljanicki/x-twitter-mcp-server)](https://smithery.ai/server/@rafaljanicki/x-twitter-mcp-server)
[![PyPI version](https://badge.fury.io/py/x-twitter-mcp.svg)](https://badge.fury.io/py/x-twitter-mcp)

A Model Context Protocol (MCP) server for interacting with Twitter (X) via AI tools. This server allows you to fetch tweets, post tweets, search Twitter, manage followers, and more, all through natural language commands in AI Tools.

**🚀 NEW: OAuth 2.0 Authentication with Callback URLs! Secure, easy, and professional.**

<a href="https://glama.ai/mcp/servers/@rafaljanicki/x-twitter-mcp-server">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/@rafaljanicki/x-twitter-mcp-server/badge" alt="X (Twitter) server MCP server" />
</a>

## Features

- **🔐 OAuth 2.0 Authentication**: Secure Twitter authentication with callback URLs
- **🌐 Web Interface**: Beautiful Arabic interface for account management
- **📱 One-Click Setup**: Add Twitter accounts with just a username
- **🛡️ Secure Storage**: Local SQLite database for credential storage
- **📊 Account Management**: Add, update, test, and remove accounts easily
- Fetch user profiles, followers, and following lists
- Post, delete, and favorite tweets
- Search Twitter for tweets and trends
- Manage bookmarks and timelines
- Built-in rate limit handling for the Twitter API
- Uses Twitter API v2 with proper authentication

## How It Works

1. **OAuth Setup**: Configure your Twitter Developer App with callback URL
2. **User Experience**: Users enter username and get OAuth link
3. **Secure Flow**: Twitter handles authentication and redirects back
4. **Automatic Storage**: Account credentials are stored locally
5. **Daily Usage**: Just use username in Claude Desktop requests

## Prerequisites

- **Python 3.10 or higher**: Ensure Python is installed on your system.
- **Twitter Developer Account**: You need OAuth 2.0 credentials from the [Twitter Developer Portal](https://developer.twitter.com/).
- **OAuth App Setup**: Configure your Twitter app with the correct callback URL.
- Optional: **Claude Desktop**: Download and install the Claude Desktop app from the [Anthropic website](https://www.anthropic.com/).
- Optional: **Node.js** (for MCP integration): Required for running MCP servers in Claude Desktop.
- A package manager like `uv` or `pip` for Python dependencies.

## Twitter Developer App Setup

### Step 1: Create Twitter App
1. Go to [Twitter Developer Portal](https://developer.twitter.com/)
2. Create a new app or use existing one
3. Enable OAuth 2.0

### Step 2: Configure OAuth Settings
1. In your app settings, add these OAuth 2.0 scopes:
   - `tweet.read`
   - `tweet.write`
   - `users.read`
   - `follows.read`
   - `offline.access`

2. Set the callback URL to:
   ```
   http://YOUR_SERVER_IP:8000/auth/callback
   ```
   Or for production:
   ```
   https://yourdomain.com/auth/callback
   ```

### Step 3: Get Credentials
Copy these from your Twitter app:
- **Client ID** (API Key)
- **Client Secret** (API Secret)

## Installation

### Option 1: Installing via Smithery (Recommended)

To install X (Twitter) MCP server for Claude Desktop automatically via [Smithery](https://smithery.ai/server//x-twitter-mcp-server):

```bash
npx -y @smithery/cli install @rafaljanicki/x-twitter-mcp-server --client claude
```

### Option 2: Install from PyPI
The easiest way to install `x-twitter-mcp` is via PyPI:

```bash
pip install x-twitter-mcp
```

### Option 3: Install from Source
If you prefer to install from the source repository:

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/rafaljanicki/x-twitter-mcp-server.git
   cd x-twitter-mcp-server
   ```

2. **Set Up a Virtual Environment** (optional but recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies**:
   Using `uv` (recommended, as the project uses `uv.lock`):
   ```bash
   uv sync
   ```
   Alternatively, using `pip`:
   ```bash
   pip install .
   ```

## Configuration

### Environment Variables
Create a `.env` file or set environment variables:

```bash
# Twitter OAuth
export TWITTER_CLIENT_ID="your_twitter_client_id"
export TWITTER_CLIENT_SECRET="your_twitter_client_secret"

# Server Settings
export HOST="0.0.0.0"  # للوصول من الخارج
export PORT="8000"

# Optional: Custom callback URL
export TWITTER_REDIRECT_URI="https://yourdomain.com/auth/callback"
```

### For Production
```bash
# Security
export SECRET_KEY="your-super-secret-key-here"
export DATABASE_URL="sqlite:///./twitter_accounts.db"

# OAuth Security
export OAUTH_STATE_EXPIRE_SECONDS="1800"  # 30 minutes
```

## Running the Server

### Option 1: Using the CLI Script
The project defines a CLI script `x-twitter-mcp-server`.

If installed from PyPI:
```bash
x-twitter-mcp-server
```

If installed from source with `uv`:
```bash
uv run x-twitter-mcp-server
```

### Option 2: Using FastMCP Directly (Source Only)
If you installed from source and prefer to run the server using FastMCP's development mode:

```bash
fastmcp dev src/x_twitter_mcp/server.py
```

The server will start and you'll see:
```
Starting TwitterMCPServer...
✅ خادم المصادقة يعمل على http://127.0.0.1:8000
🌐 الصفحة الرئيسية: http://127.0.0.1:8000/
📖 واجهة API: http://127.0.0.1:8000/docs
```

## Using the OAuth System

### Step 1: Access the Web Interface
Open your browser and go to: **http://YOUR_SERVER_IP:8000/**

### Step 2: Add Account via OAuth
1. Enter the username you want to use
2. Click "إنشاء رابط المصادقة"
3. Copy the generated OAuth URL
4. Open the URL in a new tab
5. Sign in to Twitter and authorize the app
6. You'll be redirected back with success message

### Step 3: Use in Claude Desktop
Now you can use any tool with just your username:

```
Post a tweet saying "Hello World!" using username "myusername"
Search Twitter for recent tweets about AI using username "myusername"
Show my Twitter timeline using username "myusername"
```

## Web Interface Features

### 🌐 Main Page (`/`)
- **OAuth Authentication**: One-click account setup
- **Manual API**: Link to traditional API interface
- **Account List**: View all stored accounts
- **Arabic Interface**: Full Arabic language support

### 🔐 OAuth Endpoints
- `GET /auth/oauth-url?username={username}` - Generate OAuth URL
- `GET /auth/callback?code={code}&state={state}` - Handle Twitter callback

### 📊 Account Management
- `GET /accounts/` - List all accounts
- `POST /accounts/` - Add account manually
- `GET /accounts/{username}` - Get specific account
- `PUT /accounts/{username}` - Update account
- `DELETE /accounts/{username}` - Delete account
- `POST /accounts/{username}/test` - Test credentials

## Using with Claude Desktop

### Step 1: Install Node.js
Claude Desktop uses Node.js to run MCP servers. If you don't have Node.js installed:
- Download and install Node.js from [nodejs.org](https://nodejs.org/).
- Verify installation:
  ```bash
  node --version
  ```

### Step 2: Locate Claude Desktop Configuration
Claude Desktop uses a `claude_desktop_config.json` file to configure MCP servers.

- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

If the file doesn't exist, create it.

### Step 3: Configure the MCP Server
Edit `claude_desktop_config.json` to include the `x-twitter-mcp` server:

```json
{
  "mcpServers": {
    "x-twitter-mcp": {
      "command": "x-twitter-mcp-server",
      "args": [],
      "env": {
        "PYTHONUNBUFFERED": "1",
        "TWITTER_CLIENT_ID": "your_client_id",
        "TWITTER_CLIENT_SECRET": "your_client_secret"
      }
    }
  }
}
```

### Step 4: Restart Claude Desktop
- Quit Claude Desktop completely.
- Reopen Claude Desktop to load the new configuration.

### Step 5: Verify Connection
- Open Claude Desktop.
- Look for a hammer or connector icon in the input area (bottom right corner).
- Click the icon to see the available tools from `x-twitter-mcp`.

## Available Tools

### Account Management Tools

#### `add_twitter_account`
- **Description**: Add a new Twitter account to the database
- **Usage**: First time setup only (manual method)
- **Example**: 
  ```
  Add my Twitter account with username "john_doe", API key "xxx", API secret "xxx", access token "xxx", access token secret "xxx", and bearer token "xxx"
  ```

#### `list_twitter_accounts`
- **Description**: List all stored Twitter accounts
- **Usage**: Check what accounts you have
- **Example**: 
  ```
  List all my Twitter accounts
  ```

#### `test_twitter_account`
- **Description**: Test if stored credentials are valid
- **Usage**: Verify account works
- **Example**: 
  ```
  Test my Twitter account "john_doe"
  ```

#### `remove_twitter_account`
- **Description**: Remove a Twitter account from database
- **Usage**: Clean up old accounts
- **Example**: 
  ```
  Remove my Twitter account "john_doe"
  ```

### User Management Tools

#### `get_user_profile`
- **Description**: Get detailed profile information for a user
- **Usage**: 
  ```
  Get the Twitter profile for user ID 123456789 using username "john_doe"
  ```

#### `get_user_by_screen_name`
- **Description**: Fetches a user by screen name
- **Usage**: 
  ```
  Get the Twitter user with screen name "example_user" using username "john_doe"
  ```

#### `get_user_followers`
- **Description**: Retrieves a list of followers for a given user
- **Usage**: 
  ```
  Get the followers of user ID 123456789, limit to 50, using username "john_doe"
  ```

### Tweet Management Tools

#### `post_tweet`
- **Description**: Post a tweet with optional media, reply, and tags
- **Usage**: 
  ```
  Post a tweet saying "Hello from Claude Desktop! #MCP" using username "john_doe"
  ```

#### `delete_tweet`
- **Description**: Delete a tweet by its ID
- **Usage**: 
  ```
  Delete the tweet with ID 123456789012345678 using username "john_doe"
  ```

#### `search_twitter`
- **Description**: Search Twitter with a query
- **Usage**: 
  ```
  Search Twitter for recent tweets about AI, limit to 10, using username "john_doe"
  ```

#### `get_timeline`
- **Description**: Get tweets from your home timeline
- **Usage**: 
  ```
  Show my Twitter For You timeline, limit to 20 tweets, using username "john_doe"
  ```

## OAuth Flow Diagram

```
User → Web Interface → Generate OAuth URL → Twitter Login → Authorization → Callback → Success
  ↓
Username stored → Use in Claude Desktop → API calls with stored credentials
```

## Security Features

1. **OAuth 2.0**: Industry-standard authentication protocol
2. **PKCE Support**: Enhanced security for public clients
3. **State Validation**: Prevents CSRF attacks
4. **Local Storage**: Credentials stored locally, not in cloud
5. **Session Management**: Secure OAuth state handling
6. **Scope Limitation**: Only requested permissions granted

## Production Deployment

### Environment Variables
```bash
# Production settings
export HOST="0.0.0.0"
export PORT="8000"
export SECRET_KEY="your-production-secret-key"
export TWITTER_REDIRECT_URI="https://yourdomain.com/auth/callback"

# Database (optional: use PostgreSQL for production)
export DATABASE_URL="postgresql://user:pass@localhost/twitter_mcp"
```

### Reverse Proxy (Nginx)
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### SSL Certificate
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com
```

## Troubleshooting

### OAuth Issues
- **Invalid Client**: Check your Twitter app credentials
- **Callback Mismatch**: Ensure callback URL matches exactly
- **Scope Issues**: Verify OAuth 2.0 scopes are enabled
- **State Expired**: OAuth states expire after 1 hour

### Server Issues
- **Port Conflicts**: Ensure port 8000 is available
- **Firewall**: Allow incoming connections on port 8000
- **Environment Variables**: Check all required variables are set

### Twitter API Issues
- **Rate Limits**: Check Twitter API rate limits
- **App Status**: Ensure your Twitter app is active
- **Permissions**: Verify required scopes are granted

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on the [GitHub repository](https://github.com/rafaljanicki/x-twitter-mcp-server).

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Author

- **Rafal Janicki** - [rafal@kult.io](mailto:rafal@kult.io)


to run mcp as sse use this command
mcp-proxy --host=0.0.0.0 --port=9000 --allow-origin='*' -- python run_server.py

can accses it http://ip:port/sse