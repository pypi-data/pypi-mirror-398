# __main__.py
from .server import mcp
import sys

def main():
    """包的主入口点，当通过命令行调用时执行"""
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()