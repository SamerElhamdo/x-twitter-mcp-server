# X (Twitter) MCP server

[![smithery badge](https://smithery.ai/badge/@rafaljanicki/x-twitter-mcp-server)](https://smithery.ai/server/@rafaljanicki/x-twitter-mcp-server)
[![PyPI version](https://badge.fury.io/py/x-twitter-mcp.svg)](https://badge.fury.io/py/x-twitter-mcp)

A Model Context Protocol (MCP) server for interacting with Twitter (X) via AI tools. This server allows you to fetch tweets, post tweets, search Twitter, manage followers, and more, all through natural language commands in AI Tools.

## Features

- Fetch user profiles, followers, and following lists.
- Post, delete, and favorite tweets.
- Search Twitter for tweets and trends.
- Manage bookmarks and timelines.
- Built-in rate limit handling for the Twitter API.
- Uses Twitter API v2 with proper authentication (API keys and tokens), avoiding the username/password hack to minimize the risk of account suspensions.
- Provides a complete implementation of Twitter API v2 endpoints for user management, tweet management, timelines, and search functionality.

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
npx -y @smithery/cli install /x-twitter-mcp-server --client claude
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

4. **Configure Environment Variables**:
    - Create a `.env` file in the project root (you can copy `.env.example` if provided).
    - Add your Twitter API credentials:
      ```
      TWITTER_API_KEY=your_api_key
      TWITTER_API_SECRET=your_api_secret
      TWITTER_ACCESS_TOKEN=your_access_token
      TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
      TWITTER_BEARER_TOKEN=your_bearer_token
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
If you installed from source and prefer to run the server using FastMCP’s development mode:

```bash
fastmcp dev src/x_twitter_mcp/server.py
```

The server will start and listen for MCP connections. You should see output like:
```
Starting TwitterMCPServer...
```

## Using with Claude Desktop

To use this MCP server with Claude Desktop, you need to configure Claude to connect to the server. Follow these steps:

### Step 1: Install Node.js
Claude Desktop uses Node.js to run MCP servers. If you don’t have Node.js installed:
- Download and install Node.js from [nodejs.org](https://nodejs.org/).
- Verify installation:
  ```bash
  node --version
  ```

### Step 2: Locate Claude Desktop Configuration
Claude Desktop uses a `claude_desktop_config.json` file to configure MCP servers.

- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

If the file doesn’t exist, create it.

### Step 3: Configure the MCP Server
Edit `claude_desktop_config.json` to include the `x-twitter-mcp` server. Replace `/path/to/x-twitter-mcp-server` with the actual path to your project directory (if installed from source) or the path to your Python executable (if installed from PyPI).

If installed from PyPI:
```json
{
  "mcpServers": {
    "x-twitter-mcp": {
      "command": "x-twitter-mcp-server",
      "args": [],
      "env": {
        "PYTHONUNBUFFERED": "1",
        "TWITTER_API_KEY": "your_api_key",
        "TWITTER_API_SECRET": "your_api_secret",
        "TWITTER_ACCESS_TOKEN": "your_access_token",
        "TWITTER_ACCESS_TOKEN_SECRET": "your_access_token_secret",
        "TWITTER_BEARER_TOKEN": "your_bearer_token"
      }
    }
  }
}
```

If installed from source with `uv`:
```json
{
  "mcpServers": {
    "x-twitter-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/x-twitter-mcp-server",
        "run",
        "x-twitter-mcp-server"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

- `"command": "x-twitter-mcp-server"`: Uses the CLI script directly if installed from PyPI.
- `"env"`: If installed from PyPI, you may need to provide environment variables directly in the config (since there’s no `.env` file). If installed from source, the `.env` file will be used.
- `"env": {"PYTHONUNBUFFERED": "1"}`: Ensures output is unbuffered for better logging in Claude.

### Step 4: Restart Claude Desktop
- Quit Claude Desktop completely.
- Reopen Claude Desktop to load the new configuration.

### Step 5: Verify Connection
- Open Claude Desktop.
- Look for a hammer or connector icon in the input area (bottom right corner). This indicates MCP tools are available.
- Click the icon to see the available tools from `x-twitter-mcp`, such as `post_tweet`, `search_twitter`, `get_user_profile`, etc.

### Step 6: Test with Claude
You can now interact with Twitter using natural language in Claude Desktop. Here are some example prompts:

- **Fetch a User Profile**:
  ```
  Get the Twitter profile for user ID 123456.
  ```
  Claude will call the `get_user_profile` tool and return the user’s details.

- **Post a Tweet**:
  ```
  Post a tweet saying "Hello from Claude Desktop! #MCP"
  ```
  Claude will use the `post_tweet` tool to post the tweet and confirm the action.

- **Search Twitter**:
  ```
  Search Twitter for recent tweets about AI.
  ```
  Claude will invoke the `search_twitter` tool and return relevant tweets.

- **Get Trends**:
  ```
  What are the current trending topics on Twitter?
  ```
  Claude will use the `get_trends` tool to fetch trending topics.

When prompted, grant Claude permission to use the MCP tools for the chat session.

## Troubleshooting

- **Server Not Starting**:
    - Ensure your `.env` file has all required Twitter API credentials (if installed from source).
    - If installed from PyPI, ensure environment variables are set in `claude_desktop_config.json` or your shell.
    - Check the terminal output for errors when running `x-twitter-mcp-server`.
    - Verify that `uv` or your Python executable is correctly installed and accessible.

- **Claude Not Detecting the Server**:
    - Confirm the path in `claude_desktop_config.json` is correct.
    - Ensure the `command` and `args` point to the correct executable and script.
    - Restart Claude Desktop after updating the config file.
    - Check Claude’s Developer Mode logs (Help → Enable Developer Mode → Open MCP Log File) for errors.

- **Rate Limit Errors**:
    - The server includes rate limit handling, but if you hit Twitter API limits, you may need to wait for the reset window (e.g., 15 minutes for tweet actions).

- **Syntax Warnings**:
    - If you see `SyntaxWarning` messages from Tweepy, they are due to docstring issues in Tweepy with Python 3.13. The server includes a warning suppression to handle this.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on the [GitHub repository](https://github.com/rafaljanicki/x-twitter-mcp-server).

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Author

- **Rafal Janicki** - [rafal@kult.io](mailto:rafal@kult.io)