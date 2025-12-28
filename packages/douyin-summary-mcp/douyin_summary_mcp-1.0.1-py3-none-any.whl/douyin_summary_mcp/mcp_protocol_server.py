"""MCP协议服务器实现"""
import json
import sys
import logging
from typing import Any, Dict, List, Optional
import os

from .douyin_parser import extract_douyin_url
from .rapidapi_client import get_douyin_mp3_url
from .aliyun_asr import recognize_audio
from .qwen_client import format_dialogue

# 配置日志（输出到stderr，避免干扰stdout的JSON-RPC通信）
logging.basicConfig(
    level=logging.WARNING,  # MCP服务器通常使用WARNING级别，减少日志输出
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


class MCPServer:
    """MCP协议服务器"""
    
    def __init__(self):
        self.rapidapi_key = os.getenv("RAPIDAPI_KEY")
        self.dashscope_api_key = os.getenv("DASHSCOPE_API_KEY")
        
    def validate_keys(self) -> Optional[str]:
        """验证API Keys是否配置"""
        missing = []
        if not self.rapidapi_key:
            missing.append("RAPIDAPI_KEY")
        if not self.dashscope_api_key:
            missing.append("DASHSCOPE_API_KEY")
        
        if missing:
            return f"缺少必要的环境变量: {', '.join(missing)}"
        return None
    
    def handle_initialize(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理initialize请求"""
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "douyin-summary-mcp",
                    "version": "1.0.0"
                }
            }
        }
    
    def handle_tools_list(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理tools/list请求"""
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "tools": [
                    {
                        "name": "process_douyin_share",
                        "description": "处理抖音分享链接，提取音频并进行语音识别，最后使用AI整理对话内容。返回结构化的对话JSON数组。",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "share_text": {
                                    "type": "string",
                                    "description": "抖音分享文本，包含短链接的完整分享内容"
                                }
                            },
                            "required": ["share_text"]
                        }
                    }
                ]
            }
        }
    
    def handle_tools_call(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理tools/call请求"""
        params = request.get("params", {})
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name == "process_douyin_share":
            return self._process_douyin_share_tool(request, arguments)
        else:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32601,
                    "message": f"未知的工具: {tool_name}"
                }
            }
    
    def _process_douyin_share_tool(self, request: Dict[str, Any], arguments: Dict[str, Any]) -> Dict[str, Any]:
        """处理process_douyin_share工具调用"""
        # 验证API Keys
        error_msg = self.validate_keys()
        if error_msg:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32602,
                    "message": error_msg
                }
            }
        
        share_text = arguments.get("share_text")
        if not share_text:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32602,
                    "message": "缺少必需参数: share_text"
                }
            }
        
        try:
            # 调用处理函数
            result = self._process_douyin_share(share_text)
            
            if result["success"]:
                # 构建返回内容
                content_parts = []
                
                # 添加基本信息
                info_text = f"处理成功！\n\n"
                info_text += f"抖音链接: {result['data']['douyin_url']}\n"
                info_text += f"MP3地址: {result['data']['mp3_url']}\n"
                info_text += f"识别文本长度: {len(result['data']['recognized_text'])} 字符\n\n"
                
                content_parts.append({
                    "type": "text",
                    "text": info_text
                })
                
                # 添加原始识别文本
                content_parts.append({
                    "type": "text",
                    "text": f"原始识别文本:\n{result['data']['recognized_text']}\n\n"
                })
                
                # 添加格式化对话
                if result['data'].get('formatted_dialogue'):
                    import json as json_lib
                    dialogue_json = json_lib.dumps(
                        result['data']['formatted_dialogue'],
                        ensure_ascii=False,
                        indent=2
                    )
                    content_parts.append({
                        "type": "text",
                        "text": f"格式化对话（JSON）:\n{dialogue_json}"
                    })
                
                return {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {
                        "content": content_parts,
                        "isError": False
                    }
                }
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"处理失败: {result['message']}"
                            }
                        ],
                        "isError": True
                    }
                }
                
        except Exception as e:
            logger.exception("处理抖音分享时出错")
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32603,
                    "message": f"内部错误: {str(e)}"
                }
            }
    
    def _process_douyin_share(self, share_text: str) -> Dict[str, Any]:
        """处理抖音分享链接的核心逻辑"""
        result = {
            "success": False,
            "message": "",
            "data": None
        }
        
        # 步骤1: 解析抖音分享文本，提取短链接
        douyin_url = extract_douyin_url(share_text)
        if not douyin_url:
            result["message"] = "未能从分享文本中提取到抖音短链接"
            return result
        
        # 步骤2: 调用RapidAPI获取MP3地址
        mp3_url = get_douyin_mp3_url(douyin_url, self.rapidapi_key)
        if not mp3_url:
            result["message"] = "未能从RapidAPI获取到MP3地址"
            return result
        
        # 步骤3: 调用阿里云录音文件识别接口
        recognized_text = recognize_audio(mp3_url, self.dashscope_api_key)
        if not recognized_text:
            result["message"] = "语音识别失败或未识别出文本"
            return result
        
        # 步骤4: 调用阿里千问大模型整理对话内容
        formatted_dialogue = format_dialogue(recognized_text, self.dashscope_api_key)
        if not formatted_dialogue:
            formatted_dialogue = None
        
        # 成功返回结果
        result["success"] = True
        result["message"] = "处理成功"
        result["data"] = {
            "douyin_url": douyin_url,
            "mp3_url": mp3_url,
            "recognized_text": recognized_text,
            "formatted_dialogue": formatted_dialogue
        }
        
        return result
    
    def run(self):
        """运行MCP服务器主循环"""
        try:
            for line in sys.stdin:
                if not line.strip():
                    continue
                    
                try:
                    # 解析JSON-RPC请求
                    request = json.loads(line.strip())
                    
                    # 获取方法名
                    method = request.get("method")
                    request_id = request.get("id")
                    
                    # 处理不同的请求类型
                    if method == "initialize":
                        response = self.handle_initialize(request)
                    elif method == "tools/list":
                        response = self.handle_tools_list(request)
                    elif method == "tools/call":
                        response = self.handle_tools_call(request)
                    elif method == "ping":
                        # 处理ping请求
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {}
                        }
                    elif method is None:
                        # 可能是通知（notification），不需要响应
                        continue
                    else:
                        # 未知方法
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {
                                "code": -32601,
                                "message": f"未知方法: {method}"
                            }
                        }
                    
                    # 发送响应（如果有request_id，说明需要响应）
                    if request_id is not None:
                        print(json.dumps(response), flush=True)
                    
                except json.JSONDecodeError as e:
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": f"JSON解析错误: {str(e)}"
                        }
                    }
                    print(json.dumps(error_response), flush=True)
                except Exception as e:
                    logger.exception("处理请求时出错")
                    request_id = request.get("id") if 'request' in locals() else None
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32603,
                            "message": f"内部错误: {str(e)}"
                        }
                    }
                    if request_id is not None:
                        print(json.dumps(error_response), flush=True)
        except KeyboardInterrupt:
            # 优雅退出
            pass
        except Exception as e:
            logger.exception("MCP服务器运行时出错")
            sys.exit(1)


def main():
    """MCP服务器入口"""
    server = MCPServer()
    server.run()


if __name__ == "__main__":
    main()

