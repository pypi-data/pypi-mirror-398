"""解析抖音分享文本，提取短链接"""
import re
from typing import Optional


def extract_douyin_url(share_text: str) -> Optional[str]:
    """
    从抖音分享文本中提取短链接
    
    Args:
        share_text: 抖音分享文本，例如：
            "7.46 z@G.vs YZZ:/ 08/31 随机进家做菜... https://v.douyin.com/ybL9NO9RjKA/ 复制此链接..."
    
    Returns:
        提取到的短链接，如果未找到则返回None
    """
    # 匹配抖音短链接格式：https://v.douyin.com/xxxxx/
    pattern = r'https://v\.douyin\.com/\w+/'
    match = re.search(pattern, share_text)
    
    if match:
        return match.group(0).rstrip('/')  # 移除末尾的斜杠
    
    return None

