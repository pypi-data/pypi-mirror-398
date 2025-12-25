import re
import json5
import textwrap


def find_emojis(response):
    """
    匹配 emoji
    """

    emoji_pattern = re.compile(
        r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F700-\U0001F77F"
        r"\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F"
        r"\U0001FA70-\U0001FAFF\U00002640\U00002642]",  # 添加 U+2640 和 U+2642 范围
        flags=re.UNICODE,
    )

    emojis = emoji_pattern.findall(response)
    return emojis


def find_expressings(response):
    """
    匹配 emoji
    """

    expression_pattern = re.compile(r"<.*?>")

    # 查找匹配项
    expressions = expression_pattern.findall(response)
    return expressions


def remove_blank_lines(dialog):
    """
    Args:
        dialog: str, dialog content
    """
    dialog = dialog.strip()
    dialog_list = []
    for line in dialog.split("\n"):
        if not line:
            continue
        dialog_list.append(line)

    dialog = "\n".join(dialog_list)

    return dialog


def find_chinese(text):
    """
    提取文本中的中文字符

    Args:
        text: str, 输入文本

    Returns:
        list: 包含所有中文字符的列表
    """
    chinese_pattern = re.compile(r"[\u4e00-\u9fff]+", flags=re.UNICODE)
    chinese_chars = chinese_pattern.findall(text)
    return "".join(chinese_chars)


def load_json_block(json_text: str):
    """解析大模型输出的JSON代码块

    Args:
        json_text: 大模型返回的文本，可能包含JSON代码块

    Returns:
        Any: 解析后的对象

    Raises:
        ValueError: 当JSON解析失败时，包含原始字符串信息
    """

    json_text = json_text.strip()
    json_content = None

    # 先判断是否包含```json代码块
    if "```json" in json_text:
        json_pattern = r"```json\s*(.*?)\s*```"
        match = re.search(json_pattern, json_text, re.DOTALL)
        if match:
            json_content = match.group(1).strip()

    # 再判断是否包含普通```代码块
    elif "```" in json_text:
        code_pattern = r"```\s*(.*?)\s*```"
        match = re.search(code_pattern, json_text, re.DOTALL)
        if match:
            json_content = match.group(1).strip()

    else:
        json_content = json_text

    # 如果没有提取到任何内容，使用原始文本
    if json_content is None:
        json_content = json_text

    try:
        return json5.loads(json_content)
    except Exception as e:
        raise ValueError(
            f"JSON解析失败: {str(e)}\n原始字符串: {textwrap.shorten(json_text, width=200, placeholder='...')}"
        ) from e


def truncate_string(text: str, max_length: int = 200, ellipsis: str = "...") -> str:
    """
    截断过长的字符串，用省略号代替超长部分

    Args:
        text: str, 要截断的字符串
        # max_length: int, 最大长度，默认200
        ellipsis: str, 省略号样式，默认"..."

    Returns:
        str: 截断后的字符串

    Examples:
        >>> truncate_string("这是一个很长的字符串，需要被截断", 10)
        '这是一个很长的...'
        >>> truncate_string("短字符串", 10)
        '短字符串'
        >>> truncate_string("测试", 5, "…")
        '测试'
    """
    if not isinstance(text, str):
        text = str(text)

    if len(text) <= max_length:
        return text

    # 计算实际可显示字符数（减去省略号长度）
    available_length = max_length - len(ellipsis)

    if available_length <= 0:
        return ellipsis[:max_length]

    return text[:available_length] + ellipsis
