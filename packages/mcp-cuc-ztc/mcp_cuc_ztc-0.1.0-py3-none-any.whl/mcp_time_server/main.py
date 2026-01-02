from typing import Optional
from datetime import datetime
import pytz
from mcp.server.fastmcp import FastMCP

# 初始化 FastMCP 服务器实例
# 参数 "time-server" 是服务器的名称
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
            # 如果提供了时区参数，使用指定的时区
            tz = pytz.timezone(timezone)
            current_time = datetime.now(tz)
        else:
            # 如果没有提供时区参数，使用系统默认时区
            current_time = datetime.now()
        
        # 格式化时间字符串
        # 格式：YYYY-MM-DD HH:MM:SS.SSSSSS 时区名称
        return current_time.strftime("%Y-%m-%d %H:%M:%S.%f %Z")
    except pytz.exceptions.UnknownTimeZoneError:
        # 处理无效的时区参数
        return f"错误：未知的时区 '{timezone}'"


def main():
    """主函数，启动 MCP 服务器"""
    # 使用 stdio 传输方式运行服务器
    # 这种方式适用于本地进程间通信
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
