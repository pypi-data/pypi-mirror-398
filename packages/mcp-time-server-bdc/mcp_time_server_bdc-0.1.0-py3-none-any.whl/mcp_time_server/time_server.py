from typing import Optional 
from datetime import datetime 
import pytz 
import click
from mcp.server import FastMCP 


@click.command()
@click.option("--transport", type=click.Choice(["stdio", "streamable-http", "sse"]), 
              default="stdio", help="选择传输方式")
@click.option("--port", default=8000, help="服务器监听端口（仅用于网络传输）")
def main(transport: str, port: int): 
    """主函数，启动 MCP 服务器"""
    # 根据传输方式设置参数
    if transport in ["streamable-http", "sse"]:
        # 网络传输方式需要指定端口
        mcp = FastMCP("time-server", port=port)
    else:
        # stdio传输方式不需要端口
        mcp = FastMCP("time-server")
    
    # 在FastMCP实例创建后定义并注册工具函数
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
    
    # 运行服务器
    mcp.run(transport=transport)


if __name__ == "__main__": 
    main()