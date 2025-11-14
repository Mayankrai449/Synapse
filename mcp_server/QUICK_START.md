# MCP Server - Quick Start (2 Minutes)

## Install

```bash
cd mcp_server
pip install fastmcp httpx
```

## Configure Claude Desktop

**Windows**: Edit `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "synapse": {
      "command": "python",
      "args": ["C:\\Users\\ACER\\OneDrive\\Desktop\\appointy\\mcp_server\\synapse_mcp.py"]
    }
  }
}
```

**Update path to match your location!**

## Restart Claude Desktop

Quit and reopen Claude Desktop completely.

## Test

**Ask Claude:**
```
Save these notes to my Synapse knowledge base:

Test MCP integration working!
```

**Claude responds:**
```
✓ Saved to Synapse!
Document ID: abc-123...
```

## Done! 🎉

Now tell Claude to save:
- Conversations: "Save our chat about X"
- Notes: "Save this idea: ..."
- Content: "Save this article: ..."

See **MCP_SERVER_GUIDE.md** for full documentation.
