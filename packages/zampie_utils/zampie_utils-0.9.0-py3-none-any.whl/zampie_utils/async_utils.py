from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.progress import (
    Progress,
    TextColumn,
    BarColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from tqdm import tqdm

from .logger import logger


def submit_task(func, item, unpack_args=False, unpack_kwargs=False):
    """根据item的类型决定如何调用函数
    
    Args:
        func: 要执行的函数
        item: 输入项
        unpack_args: 控制元组/列表的传递方式。
            - True: 解包为位置参数传递
            - False: 整体作为单个位置参数传递（默认）
        unpack_kwargs: 控制字典的传递方式。
            - True: 解包为关键字参数传递
            - False: 整体作为单个位置参数传递（默认）
    """
    if isinstance(item, dict):
        # 检查是否是混合格式 {'args': (...), 'kwargs': {...}}
        if "args" in item and "kwargs" in item:
            return func(*item["args"], **item["kwargs"])
        elif "args" in item:
            return func(*item["args"])
        elif "kwargs" in item:
            return func(**item["kwargs"])
        else:
            # 纯字典
            if unpack_kwargs:
                # 作为关键字参数传递
                return func(**item)
            else:
                # 将字典整体作为单个位置参数传递
                return func(item)
    elif isinstance(item, (tuple, list)) and not isinstance(item, str):
        # 元组或列表
        if unpack_args:
            # 作为位置参数传递
            return func(*item)
        else:
            # 将元组或列表整体作为单个位置参数传递
            return func(item)
    else:
        # 单个值
        return func(item)


def sequential_map(
    func, items, description=None, log_level="none", progress_type="rich", unpack_args=False, unpack_kwargs=False, raise_on_error=False, error_return_value=None
):
    """
    顺序执行函数，用于单线程场景（如调试）

    Args:
        func: 要执行的函数
        items: 输入数据列表
        description: 进度条描述，默认为函数名
        log_level: 日志级别
        progress_type: 进度条类型，可选值：
            - "rich": 使用 rich 进度条（默认）
            - "tqdm": 使用 tqdm 进度条
            - "none": 无进度条
        unpack_args: 控制元组/列表的传递方式。
            - True: 解包为位置参数传递
            - False: 整体作为单个位置参数传递（默认）
        unpack_kwargs: 控制字典的传递方式。
            - True: 解包为关键字参数传递
            - False: 整体作为单个位置参数传递（默认）
        raise_on_error: 控制错误处理方式。
            - True: 遇到错误时立即抛出异常
            - False: 将异常对象添加到结果列表中（默认）
        error_return_value: 当 raise_on_error=False 时，出错时返回的指定值。
            - None: 返回 None（默认）
            - "error_log": 返回错误信息字符串
            - 其他值: 返回指定的值

    Returns:
        按输入顺序排列的结果列表

    Raises:
        Exception: 当 raise_on_error=True 且函数执行出错时抛出异常
    """
    results = []

    # 检查是否支持len，如果不支持则转换为列表
    if not hasattr(items, "__len__"):
        logger.info("Converting iterator to list for map processing...")
        items = list(items)

    total = len(items)

    # 使用函数名
    if description is None:
        func_name = getattr(func, "__name__", "task")
        description = f"<{func_name}>"

    if progress_type == "rich":
        # 使用 rich 进度条，显示数量和进度
        with Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
        ) as progress:
            total_task = progress.add_task(f"[green]{description}[/green]", total=total)
            for i, item in enumerate(items):
                try:
                    result = submit_task(func, item, unpack_args, unpack_kwargs)
                    logger.log(log_level, f"index: {i}, result: {result}")
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error in sequential_map: {e}")
                    if raise_on_error:
                        raise
                    if error_return_value == "error_log":
                        results.append(str(e))
                    else:
                        results.append(error_return_value)
                progress.update(total_task, advance=1)

    elif progress_type == "tqdm":
        # 使用 tqdm 进度条
        with tqdm(total=total, desc=description, unit="item") as pbar:
            for i, item in enumerate(items):
                try:
                    result = submit_task(func, item, unpack_args, unpack_kwargs)
                    logger.log(log_level, f"index: {i}, result: {result}")
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error in sequential_map: {e}")
                    if raise_on_error:
                        raise
                    if error_return_value == "error_log":
                        results.append(str(e))
                    else:
                        results.append(error_return_value)
                pbar.update(1)

    else:  # progress_type == "none"
        # 无进度条
        for i, item in enumerate(items):
            try:
                result = submit_task(func, item, unpack_args, unpack_kwargs)
                logger.log(log_level, f"index: {i}, result: {result}")
                results.append(result)
            except Exception as e:
                logger.error(f"Error in sequential_map: {e}")
                if raise_on_error:
                    raise
                if error_return_value == "error_log":
                    results.append(str(e))
                else:
                    results.append(error_return_value)

    return results


def parallel_map(
    func, items, description=None, log_level="none", max_workers=5, progress_type="rich", unpack_args=False, unpack_kwargs=False, raise_on_error=False, error_return_value=None
):
    """
    并行执行函数，保证输出顺序与输入顺序一致

    Args:
        func: 要执行的函数
        items: 输入数据列表，支持以下格式：
            - 单个值的列表: [1, 2, 3]
            - 元组列表（位置参数）: [(1, 2), (3, 4), (5, 6)]
            - 字典列表（关键字参数）: [{'a': 1, 'b': 2}, {'a': 3, 'b': 4}]
            - 混合格式：[{'args': (...), 'kwargs': {...}}, ...]
        description: 进度条描述，默认为函数名
        log_level: 日志级别
        max_workers: 最大工作线程数，默认为 5
        progress_type: 进度条类型，可选值：
            - "rich": 使用 rich 进度条（默认）
            - "tqdm": 使用 tqdm 进度条
            - "none": 无进度条
        unpack_args: 控制元组/列表的传递方式。
            - True: 解包为位置参数传递
            - False: 整体作为单个位置参数传递（默认）
        unpack_kwargs: 控制字典的传递方式。
            - True: 解包为关键字参数传递
            - False: 整体作为单个位置参数传递（默认）
        raise_on_error: 控制错误处理方式。
            - True: 遇到错误时立即抛出异常
            - False: 将异常对象添加到结果列表中（默认）
        error_return_value: 当 raise_on_error=False 时，出错时返回的指定值。
            - None: 返回 None（默认）
            - "error_log": 返回错误信息字符串
            - 其他值: 返回指定的值

    Returns:
        按输入顺序排列的结果列表

    Raises:
        Exception: 当 raise_on_error=True 且函数执行出错时抛出异常

    Examples:
        # 单个参数
        parallel_map(lambda x: x * 2, [1, 2, 3])

        # 多个位置参数
        parallel_map(lambda x, y: x + y, [(1, 2), (3, 4), (5, 6)])

        # 关键字参数
        parallel_map(lambda a, b: a + b, [{'a': 1, 'b': 2}, {'a': 3, 'b': 4}])

        # 字典作为单个位置参数（适用于形参是一个dict的函数）
        parallel_map(lambda d: (d['a'] + d['b']), [{'a': 1, 'b': 2}, {'a': 3, 'b': 4}], unpack_kwargs=False)

        # 混合参数
        parallel_map(lambda x, y, z=0: x + y + z,
                    [{'args': (1, 2), 'kwargs': {'z': 3}},
                     {'args': (4, 5), 'kwargs': {'z': 6}}])

    Problem:
        Process上下文中会导致icecream不可用,因为
        # icecream的ic()函数默认将输出写入stderr（标准错误流），而不是stdout（标准输出流）。这会导致：
        # 输出缓冲问题: stderr和stdout有不同的缓冲策略
        # 输出顺序混乱: 当使用map等函数时，多个ic()调用的输出可能交错
        需要手动配置输出函数为print
        ic.configureOutput(outputFunction=print)

    """
    # 如果只有一个worker或更少，使用顺序执行，避免线程开销
    if max_workers <= 1:
        return sequential_map(func, items, description, log_level, progress_type, unpack_args, unpack_kwargs, raise_on_error, error_return_value)

    # 检查是否支持len，如果不支持则转换为列表
    if not hasattr(items, "__len__"):
        logger.info("Converting iterator to list for map processing...")
        items = list(items)

    # 使用函数名
    if description is None:
        func_name = getattr(func, "__name__", "task")
        description = f"<{func_name}>"

    results = [None] * len(items)
    
    # 创建包装函数来传递 unpack_kwargs 参数
    def submit_task_wrapper(func, item):
        return submit_task(func, item, unpack_args, unpack_kwargs)

    if progress_type == "rich":
        # 使用 rich 进度条，显示数量和进度
        with Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
        ) as progress:
            total_task = progress.add_task(
                f"[green]{description}[/green]", total=len(items)
            )

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交所有任务，并保存任务和索引的映射
                future_to_index = {
                    executor.submit(submit_task_wrapper, func, item): i
                    for i, item in enumerate(items)
                }

                # 按完成顺序获取结果，但保存到正确的位置
                for future in as_completed(future_to_index):
                    index = future_to_index[future]
                    try:
                        logger.log(
                            log_level, f"index: {index}, result: {future.result()}"
                        )
                        results[index] = future.result()
                    except Exception as e:
                        logger.error(f"Error in parallel_map: {e}")
                        if raise_on_error:
                            raise
                        if error_return_value == "error_log":
                            results[index] = str(e)
                        else:
                            results[index] = error_return_value
                    progress.update(total_task, advance=1)

    elif progress_type == "tqdm":
        # 使用 tqdm 进度条
        if tqdm is None:
            logger.warning("tqdm not available, falling back to no progress bar")
            progress_type = "none"
        else:
            with tqdm(total=len(items), desc=description, unit="item") as pbar:
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    # 提交所有任务，并保存任务和索引的映射
                    future_to_index = {
                        executor.submit(submit_task_wrapper, func, item): i
                        for i, item in enumerate(items)
                    }

                    # 按完成顺序获取结果，但保存到正确的位置
                    for future in as_completed(future_to_index):
                        index = future_to_index[future]
                        try:
                            logger.log(
                                log_level, f"index: {index}, result: {future.result()}"
                            )
                            results[index] = future.result()
                        except Exception as e:
                            logger.error(f"Error in parallel_map: {e}")
                            if raise_on_error:
                                raise
                            if error_return_value == "error_log":
                                results[index] = str(e)
                            else:
                                results[index] = error_return_value
                        pbar.update(1)

    else:  # progress_type == "none"
        # 无进度条
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务，并保存任务和索引的映射
            future_to_index = {
                executor.submit(submit_task_wrapper, func, item): i
                for i, item in enumerate(items)
            }

            # 按完成顺序获取结果，但保存到正确的位置
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    logger.log(log_level, f"index: {index}, result: {future.result()}")
                    results[index] = future.result()
                except Exception as e:
                    logger.error(f"Error in parallel_map: {e}")
                    if raise_on_error:
                        raise
                    if error_return_value == "error_log":
                        results[index] = str(e)
                    else:
                        results[index] = error_return_value

    return results


def auto_map(
    func, items, description=None, log_level="none", max_workers=1, progress_type="rich", unpack_args=False, unpack_kwargs=False, raise_on_error=False, error_return_value=None
):
    """
    智能映射函数，根据max_workers自动选择执行方式

    Args:
        func: 要执行的函数
        items: 输入数据列表
        description: 进度条描述，默认为函数名
        log_level: 日志级别
        max_workers: 最大工作线程数，默认为 1（顺序执行）
        progress_type: 进度条类型，可选值：
            - "rich": 使用 rich 进度条（默认）
            - "tqdm": 使用 tqdm 进度条
            - "none": 无进度条
        unpack_args: 控制元组/列表的传递方式。
            - True: 解包为位置参数传递
            - False: 整体作为单个位置参数传递（默认）
        unpack_kwargs: 控制字典的传递方式。
            - True: 解包为关键字参数传递
            - False: 整体作为单个位置参数传递（默认）
        raise_on_error: 控制错误处理方式。
            - True: 遇到错误时立即抛出异常
            - False: 将异常对象添加到结果列表中（默认）
        error_return_value: 当 raise_on_error=False 时，出错时返回的指定值。
            - None: 返回 None（默认）
            - "error_log": 返回错误信息字符串
            - 其他值: 返回指定的值

    Returns:
        按输入顺序排列的结果列表

    Raises:
        Exception: 当 raise_on_error=True 且函数执行出错时抛出异常
    """
    return parallel_map(func, items, description, log_level, max_workers, progress_type, unpack_args, unpack_kwargs, raise_on_error, error_return_value)


def parallel_execute(tasks, max_workers=None, raise_on_error=False, error_return_value=None):
    """
    同时执行多个函数，并返回每个函数的返回值
    
    Args:
        tasks: 任务列表，每个任务可以是以下格式之一：
            - 函数对象（无参数函数）：直接传入函数
            - (函数, args) 元组：args 可以是元组/列表（位置参数）
            - (函数, args, kwargs) 元组：args 是元组/列表，kwargs 是字典
            - {'func': 函数, 'args': 元组/列表, 'kwargs': 字典} 字典格式
            - {'func': 函数, 'args': 元组/列表} 字典格式（仅位置参数）
            - {'func': 函数, 'kwargs': 字典} 字典格式（仅关键字参数）
        max_workers: 最大工作线程数，默认为任务数量
        raise_on_error: 控制错误处理方式。
            - True: 遇到错误时立即抛出异常
            - False: 将错误信息添加到结果列表中（默认）
        error_return_value: 当 raise_on_error=False 时，出错时返回的指定值。
            - None: 返回 None（默认）
            - "error_log": 返回错误信息字符串
            - 其他值: 返回指定的值
    
    Returns:
        按输入顺序排列的结果列表，每个元素对应一个任务的返回值
    
    Raises:
        Exception: 当 raise_on_error=True 且函数执行出错时抛出异常
    
    Examples:
        # 无参数函数
        def func1():
            return 1
        def func2():
            return 2
        
        results = parallel_execute([func1, func2])
        # 返回: [1, 2]
        
        # 带位置参数
        def add(a, b):
            return a + b
        
        results = parallel_execute([
            (add, (1, 2)),
            (add, (3, 4)),
        ])
        # 返回: [3, 7]
        
        # 带关键字参数
        def greet(name, age=0):
            return f"{name} is {age} years old"
        
        results = parallel_execute([
            (greet, (), {'name': 'Alice', 'age': 25}),
            (greet, (), {'name': 'Bob'}),
        ])
        # 返回: ['Alice is 25 years old', 'Bob is 0 years old']
        
        # 混合参数
        def calculate(x, y, operation='add'):
            if operation == 'add':
                return x + y
            return x - y
        
        results = parallel_execute([
            {'func': calculate, 'args': (1, 2), 'kwargs': {'operation': 'add'}},
            {'func': calculate, 'args': (5, 3), 'kwargs': {'operation': 'subtract'}},
        ])
        # 返回: [3, 2]
    """
    if not tasks:
        return []
    
    # 默认工作线程数为任务数量
    if max_workers is None:
        max_workers = len(tasks)
    
    # 解析任务并创建执行函数
    def parse_and_execute(task, index):
        """解析任务并执行"""
        try:
            # 如果是函数对象（可调用且不是元组/列表/字典）
            if callable(task) and not isinstance(task, (tuple, list, dict)):
                return task()
            
            # 如果是元组
            elif isinstance(task, (tuple, list)):
                if len(task) == 0:
                    raise ValueError("任务元组不能为空")
                func = task[0]
                args = task[1] if len(task) > 1 else ()
                kwargs = task[2] if len(task) > 2 else {}
                
                if not isinstance(args, (tuple, list)):
                    args = (args,)
                if not isinstance(kwargs, dict):
                    kwargs = {}
                
                return func(*args, **kwargs)
            
            # 如果是字典
            elif isinstance(task, dict):
                if 'func' not in task:
                    raise ValueError("任务字典必须包含 'func' 键")
                
                func = task['func']
                args = task.get('args', ())
                kwargs = task.get('kwargs', {})
                
                if not isinstance(args, (tuple, list)):
                    args = (args,) if args is not None else ()
                if not isinstance(kwargs, dict):
                    kwargs = {}
                
                return func(*args, **kwargs)
            
            else:
                raise ValueError(f"不支持的任务格式: {type(task)}")
        
        except Exception as e:
            logger.error(f"Error executing task {index}: {e}")
            if raise_on_error:
                raise
            if error_return_value == "error_log":
                return str(e)
            return error_return_value
    
    # 执行任务
    results = [None] * len(tasks)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务，并保存任务和索引的映射
        future_to_index = {
            executor.submit(parse_and_execute, task, i): i
            for i, task in enumerate(tasks)
        }
        
        # 按完成顺序获取结果，但保存到正确的位置
        for future in as_completed(future_to_index):
            index = future_to_index[future]
            try:
                results[index] = future.result()
            except Exception as e:
                logger.error(f"Error getting result for task {index}: {e}")
                if raise_on_error:
                    raise
                if error_return_value == "error_log":
                    results[index] = str(e)
                else:
                    results[index] = error_return_value
    
    return results