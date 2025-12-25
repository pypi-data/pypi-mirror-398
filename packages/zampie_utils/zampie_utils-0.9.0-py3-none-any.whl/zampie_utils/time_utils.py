import time
import threading
from functools import wraps
from typing import Optional, Callable, Any, Tuple

from .logger import logger


def format_time(seconds: float, unit: str = "auto") -> Tuple[float, str]:
    """
    自动格式化时间，返回格式化后的时间值和单位

    Args:
        seconds: 时间（秒）
        unit: 显示单位，"auto"为自动选择

    Returns:
        (格式化后的时间值, 单位字符串)
    """
    if unit == "auto":
        if seconds < 1:
            return seconds * 1000, "ms"
        elif seconds < 60:
            return seconds, "s"
        elif seconds < 3600:
            return seconds / 60, "min"
        else:
            return seconds / 3600, "h"
    elif unit == "ms":
        return seconds * 1000, "ms"
    elif unit == "min":
        return seconds / 60, "min"
    elif unit == "h":
        return seconds / 3600, "h"
    else:
        return seconds, "s"


class Timer:
    """
    线程安全的计时装饰器类，用于测量函数执行时间

    Args:
        unit: 时间单位，支持 "auto"(自动选择), "ms"(毫秒), "s"(秒), "min"(分钟), "h"(小时)
        name: 计时器名称，默认使用函数名

    被装饰的函数可以通过以下方式访问执行时间信息：
        - func.time_info: 包含所有时间信息的字典
        - func.get_time_info(): 获取时间信息字典的函数

        字典包含的字段：
        - last_execution_time: 最后一次执行的原始时间（秒）
        - last_formatted_time: 最后一次执行的格式化时间值
        - last_time_unit: 最后一次执行的时间单位
        - turn: 执行次数
        - total_execution_time: 总执行时间（秒，累计所有执行时间，可能包含并发重复计数）
        - total_formatted_time: 总执行时间的格式化值
        - total_time_unit: 总执行时间的单位
        - span_execution_time: 时间跨度（秒，从第一次开始到现在的时间，避免并发重复计数）
        - span_formatted_time: 时间跨度的格式化值
        - span_time_unit: 时间跨度的单位
        - average_time: 平均执行时间（基于总耗时/总次数）
        - average_formatted_time: 平均执行时间的格式化值
        - average_time_unit: 平均执行时间的单位
        - message: 完整的日志消息（包含执行时间、时间跨度与平均信息，以及唯一执行序号seq）

    Example:
        @Timer("ms", "数据处理")
        def process_data():
            # 处理数据
            pass

        process_data()

        # 获取时间信息
        info = process_data.get_time_info()
        print(f"执行时间: {info['last_formatted_time']:.3f} {info['last_time_unit']}")
        print(f"执行次数: {info['turn']}")
        print(f"总执行时间: {info['total_formatted_time']:.3f} {info['total_time_unit']}")
        print(f"时间跨度: {info['span_formatted_time']:.3f} {info['span_time_unit']}")
        print(f"完整消息: {info['message']}")
        if 'average_time' in info:
            print(f"平均时间: {info['average_formatted_time']:.3f} {info['average_time_unit']}")
    """

    def __init__(self, unit: str = "auto", name: str = ""):
        self.unit = unit
        self.name = name
        self.turn = 0
        self.total_execution_time = 0.0  # 总执行时间，累计所有执行时间
        self.span_execution_time = 0.0  # 时间跨度，从第一次开始到现在的时间
        self.first_start_time = None  # 第一次开始执行的时间
        # 添加线程锁来保证线程安全
        self._lock = threading.RLock()  # 使用可重入锁，支持同一线程多次获取
        # 用于生成唯一的执行序号
        self._execution_sequence = 0

    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            display_name = self.name if self.name else func.__name__

            # 记录第一次开始时间
            if self.first_start_time is None:
                self.first_start_time = time.time()

            logger.info(f'"{display_name}" start')
            start_time = time.time()

            error: Optional[Exception] = None
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                error = e
                raise
            finally:
                elapsed_time = time.time() - start_time

                # 使用锁保护所有共享状态的修改
                with self._lock:
                    # 保存当前执行的序号
                    self.turn += 1

                    self.total_execution_time += elapsed_time  # 累计总执行时间

                    # 计算时间跨度（从第一次开始到现在）
                    if self.first_start_time is not None:
                        self.span_execution_time = time.time() - self.first_start_time

                    # 在锁内计算所有需要的数据，确保数据一致性
                    formatted_time, unit = format_time(elapsed_time, self.unit)
                    total_formatted_time, total_unit = format_time(
                        self.total_execution_time, self.unit
                    )
                    span_formatted_time, span_unit = format_time(
                        self.span_execution_time, self.unit
                    )
                    # 以总耗时 / 总次数 计算平均耗时
                    avg_time = (
                        (self.total_execution_time / self.turn) if self.turn else 0.0
                    )
                    avg_formatted_time, avg_unit = format_time(avg_time, self.unit)

                    # 在锁内生成消息，使用唯一的执行序号
                    msg = (
                        f'"{display_name}" over, cost: {formatted_time:.2f} {unit}, '
                        f"avg: {avg_formatted_time:.2f} {avg_unit}, "
                        f"span: {span_formatted_time:.2f} {span_unit}, turn: {self.turn}"
                    )

                    if error is not None:
                        msg += f", error: {error}"

                    # 将执行时间信息存储在字典中
                    time_info = {
                        "message": msg,
                        "last_execution_time": elapsed_time,
                        "last_formatted_time": formatted_time,
                        "last_time_unit": unit,
                        "turn": self.turn,
                        "total_execution_time": self.total_execution_time,
                        "total_formatted_time": total_formatted_time,
                        "total_time_unit": total_unit,
                        "span_execution_time": self.span_execution_time,
                        "span_formatted_time": span_formatted_time,
                        "span_time_unit": span_unit,
                        "average_time": avg_time,
                        "average_formatted_time": avg_formatted_time,
                        "average_time_unit": avg_unit,
                    }

                # 在锁外记录日志，避免长时间持有锁
                if error is None:
                    logger.info(msg)
                else:
                    logger.error(msg)

                # 将时间信息附加到函数对象上
                wrapper.time_info = time_info

        # 添加获取时间信息字典的函数
        def get_time_info() -> dict:
            """获取执行时间信息的字典"""
            with self._lock:  # 确保读取时数据一致性
                return getattr(wrapper, "time_info", {})

        wrapper.get_time_info = get_time_info
        return wrapper


# 为了保持向后兼容，可以保留原来的函数版本
def timer(unit: str = "auto", name: str = "") -> Callable:
    """
    计时装饰器，用于测量函数执行时间

    Args:
        unit: 时间单位，支持 "auto"(自动选择), "ms"(毫秒), "s"(秒), "min"(分钟), "h"(小时)
        name: 自定义消息，默认使用函数名

    Returns:
        装饰器函数

    Example:
        @timer()  # 自动选择单位
        def process_data():
            # 处理数据
            pass

        @timer("ms", "数据处理")
        def process_data():
            # 处理数据
            pass
    """
    return Timer(unit, name)


class ContextTimer:
    """
    上下文管理器形式的计时器

    Args:
        name: 计时器名称
        unit: 时间单位，支持 "auto"(自动选择), "ms"(毫秒), "s"(秒), "min"(分钟), "h"(小时)

    Example:
        with ContextTimer("数据处理"):  # 自动选择单位
            # 处理数据
            pass

        with ContextTimer("数据处理", "ms"):
            # 处理数据
            pass
    """

    def __init__(self, name: str = "timer", unit: str = "auto"):
        self.name = name
        self.unit = unit
        self.start_time: Optional[float] = None

    def __enter__(self) -> "ContextTimer":
        logger.info(f"{self.name}: 开始计时")
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.start_time is None:
            return

        elapsed_time = time.time() - self.start_time
        formatted_time, unit = format_time(elapsed_time, self.unit)

        if exc_type is None:
            logger.info(f"{self.name} 执行完成，耗时: {formatted_time:.3f} {unit}")
        else:
            logger.error(f"{self.name} 执行异常，耗时: {formatted_time:.3f} {unit}")


def measure_time(func: Callable, *args, **kwargs) -> Tuple[Any, float]:
    """
    测量函数执行时间

    Args:
        func: 要测量的函数
        *args: 函数参数
        **kwargs: 函数关键字参数

    Returns:
        (函数返回值, 执行时间)
    """
    start_time = time.time()
    result = func(*args, **kwargs)
    elapsed_time = time.time() - start_time
    return result, elapsed_time


def sleep_with_log(seconds: float, msg: str = "") -> None:
    """
    带日志的睡眠函数

    Args:
        seconds: 睡眠时间（秒）
        msg: 日志消息
    """
    msg = msg or f"暂停 {seconds} 秒"
    logger.info(f"{msg}: 开始")
    time.sleep(seconds)
    logger.info(f"{msg}: 结束")


def timeout(seconds):
    """
    跨平台超时装饰器，限制函数执行时间

    Args:
        seconds: 超时时间（秒）
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            import threading
            import queue

            result_queue = queue.Queue()
            exception_queue = queue.Queue()

            def target():
                try:
                    result = func(*args, **kwargs)
                    result_queue.put(result)
                except Exception as e:
                    exception_queue.put(e)

            # 在单独线程中执行函数
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()

            # 等待结果或超时
            thread.join(timeout=seconds)

            if thread.is_alive():
                # 超时了
                raise TimeoutError(f"函数 {func.__name__} 执行超时 ({seconds}秒)")

            # 检查是否有异常
            if not exception_queue.empty():
                raise exception_queue.get()

            # 返回结果
            if not result_queue.empty():
                return result_queue.get()
            else:
                raise TimeoutError(f"函数 {func.__name__} 执行超时 ({seconds}秒)")

        return wrapper

    return decorator


def countdown(seconds: int, message: str = "等待中"):
    """
    倒计时函数，动态显示剩余时间

    Args:
        seconds: 倒计时的总秒数
        message: 显示的前缀消息
    """
    for remaining in range(seconds, 0, -1):
        mins, secs = divmod(remaining, 60)
        time_str = f"{mins:02d}:{secs:02d}"
        sys.stdout.write(f"\r{message} - 剩余时间: {time_str}")
        sys.stdout.flush()
        time.sleep(1)
    sys.stdout.write("\r" + " " * 50 + "\r")  # 清除倒计时行
    sys.stdout.flush()
