"""MCP Time Server - A Model Context Protocol server with timezone support."""

from typing import Optional
from datetime import datetime
import pytz
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("time-server")


@mcp.tool()
def get_current_time(timezone: Optional[str] = None) -> str:
    """获取当前时间的工具函数
    
    Args:
        timezone: 可选参数，时区字符串，例如 "Asia/Shanghai"、"America/New_York"
                  如果不提供，将使用系统默认时区
    
    Returns:
        格式化的当前时间字符串
    """
    try:
        if timezone:
            tz = pytz.timezone(timezone)
            current_time = datetime.now(tz)
        else:
            current_time = datetime.now()
        
        return current_time.strftime("%Y-%m-%d %H:%M:%S.%f %Z")
    except pytz.exceptions.UnknownTimeZoneError:
        return f"错误：未知的时区 '{timezone}'"


def main():
    """主函数，启动 MCP 服务器 (stdio 模式)"""
    mcp.run(transport="stdio")
