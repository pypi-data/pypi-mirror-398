"""
时间服务器主模块

提供JSON-RPC接口的时间服务器，支持获取不同时区的当前时间。
使用FastAPI框架实现，可通过uvicorn运行。
"""

import json
import traceback
from datetime import datetime
import pytz
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# 创建FastAPI应用实例
app = FastAPI()
# 为了兼容性，同时创建其他常用名称
mcp = app
server = app

@app.post("/")
async def handle_jsonrpc(request: Request):
    """处理JSON-RPC请求的端点"""
    try:
        # 读取请求体
        post_data = await request.body()
        post_data_str = post_data.decode('utf-8')
        
        print(f"收到请求: {post_data_str}")
        
        # 解析JSON请求
        request_data = json.loads(post_data_str)
        
        # 检查是否是工具调用请求
        if request_data.get('method') == 'tools/get_current_time':
            # 获取参数
            params = request_data.get('params', {})
            timezone = params.get('timezone')
            
            # 调用时间工具函数
            result = get_current_time(timezone)
            
            # 构造响应
            response = {
                "jsonrpc": "2.0",
                "result": result,
                "id": request_data.get('id')
            }
            
            # 发送响应
            return JSONResponse(content=response)
            
        else:
            # 未知方法
            return JSONResponse(
                status_code=404,
                content={"error": f"Unknown method: {request_data.get('method')}"}
            )
            
    except json.JSONDecodeError:
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid JSON format"}
        )
    except Exception as e:
        # 记录详细错误信息
        error_info = traceback.format_exc()
        print(f"处理请求时发生错误: {error_info}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

def get_current_time(timezone=None):
    """获取当前时间，支持可选的时区参数"""
    try:
        if timezone:
            tz = pytz.timezone(timezone)
            current_time = datetime.now(tz)
            return current_time.strftime("%Y-%m-%d %H:%M:%S %Z")
        else:
            current_time = datetime.now()
            return current_time.strftime("%Y-%m-%d %H:%M:%S")
    except pytz.exceptions.UnknownTimeZoneError:
        return f"错误: 未知的时区 '{timezone}'"
    except Exception as e:
        return f"获取时间时发生错误: {str(e)}"

# 在main.py文件末尾添加main函数
def main():
    """命令行入口点"""
    import uvicorn
    print("正在启动时间服务器...")
    print("服务器已启动，监听地址: http://localhost:8000")
    print("提供的方法: tools/get_current_time")
    print("按 Ctrl+C 停止服务器")
    uvicorn.run("time_server_pkg.main:app", host="localhost", port=8000, reload=True)

# 修改直接运行部分，调用main函数
if __name__ == "__main__":
    main()
