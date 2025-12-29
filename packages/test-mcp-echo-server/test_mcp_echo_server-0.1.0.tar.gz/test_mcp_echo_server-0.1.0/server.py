import os
from mcp.server.fastmcp import FastMCP

def main():
    server = FastMCP(
        "echo",
        json_response=os.environ.get("MCP_JSON")=="True",
        host=os.environ.get("MCP_HOST", "0.0.0.0"),
        port=int(os.environ.get("MCP_PORT", 8000)))

    @server.tool()
    def echo(text: str) -> str:
        return text

    server.run("streamable-http")

if __name__ == "__main__":
    main()
