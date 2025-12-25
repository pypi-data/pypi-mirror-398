import random
import time
import threading
from functools import wraps

from .logger import logger
from .async_utils import parallel_map


def log_calls(level="info", log_args=True, log_result=True, log_exception=True):
    """
    函数调用日志装饰器，记录函数调用、参数、返回值和异常

    Args:
        level: 日志级别，支持 "debug", "info", "notice", "warning", "error", "critical"
        log_args: 是否记录函数参数
        log_result: 是否记录函数返回值
        log_exception: 是否记录异常信息

    Example:
        @log_calls("info", log_args=True, log_result=True)
        def process_data(x, y):
            return x + y

        @log_calls("debug", log_exception=False)
        def risky_operation():
            # 只记录调用，不记录异常
            pass
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 获取日志函数
            log_func = logger.log_router.get(level.lower(), logger.info)

            # 记录函数调用
            call_msg = f"调用函数: {func.__name__}"
            if log_args:
                args_str = ", ".join([str(arg) for arg in args])
                kwargs_str = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
                params = []
                if args_str:
                    params.append(f"args=({args_str})")
                if kwargs_str:
                    params.append(f"kwargs={{{kwargs_str}}}")
                call_msg += f", 参数: {', '.join(params)}"

            log_func(call_msg)

            try:
                result = func(*args, **kwargs)

                # 记录返回值
                if log_result:
                    result_msg = f"函数 {func.__name__} 返回: {result}"
                    log_func(result_msg)

                return result

            except Exception as e:
                if log_exception:
                    error_msg = f"函数 {func.__name__} 异常: {type(e).__name__}: {e}"
                    logger.error(error_msg)
                raise

        return wrapper

    return decorator


def mapable(func):
    """
    装饰器：将普通函数转换为可并行映射的函数

    Args:
        func: 要装饰的函数

    Returns:
        装饰后的函数，支持 .map() 方法

    Examples:
        @mapable
        def process_item(x):
            return x * 2

        # 使用方式
        results = process_item.map([1, 2, 3, 4, 5])

        # 或者直接调用（保持原函数行为）
        result = process_item(5)  # 返回 10
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        """
        包装器函数，用于保持原函数的行为和元数据

        作用：
        1. 保持原函数行为：当直接调用装饰后的函数时，行为与原始函数完全一致
        2. 保持元数据：@wraps(func) 确保装饰后的函数保持原函数的 __name__、__doc__ 等元数据
        3. 避免污染原函数：不直接修改原函数对象，而是创建新的包装器
        4. 为 .map() 方法提供基础：后续将 map_method 绑定到 wrapper.map

        为什么不能直接返回 func：
        - 直接返回 func 会永久修改原函数对象（添加 .map 属性）
        - 违反装饰器最佳实践，可能产生副作用
        - 多次装饰同一函数时会产生问题
        """
        return func(*args, **kwargs)

    def map_method(items, description=None, log_level="none", max_workers=1, progress_type="rich"):
        """
        并行映射方法

        Args:
            items: 输入数据列表
            description: 进度条描述，默认为函数名 + "running"
            log_level: 日志级别
            max_workers: 最大工作线程数

        Returns:
            按输入顺序排列的结果列表
        """
        return parallel_map(func, items, description, log_level, max_workers, progress_type)

    # 将 map 方法绑定到函数对象
    wrapper.map = map_method
    return wrapper


def conditional(condition_func):
    """
    条件执行装饰器，根据条件决定是否执行函数

    Args:
        condition_func: 条件函数，返回True时执行原函数
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if condition_func():
                return func(*args, **kwargs)
            else:
                logger.info(f"条件不满足，跳过函数 {func.__name__}")
                return None

        return wrapper

    return decorator


def retry(retries=3, delay=1, backoff=0.25):
    """
    重试装饰器，当函数执行失败时自动重试指定次数
    
    Args:
        retries (int): 最大重试次数，默认为3次
        delay (float): 基础延迟时间（秒），默认为1秒
        backoff (float): 退避系数，用于计算随机延迟，默认为0.25
        
    Returns:
        function: 装饰器函数
        
    Features:
        - 支持指数退避：每次重试的延迟时间会加上随机因子，避免多个请求同时重试
        - 错误历史记录：记录所有重试过程中的错误信息
        - 详细日志：记录重试过程和最终失败信息
        - 随机延迟：delay + delay * backoff * (1 - 2 * random.random())
        
    Examples:
        @retry(retries=3, delay=1, backoff=0.25)
        def unstable_api_call():
            # 可能失败的API调用
            return requests.get("http://example.com")
            
        @retry(retries=5, delay=2, backoff=0.5)
        def database_operation():
            # 数据库操作，重试5次，基础延迟2秒
            return db.execute("SELECT * FROM users")
            
        # 使用默认参数
        @retry()
        def simple_operation():
            return some_risky_function()
    """

    def decorator(func):
        """
        内部装饰器函数
        
        Args:
            func: 要装饰的函数
            
        Returns:
            function: 包装后的函数
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            """
            包装器函数，实现重试逻辑
            
            Args:
                *args: 位置参数
                **kwargs: 关键字参数
                
            Returns:
                原函数的返回值
                
            Raises:
                Exception: 当所有重试都失败时，抛出包含所有错误信息的异常
            """

            attempts = retries
            err_history = []
            while attempts > 0:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts -= 1
                    err_history.append(e)
                    if attempts == 0:
                        err_text = "\n".join([str(err) for err in err_history])
                        logger.error(f"retry failed: {err_text}")
                        raise Exception(f"retry failed: {err_text}")
                        # return None

                    # 给delay加上25%的随机数，避免多个请求同时重试
                    r_delay = delay + delay * backoff * (1 - 2 * random.random())
                    r_delay = max(0, r_delay)

                    logger.error(
                        f"{str(e)}, retrying after {r_delay:.2f} seconds, {attempts} retries left"
                    )

                    time.sleep(r_delay)

        return wrapper

    return decorator


def safe(error_return_value=None):
    """
    安全执行装饰器，确保函数在出错时能够安全返回默认值或错误信息

    Args:
        error_return_value: 出错时返回的指定值。
            - None: 返回 None（默认）
            - "error_log": 返回错误信息字符串
            - 其他值: 返回指定的值

    Examples:
        @safe(error_return_value="默认值")
        def risky_function():
            return 1 / 0  # 会返回 "默认值"

        @safe(error_return_value="error_log")
        def another_risky_function():
            return 1 / 0  # 会返回错误信息字符串

        @safe()
        def safe_function():
            return 1 / 0  # 会返回 None
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if error_return_value == "error_log":
                    res = str(e)
                else:
                    res = error_return_value
                
                error_msg = f"函数 {func.__name__} 执行出错: {type(e).__name__}: {e}, 返回值: {res}"
                logger.error(error_msg)

                return res

        return wrapper

    return decorator


def timeout(seconds):
    """
    超时装饰器，为函数添加超时限制，超时则抛出 TimeoutError
    
    Args:
        seconds (float): 超时时间（秒），必须大于0
        
    Returns:
        function: 装饰器函数
        
    Raises:
        TimeoutError: 当函数执行时间超过指定时间时抛出
        
    Features:
        - 跨平台支持：使用 threading 模块实现，适用于 Windows 和 Unix 系统
        - 自动清理：超时后自动清理线程资源
        - 详细日志：记录超时信息
        
    Examples:
        @timeout(5)
        def slow_function():
            time.sleep(10)  # 超过5秒会抛出 TimeoutError
            return "完成"
            
        @timeout(2.5)
        def api_call():
            # API调用，2.5秒超时
            return requests.get("http://example.com")
            
        try:
            result = slow_function()
        except TimeoutError as e:
            print(f"函数执行超时: {e}")
    """
    
    if seconds <= 0:
        raise ValueError("超时时间必须大于0")
    
    def decorator(func):
        """
        内部装饰器函数
        
        Args:
            func: 要装饰的函数
            
        Returns:
            function: 包装后的函数
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            """
            包装器函数，实现超时逻辑
            
            Args:
                *args: 位置参数
                **kwargs: 关键字参数
                
            Returns:
                原函数的返回值
                
            Raises:
                TimeoutError: 当函数执行时间超过指定时间时抛出
            """
            result = None
            exception = None
            
            def target():
                """在单独线程中执行的目标函数"""
                nonlocal result, exception
                try:
                    result = func(*args, **kwargs)
                except Exception as e:
                    exception = e
            
            # 创建并启动线程
            thread = threading.Thread(target=target)
            thread.daemon = True  # 设置为守护线程
            thread.start()
            thread.join(timeout=seconds)  # 等待线程完成或超时
            
            # 检查是否超时
            if thread.is_alive():
                error_msg = f"函数 {func.__name__} 执行超时（超过 {seconds} 秒）"
                logger.error(error_msg)
                raise TimeoutError(error_msg)
            
            # 如果函数抛出了异常，重新抛出
            if exception is not None:
                raise exception
            
            # 返回函数结果
            return result
        
        return wrapper
    
    return decorator
