# Use an official Python image based on Debian
FROM python:3.13-slim

# Set the working directory in the container
WORKDIR /app

# Copy the project files
COPY . .

# Install dependencies using pip
RUN pip install --no-cache-dir .

# Command to run the MCP server (will be overridden by smithery.yaml, but good for local testing)
CMD ["python", "src/x_twitter_mcp/server.py"]