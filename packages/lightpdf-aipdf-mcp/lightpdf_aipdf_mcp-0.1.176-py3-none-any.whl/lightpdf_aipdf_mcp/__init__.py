from .api import server

def main():
    """Main entry point for the package (FastMCP version)."""
    server.cli_main()

# 只导出main函数
__all__ = ['main']