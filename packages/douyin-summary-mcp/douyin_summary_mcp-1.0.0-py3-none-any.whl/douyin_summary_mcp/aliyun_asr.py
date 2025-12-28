"""阿里云语音识别客户端"""
import requests
import time
import logging
import json
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def submit_asr_task(mp3_url: str, api_key: str) -> Optional[str]:
    """
    提交阿里云语音识别异步任务
    
    Args:
        mp3_url: 音频文件的公网访问URL
        api_key: 阿里云DashScope API Key
    
    Returns:
        任务ID (task_id)，如果提交失败则返回None
    """
    url = "https://dashscope.aliyuncs.com/api/v1/services/audio/asr/transcription"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-DashScope-Async": "enable"
    }
    
    payload = {
        "model": "qwen3-asr-flash-filetrans",
        "input": {
            "file_url": mp3_url
        },
        "parameters": {
            "channel_id": [0],
            "enable_itn": False
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # 提取task_id
        if isinstance(data, dict):
            task_id = data.get("output", {}).get("task_id") or data.get("task_id")
            if task_id:
                logger.info(f"成功提交ASR任务，task_id: {task_id}")
                return task_id
            else:
                logger.warning(f"API响应中未找到task_id，响应数据: {data}")
                return None
        else:
            logger.warning(f"API响应格式异常: {type(data)}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"提交ASR任务失败: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"处理ASR任务响应时出错: {str(e)}")
        return None


def _download_transcription_result(transcription_url: str) -> Optional[Dict[str, Any]]:
    """
    从transcription_url下载并解析识别结果JSON文件
    
    Args:
        transcription_url: 识别结果JSON文件的URL
    
    Returns:
        解析后的JSON字典，如果下载或解析失败则返回None
    """
    try:
        logger.info(f"正在下载识别结果: {transcription_url}")
        response = requests.get(transcription_url, timeout=30)
        response.raise_for_status()
        
        # 解析JSON内容
        result_data = response.json()
        logger.info("成功下载并解析识别结果")
        return result_data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"下载识别结果失败: {str(e)}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"解析识别结果JSON失败: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"处理识别结果时出错: {str(e)}")
        return None


def get_asr_result(task_id: str, api_key: str) -> Optional[Dict[str, Any]]:
    """
    查询阿里云语音识别任务结果
    
    Args:
        task_id: 任务ID
        api_key: 阿里云DashScope API Key
    
    Returns:
        任务结果字典，包含状态和识别文本，如果查询失败则返回None
    """
    url = f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-DashScope-Async": "enable",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if isinstance(data, dict):
            return data
        else:
            logger.warning(f"API响应格式异常: {type(data)}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"查询ASR任务结果失败: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"处理ASR任务结果时出错: {str(e)}")
        return None


def recognize_audio(mp3_url: str, api_key: str, max_retries: int = 30, poll_interval: int = 5) -> Optional[str]:
    """
    完整的音频识别流程：提交任务 -> 轮询结果 -> 返回识别文本
    
    Args:
        mp3_url: 音频文件的公网访问URL
        api_key: 阿里云DashScope API Key
        max_retries: 最大轮询次数，默认30次
        poll_interval: 轮询间隔（秒），默认5秒
    
    Returns:
        识别出的文本内容，如果失败则返回None
    """
    # 1. 提交任务
    task_id = submit_asr_task(mp3_url, api_key)
    if not task_id:
        logger.error("提交ASR任务失败")
        return None
    
    # 2. 轮询任务结果
    for attempt in range(max_retries):
        logger.info(f"查询任务结果 (第 {attempt + 1}/{max_retries} 次)...")
        
        result = get_asr_result(task_id, api_key)
        if not result:
            logger.warning(f"第 {attempt + 1} 次查询失败，继续重试...")
            time.sleep(poll_interval)
            continue
        
        # 检查任务状态
        task_status = result.get("output", {}).get("task_status") or result.get("task_status")
        
        if task_status == "SUCCEEDED":
            # 任务成功，需要从transcription_url下载识别结果
            output = result.get("output", {})
            result_data = output.get("result", {})
            transcription_url = result_data.get("transcription_url")
            
            if not transcription_url:
                logger.error("任务成功但未找到transcription_url")
                logger.debug(f"完整响应: {result}")
                return None
            
            # 下载并解析识别结果JSON文件
            transcription_result = _download_transcription_result(transcription_url)
            if not transcription_result:
                logger.error("下载识别结果失败")
                return None
            
            # 从识别结果中提取文本
            # 根据DashScope filetrans的JSON格式，总文本内容在transcripts[0].text中
            transcripts = transcription_result.get("transcripts", [])
            
            if transcripts and isinstance(transcripts, list) and len(transcripts) > 0:
                # 方法1: 从transcripts[0].text提取（标准格式）
                first_transcript = transcripts[0]
                if isinstance(first_transcript, dict):
                    text = first_transcript.get("text")
                    if text and isinstance(text, str):
                        logger.info(f"识别成功，文本长度: {len(text)} 字符")
                        return text
            
            # 方法2: 如果transcripts[0].text不存在，尝试遍历所有transcripts合并文本
            if transcripts and isinstance(transcripts, list):
                text_parts = []
                for transcript in transcripts:
                    if isinstance(transcript, dict):
                        text = transcript.get("text")
                        if text and isinstance(text, str):
                            text_parts.append(text)
                
                if text_parts:
                    # 使用空字符串连接，保持原始文本格式
                    recognized_text = "".join(text_parts)
                    logger.info(f"识别成功，文本长度: {len(recognized_text)} 字符")
                    return recognized_text
            
            # 方法3: 兼容其他可能的格式（备选方案）
            text = transcription_result.get("text")
            if text and isinstance(text, str):
                logger.info(f"识别成功，文本长度: {len(text)} 字符")
                return text
            
            # 如果所有方法都失败，记录完整的响应以便调试
            logger.warning(f"识别结果中未找到文本内容，完整结果: {transcription_result}")
            return None
                    
        elif task_status == "FAILED":
            error_msg = result.get("output", {}).get("message") or result.get("message") or "未知错误"
            logger.error(f"ASR任务失败: {error_msg}")
            return None
            
        elif task_status in ["PENDING", "RUNNING"]:
            # 任务还在进行中，继续等待
            logger.info(f"任务状态: {task_status}，等待 {poll_interval} 秒后重试...")
            time.sleep(poll_interval)
        else:
            logger.warning(f"未知的任务状态: {task_status}")
            time.sleep(poll_interval)
    
    # 超过最大重试次数
    logger.error(f"任务超时，已重试 {max_retries} 次")
    return None

