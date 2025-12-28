from .server import mcp_server

def main():
    import asyncio
    asyncio.run(mcp_server())

if __name__ == "__main__":
    main()
