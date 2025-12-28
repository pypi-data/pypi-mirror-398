"""RapidAPI客户端，获取抖音视频MP3地址"""
import requests
import re
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


def _extract_video_id(short_url: str) -> Optional[str]:
    """
    从抖音短链接中提取视频ID
    
    Args:
        short_url: 抖音短链接，例如：https://v.douyin.com/iijqA87/
    
    Returns:
        视频ID，如果提取失败则返回None
    """
    try:
        redirected_url = requests.get(short_url, allow_redirects=True, timeout=30).url
        match = re.search(r'video/(\d+)', redirected_url)
        if match:
            video_id = match.group(1)
            logger.info(f"成功提取视频ID: {video_id}")
            return video_id
        else:
            logger.warning(f"无法从重定向URL中提取视频ID: {redirected_url}")
            return None
    except Exception as e:
        logger.error(f"提取视频ID时出错: {str(e)}")
        return None


def get_douyin_mp3_url(douyin_url: str, api_key: str) -> Optional[str]:
    """
    通过RapidAPI获取抖音视频的MP3地址
    
    Args:
        douyin_url: 抖音短链接，例如：https://v.douyin.com/iijqA87/
        api_key: RapidAPI的API Key
    
    Returns:
        MP3音频文件的公网访问地址，如果获取失败则返回None
    """
    # 首先从短链接提取视频ID
    video_id = _extract_video_id(douyin_url)
    if not video_id:
        logger.error("无法从短链接中提取视频ID")
        return None
    
    url = "https://douyin-api-app-web.p.rapidapi.com/web/aweme/detail"
    
    headers = {
        "Content-Type": "application/json",
        "X-Rapidapi-Host": "douyin-api-app-web.p.rapidapi.com",
        "X-Rapidapi-Key": api_key
    }
    payload = {"id": video_id}
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        
        # 根据RapidAPI的响应结构提取MP3地址
        # 需要根据实际API响应格式调整
        if isinstance(data, dict):
            # 尝试多种可能的响应结构
            mp3_url = (
                data.get("data", {}).get("mp3_url") or
                data.get("data", {}).get("audio_url") or
                data.get("mp3_url") or
                data.get("audio_url") or
                data.get("data", {}).get("video", {}).get("play_addr", {}).get("url_list", [None])[0] or
                data.get("aweme_detail", {}).get("music", {}).get("play_url", {}).get("uri")
            )
            
            if mp3_url:
                logger.info(f"成功获取MP3地址: {mp3_url}")
                return mp3_url
            else:
                logger.warning(f"API响应中未找到MP3地址，响应数据: {data}")
                return None
        else:
            logger.warning(f"API响应格式异常: {type(data)}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"调用RapidAPI失败: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"处理RapidAPI响应时出错: {str(e)}")
        return None

