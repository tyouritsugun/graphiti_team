# Debugging the MCP Server with VS Code and Claude Desktop

This guide provides a step-by-step process for setting up a local debugging environment for the Graphiti MCP server, allowing you to attach the VS Code debugger to a process launched by Claude Desktop.

## Overview

The recommended approach is to have Claude Desktop launch the server process and have VS Code "attach" to it. This allows you to debug the server in the exact environment it runs in when used by the host application.

## Prerequisites

1.  **Visual Studio Code**: With the official [Python extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python) installed.
2.  **uv**: The project's Python package manager. If you don't have it, install it by following the instructions in the main `mcp_server/README.md`.
3.  **A checkout of the `graphiti_team` repository.**

---

## Step 1: Install Dependencies

This is the most critical step. All dependencies, including development tools like `debugpy`, must be installed into a local virtual environment within the `mcp_server` directory.

1.  Navigate to the `mcp_server` directory:
    ```bash
    cd /path/to/your/graphiti_team/mcp_server
    ```

2.  Run the `uv sync` command with the `--all-extras` flag. This command reads the `pyproject.toml` file, creates a local virtual environment (`.venv`), and installs all main and development dependencies.
    ```bash
    uv sync --all-extras
    ```
This ensures that `azure-identity`, `debugpy`, and all other required packages are correctly installed in the `mcp_server/.venv` directory.

---

## Step 2: Configure VS Code for Attaching

VS Code needs to be told how to attach to the running server process.

1.  Create or open the `.vscode/launch.json` file at the root of the project.
2.  Add the following configuration. This tells VS Code to listen on `localhost:5678` for a Python process to attach to.

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Attach to MCP Server (Started by Claude)",
      "type": "python",
      "request": "attach",
      "connect": {
        "host": "localhost",
        "port": 5678
      },
      "pathMappings": [
        {
          "localRoot": "${workspaceFolder}",
          "remoteRoot": "."
        }
      ],
      "justMyCode": true
    }
  ]
}
```

---

## Step 3: Configure Claude Desktop

Claude Desktop needs to be configured to launch your MCP server script in a way that the debugger can connect to it.

1.  Open your Claude Desktop settings file.
2.  Add or modify the `graphiti` server configuration as shown below.

```json
"graphiti": {
  "command": "/your/path/to/graphiti_team/mcp_server/.venv/bin/python",
  "args": [
    "-Xfrozen_modules=off",
    "-m", "debugpy",
    "--listen", "5678",
    "/your/path/to/graphiti_team/mcp_server/graphiti_mcp_server.py",
    "--transport",
    "stdio"
  ],
  "timeout": 120,
  "env": {
    "NEO4J_URI": "bolt://localhost:7687",
    "NEO4J_USER": "neo4j",
    "NEO4J_PASSWORD": "demodemo",
    "NEO4J_DATABASE": "graphiti",
    "OPENAI_API_KEY": "your_openai_api_key_here",
    "USER_EMAIL": "your_email@example.com",
    "PROJECT_ID": "your_project_id"
  }
}
```

**IMPORTANT**:
-   Replace `/your/path/to/` with the **absolute path** to the project on your machine.
-   The `"command"` path **must** point to the `python` executable inside the `mcp_server/.venv` directory that was created in Step 1.
-   Update the values in the `env` block with your actual credentials and information.

**Argument Breakdown:**
-   `-Xfrozen_modules=off`: Prevents a common debugger warning and ensures breakpoints work reliably.
-   `-m debugpy`: Tells Python to run the `debugpy` module.
-   `--listen 5678`: Instructs `debugpy` to start a debug server on port 5678, allowing VS Code to connect.

---

## Step 4: The Debugging Workflow

You now have two options for debugging.

### Option A: Attach Anytime (Recommended for most cases)

This method is convenient and has no time pressure. The server starts normally, and you can attach the debugger whenever you're ready.

1.  **Start the Server**: In Claude Desktop, perform the action that launches the Graphiti MCP server. It will start up and connect successfully.
2.  **Attach the Debugger**: In VS Code, go to the "Run and Debug" panel (Shift+Cmd+D).
3.  Select **"Attach to MCP Server (Started by Claude)"** from the dropdown menu and press **F5** (or the green play button).
4.  The debugger will attach. You can now set breakpoints and debug any actions you take in Claude that trigger the server's tools.

### Option B: Attach at Startup (For debugging initialization)

Use this method if you need to debug the first few seconds of the server's startup process.

1.  **Modify Claude Desktop `args`**: Add the `--wait-for-client` flag.
    ```json
    "args": [
        "-m", "debugpy",
        "--listen", "5678",
        "--wait-for-client",  // <-- Add this flag
        ...
    ]
    ```
2.  **Start the Server**: In Claude Desktop, launch the server. The script will start but immediately **pause** and wait for the debugger.
3.  **Attach Quickly**: You have a limited time (the `timeout` in your config, e.g., 120s) to switch to VS Code, select the "Attach to MCP Server" configuration, and press **F5**.
4.  Once attached, the script will un-pause, and you can debug the initialization code.

Remove the `--wait-for-client` flag to return to the more convenient "Attach Anytime" workflow.