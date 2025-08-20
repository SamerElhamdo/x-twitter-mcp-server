# X (Twitter) MCP server

[![smithery badge](https://smithery.ai/badge/@rafaljanicki/x-twitter-mcp-server)](https://smithery.ai/server/@rafaljanicki/x-twitter-mcp-server)
[![PyPI version](https://badge.fury.io/py/x-twitter-mcp.svg)](https://badge.fury.io/py/x-twitter-mcp)

A Model Context Protocol (MCP) server for interacting with Twitter (X) via AI tools. This server allows you to fetch tweets, post tweets, search Twitter, manage followers, and more, all through natural language commands in AI Tools.

**🚀 NEW: Local Database with Authentication API! Now you only need to provide your username instead of all API credentials.**

<a href="https://glama.ai/mcp/servers/@rafaljanicki/x-twitter-mcp-server">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/@rafaljanicki/x-twitter-mcp-server/badge" alt="X (Twitter) server MCP server" />
</a>

## Features

- **🔐 Local Database Authentication**: Store Twitter API credentials locally and use only username
- **🌐 Web API Interface**: Manage accounts via web interface at http://127.0.0.1:8000/docs
- **📱 Account Management**: Add, update, test, and remove Twitter accounts easily
- Fetch user profiles, followers, and following lists
- Post, delete, and favorite tweets
- Search Twitter for tweets and trends
- Manage bookmarks and timelines
- Built-in rate limit handling for the Twitter API
- Uses Twitter API v2 with proper authentication (API keys and tokens)
- Provides a complete implementation of Twitter API v2 endpoints

## How It Works

1. **First Time Setup**: Add your Twitter account credentials via the web API
2. **Daily Usage**: Just provide your username in each request
3. **Secure Storage**: Credentials are stored locally in SQLite database
4. **Easy Management**: Web interface for account management

## Prerequisites

- **Python 3.10 or higher**: Ensure Python is installed on your system.
- **Twitter Developer Account**: You need API credentials (API Key, API Secret, Access Token, Access Token Secret, and Bearer Token) from the [Twitter Developer Portal](https://developer.twitter.com/).
- Optional: **Claude Desktop**: Download and install the Claude Desktop app from the [Anthropic website](https://www.anthropic.com/).
- Optional: **Node.js** (for MCP integration): Required for running MCP servers in Claude Desktop.
- A package manager like `uv` or `pip` for Python dependencies.

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

## Running the Server

You can run the server in two ways:

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
📖 يمكنك إدارة الحسابات عبر: http://127.0.0.1:8000/docs
```

## Setting Up Your First Twitter Account

### Step 1: Access the Web Interface
Open your browser and go to: **http://127.0.0.1:8000/docs**

### Step 2: Add Your Account
1. Click on the `POST /accounts/` endpoint
2. Click "Try it out"
3. Fill in your Twitter account details:
   ```json
   {
     "username": "your_twitter_username",
     "api_key": "your_api_key",
     "api_secret": "your_api_secret",
     "access_token": "your_access_token",
     "access_token_secret": "your_access_token_secret",
     "bearer_token": "your_bearer_token",
     "display_name": "Your Display Name"
   }
   ```
4. Click "Execute"

### Step 3: Test Your Account
1. Click on the `POST /accounts/{username}/test` endpoint
2. Enter your username
3. Click "Execute" to verify your credentials work

## Using with Claude Desktop

To use this MCP server with Claude Desktop, you need to configure Claude to connect to the server. Follow these steps:

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
        "PYTHONUNBUFFERED": "1"
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

## Using the Tools

### First Time: Add Your Account
```
Add my Twitter account with username "myusername", API key "xxx", API secret "xxx", access token "xxx", access token secret "xxx", and bearer token "xxx"
```

### Daily Usage: Just Use Username
Now you can use any tool with just your username:

- **Post a Tweet**:
  ```
  Post a tweet saying "Hello World!" using username "myusername"
  ```

- **Search Twitter**:
  ```
  Search Twitter for recent tweets about AI using username "myusername"
  ```

- **Get Timeline**:
  ```
  Show my Twitter timeline using username "myusername"
  ```

## Available Tools

### Account Management Tools

#### `add_twitter_account`
- **Description**: Add a new Twitter account to the database
- **Usage**: First time setup only
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

## Web API Endpoints

The server provides a web API for account management at **http://127.0.0.1:8000/docs**:

- `POST /accounts/` - Add/Update account
- `GET /accounts/` - List all accounts
- `GET /accounts/{username}` - Get specific account
- `PUT /accounts/{username}` - Update account
- `DELETE /accounts/{username}` - Delete account
- `PATCH /accounts/{username}/deactivate` - Deactivate account
- `POST /accounts/{username}/test` - Test credentials

## Security Features

1. **Local Storage**: All credentials stored locally in SQLite database
2. **No Environment Variables**: No need to set system-wide variables
3. **Per-Account Isolation**: Each account is completely separate
4. **Credential Validation**: Automatic testing of API keys
5. **Secure Access**: Web interface for safe account management

## Troubleshooting

- **Server Not Starting**:
    - Check the terminal output for errors
    - Verify that all dependencies are installed
    - Ensure port 8000 is available for the auth server

- **Authentication Errors**:
    - Use the web interface to test your credentials
    - Verify your Twitter Developer App permissions
    - Check that all 5 API credentials are correct

- **Account Not Found**:
    - Use `list_twitter_accounts` to see stored accounts
    - Add your account using `add_twitter_account`
    - Verify the username spelling

- **Web Interface Not Accessible**:
    - Check if the server is running
    - Verify the URL: http://127.0.0.1:8000/docs
    - Check firewall settings

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on the [GitHub repository](https://github.com/rafaljanicki/x-twitter-mcp-server).

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Author

- **Rafal Janicki** - [rafal@kult.io](mailto:rafal@kult.io)