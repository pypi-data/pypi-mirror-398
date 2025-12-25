import base64
import requests
import os
from urllib.parse import urlparse


def download_file(url, file_path):
    response = requests.get(url)
    with open(file_path, "wb") as f:
        f.write(response.content)


def encode_base64(file_path):
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def get_file_base64(source):
    """
    从URL或本地路径获取文件的base64编码
    
    Args:
        source (str): URL或本地文件路径
        
    Returns:
        str: 文件的base64编码字符串
        
    Raises:
        FileNotFoundError: 当本地文件不存在时
        requests.RequestException: 当URL请求失败时
        ValueError: 当source既不是有效的URL也不是有效的本地路径时
    """
    # 检查是否为URL
    parsed_url = urlparse(source)
    if parsed_url.scheme in ('http', 'https'):
        # 从URL获取文件
        try:
            response = requests.get(source)
            response.raise_for_status()  # 检查请求是否成功
            return base64.b64encode(response.content).decode("utf-8")
        except requests.RequestException as e:
            raise requests.RequestException(f"从URL获取文件失败: {e}")
    
    # 检查是否为本地文件路径
    elif os.path.exists(source):
        try:
            with open(source, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except IOError as e:
            raise FileNotFoundError(f"读取本地文件失败: {e}")
    
    else:
        raise ValueError(f"无效的源路径或URL: {source}")


