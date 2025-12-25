from fastmcp import FastMCP
from datetime import datetime

mcp = FastMCP()

@mcp.tool
def get_current_time():
    """Get current time"""
    return datetime.now()

def main():
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000, path="/mcp")

if __name__ == "__main__":
    main()