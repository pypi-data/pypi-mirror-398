"""阿里千问大模型客户端，用于整理对话内容"""
import dashscope
import json
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


def format_dialogue(recognized_text: str, api_key: str) -> Optional[List[Dict[str, Any]]]:
    """
    使用阿里千问大模型整理对话内容，返回格式化的JSON数组
    
    Args:
        recognized_text: ASR识别出的原始文本
        api_key: 阿里云DashScope API Key
    
    Returns:
        JSON数组，每个元素包含说话人的角色和说话的文本，格式：
        [
            {"speaker": "角色1", "text": "说话内容1"},
            {"speaker": "角色2", "text": "说话内容2"},
            ...
        ]
        如果处理失败则返回None
    """
    # 设置API Key
    dashscope.api_key = api_key
    
    # 构建提示词
    prompt = f"""这是一份录音文件的文字转写，请将以下对话内容整理为JSON数组，每个元素包含说话人的角色（speaker）和说话的文本（text）。

要求：
1. 仔细分析对话内容，识别不同的说话人
2. 根据对话内容推断说话人的角色（如：主持人、嘉宾、用户、客服等，如果无法确定具体角色，可以使用"说话人1"、"说话人2"等）
3. 将对话按照说话人进行分段
4. 返回标准的JSON数组格式

输出格式示例：
[
  {{"speaker": "说话人1", "text": "第一段对话内容"}},
  {{"speaker": "说话人2", "text": "第二段对话内容"}},
  {{"speaker": "说话人1", "text": "第三段对话内容"}}
]

对话内容：
{recognized_text}

请直接返回JSON数组，不要包含任何其他说明文字。"""

    try:
        logger.info("正在调用千问大模型整理对话内容...")
        
        # 调用千问大模型API
        response = dashscope.Generation.call(
            model='qwen-plus',
            messages=[
                {
                    'role': 'system',
                    'content': '你是一个专业的对话整理助手，擅长将对话内容整理为结构化的JSON格式。'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            result_format='message'  # 返回消息格式
        )
        
        if response.status_code != 200:
            error_msg = getattr(response, 'message', '未知错误')
            logger.error(f"调用千问大模型失败，状态码: {response.status_code}, 错误: {error_msg}")
            return None
        
        # 提取模型返回的内容
        try:
            content = response.output.choices[0].message.content
        except (AttributeError, IndexError, KeyError) as e:
            logger.error(f"解析API响应失败: {str(e)}")
            logger.debug(f"完整响应: {response}")
            return None
        
        # 尝试解析JSON
        try:
            # 如果返回的内容包含代码块标记，需要提取JSON部分
            if '```json' in content:
                # 提取JSON代码块中的内容
                start = content.find('```json') + 7
                end = content.find('```', start)
                if end != -1:
                    content = content[start:end].strip()
            elif '```' in content:
                # 提取普通代码块中的内容
                start = content.find('```') + 3
                end = content.find('```', start)
                if end != -1:
                    content = content[start:end].strip()
            
            # 解析JSON
            dialogue_list = json.loads(content)
            
            # 验证格式
            if not isinstance(dialogue_list, list):
                logger.error(f"返回格式错误，期望数组，实际: {type(dialogue_list)}")
                return None
            
            # 验证每个元素是否包含必要的字段
            for item in dialogue_list:
                if not isinstance(item, dict):
                    logger.error(f"数组元素格式错误，期望字典，实际: {type(item)}")
                    return None
                if 'speaker' not in item or 'text' not in item:
                    logger.error(f"数组元素缺少必要字段，元素: {item}")
                    return None
            
            logger.info(f"成功整理对话内容，共 {len(dialogue_list)} 条记录")
            return dialogue_list
            
        except json.JSONDecodeError as e:
            logger.error(f"解析JSON失败: {str(e)}")
            logger.debug(f"原始返回内容: {content}")
            return None
            
    except Exception as e:
        logger.error(f"调用千问大模型时出错: {str(e)}")
        return None

