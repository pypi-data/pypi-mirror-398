from pathlib import Path
from typing import Union, List, Optional, Dict, Any

import numpy as np
import pandas as pd

from .logger import logger
from .utils import makedirs


def read_df(file_path: Union[str, Path], **kwargs) -> pd.DataFrame:
    """
    根据文件后缀名自动使用pandas读取文件为DataFrame
    
    支持的文件格式：
    - CSV: .csv, .tsv, .txt
    - Excel: .xlsx, .xls, .xlsm, .xlsb
    - JSON: .json, .jsonl
    - Parquet: .parquet
    - Pickle: .pkl, .pickle
    - HTML: .html, .htm
    - XML: .xml
    - Feather: .feather
    - HDF5: .h5, .hdf5
    
    Args:
        file_path: 文件路径
        **kwargs: 传递给对应pandas读取函数的额外参数
        
    Returns:
        pd.DataFrame: 读取的DataFrame
        
    Raises:
        ValueError: 不支持的文件格式
        FileNotFoundError: 文件不存在
        
    Examples:
        >>> df = read_df('data.csv')
        >>> df = read_df('data.xlsx', sheet_name=0)
        >>> df = read_df('data.json', orient='records')
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    suffix = file_path.suffix.lower()
    
    # CSV格式
    if suffix in ['.csv']:
        kwargs.setdefault('encoding', 'utf-8')
        return pd.read_csv(file_path, **kwargs)
    
    # TSV格式（制表符分隔）
    if suffix in ['.tsv']:
        kwargs.setdefault('sep', '\t')
        kwargs.setdefault('encoding', 'utf-8')
        return pd.read_csv(file_path, **kwargs)
    
    # TXT格式（尝试作为CSV读取）
    if suffix in ['.txt']:
        kwargs.setdefault('encoding', 'utf-8')
        return pd.read_csv(file_path, **kwargs)
    
    # Excel格式
    if suffix in ['.xlsx', '.xls', '.xlsm', '.xlsb']:
        return pd.read_excel(file_path, **kwargs)
    
    # JSON格式
    if suffix in ['.json']:
        kwargs.setdefault('encoding', 'utf-8')
        return pd.read_json(file_path, **kwargs)
    
    # JSONL格式（每行一个JSON对象）
    if suffix in ['.jsonl']:
        kwargs.setdefault('lines', True)
        kwargs.setdefault('encoding', 'utf-8')
        return pd.read_json(file_path, **kwargs)
    
    # Parquet格式
    if suffix in ['.parquet']:
        return pd.read_parquet(file_path, **kwargs)
    
    # Pickle格式
    if suffix in ['.pkl', '.pickle']:
        return pd.read_pickle(file_path, **kwargs)
    
    # HTML格式（返回第一个表格）
    if suffix in ['.html', '.htm']:
        kwargs.setdefault('encoding', 'utf-8')
        dfs = pd.read_html(file_path, **kwargs)
        if dfs:
            logger.info(f"HTML文件包含 {len(dfs)} 个表格，返回第一个表格")
            return dfs[0]
        else:
            raise ValueError(f"HTML文件中未找到表格: {file_path}")
    
    # XML格式
    if suffix in ['.xml']:
        kwargs.setdefault('encoding', 'utf-8')
        return pd.read_xml(file_path, **kwargs)
    
    # Feather格式
    if suffix in ['.feather']:
        return pd.read_feather(file_path, **kwargs)
    
    # HDF5格式
    if suffix in ['.h5', '.hdf5']:
        if 'key' not in kwargs:
            raise ValueError("读取HDF5文件需要指定'key'参数，例如: read_df('data.h5', key='df')")
        return pd.read_hdf(file_path, **kwargs)
    
    # 不支持的文件格式
    raise ValueError(
        f"不支持的文件格式: {suffix}\n"
        f"支持格式: .csv, .tsv, .txt, .xlsx, .xls, .xlsm, .xlsb, "
        f".json, .jsonl, .parquet, .pkl, .pickle, .html, .htm, "
        f".xml, .feather, .h5, .hdf5"
    )


def save_df(df: pd.DataFrame, save_path: Union[str, Path], **kwargs) -> None:
    """
    根据文件后缀名自动使用pandas保存DataFrame到文件
    
    支持的文件格式：
    - CSV: .csv, .tsv, .txt
    - Excel: .xlsx, .xls, .xlsm, .xlsb
    - JSON: .json, .jsonl
    - Parquet: .parquet
    - Pickle: .pkl, .pickle
    - HTML: .html, .htm
    - XML: .xml
    - Feather: .feather
    - HDF5: .h5, .hdf5
    
    Args:
        df: 要保存的DataFrame
        save_path: 保存路径
        **kwargs: 传递给对应pandas保存函数的额外参数
        
    Raises:
        ValueError: 不支持的文件格式
        
    Examples:
        >>> save_df(df, 'data.csv')
        >>> save_df(df, 'data.xlsx', sheet_name='Sheet1')
        >>> save_df(df, 'data.json', orient='records')
        >>> save_df(df, 'data.jsonl')
    """
    save_path = Path(save_path)
    
    # 确保目录存在
    if save_path.parent:
        makedirs(save_path.parent)
    
    # 获取绝对路径用于日志
    abs_path = save_path.resolve()
    suffix = save_path.suffix.lower()
    rows, cols = df.shape
    
    # CSV格式
    if suffix in ['.csv']:
        kwargs.setdefault('encoding', 'utf-8')
        df.to_csv(save_path, **kwargs)
        logger.info(f"成功保存DataFrame (形状: {rows}行 × {cols}列) 到CSV文件: {abs_path}")
        return
    
    # TSV格式（制表符分隔）
    if suffix in ['.tsv']:
        kwargs.setdefault('sep', '\t')
        kwargs.setdefault('encoding', 'utf-8')
        df.to_csv(save_path, **kwargs)
        logger.info(f"成功保存DataFrame (形状: {rows}行 × {cols}列) 到TSV文件: {abs_path}")
        return
    
    # TXT格式（作为CSV保存）
    if suffix in ['.txt']:
        kwargs.setdefault('encoding', 'utf-8')
        df.to_csv(save_path, **kwargs)
        logger.info(f"成功保存DataFrame (形状: {rows}行 × {cols}列) 到TXT文件: {abs_path}")
        return
    
    # Excel格式
    if suffix in ['.xlsx', '.xls', '.xlsm', '.xlsb']:
        df.to_excel(save_path, **kwargs)
        logger.info(f"成功保存DataFrame (形状: {rows}行 × {cols}列) 到Excel文件: {abs_path}")
        return
    
    # JSON格式
    if suffix in ['.json']:
        kwargs.setdefault('encoding', 'utf-8')
        df.to_json(save_path, **kwargs)
        logger.info(f"成功保存DataFrame (形状: {rows}行 × {cols}列) 到JSON文件: {abs_path}")
        return
    
    # JSONL格式（每行一个JSON对象）
    if suffix in ['.jsonl']:
        kwargs.setdefault('lines', True)
        kwargs.setdefault('orient', 'records')
        kwargs.setdefault('encoding', 'utf-8')
        df.to_json(save_path, **kwargs)
        logger.info(f"成功保存DataFrame (形状: {rows}行 × {cols}列) 到JSONL文件: {abs_path}")
        return
    
    # Parquet格式
    if suffix in ['.parquet']:
        df.to_parquet(save_path, **kwargs)
        logger.info(f"成功保存DataFrame (形状: {rows}行 × {cols}列) 到Parquet文件: {abs_path}")
        return
    
    # Pickle格式
    if suffix in ['.pkl', '.pickle']:
        df.to_pickle(save_path, **kwargs)
        logger.info(f"成功保存DataFrame (形状: {rows}行 × {cols}列) 到Pickle文件: {abs_path}")
        return
    
    # HTML格式
    if suffix in ['.html', '.htm']:
        kwargs.setdefault('encoding', 'utf-8')
        df.to_html(save_path, **kwargs)
        logger.info(f"成功保存DataFrame (形状: {rows}行 × {cols}列) 到HTML文件: {abs_path}")
        return
    
    # XML格式
    if suffix in ['.xml']:
        kwargs.setdefault('encoding', 'utf-8')
        df.to_xml(save_path, **kwargs)
        logger.info(f"成功保存DataFrame (形状: {rows}行 × {cols}列) 到XML文件: {abs_path}")
        return
    
    # Feather格式
    if suffix in ['.feather']:
        df.to_feather(save_path, **kwargs)
        logger.info(f"成功保存DataFrame (形状: {rows}行 × {cols}列) 到Feather文件: {abs_path}")
        return
    
    # HDF5格式
    if suffix in ['.h5', '.hdf5']:
        if 'key' not in kwargs:
            raise ValueError("保存HDF5文件需要指定'key'参数，例如: save_df(df, 'data.h5', key='df')")
        df.to_hdf(save_path, **kwargs)
        logger.info(f"成功保存DataFrame (形状: {rows}行 × {cols}列, key: {kwargs.get('key')}) 到HDF5文件: {abs_path}")
        return
    
    # 不支持的文件格式
    raise ValueError(
        f"不支持的文件格式: {suffix}\n"
        f"支持格式: .csv, .tsv, .txt, .xlsx, .xls, .xlsm, .xlsb, "
        f".json, .jsonl, .parquet, .pkl, .pickle, .html, .htm, "
        f".xml, .feather, .h5, .hdf5"
    )


def read_df_multi(
    file_paths: Union[List[Union[str, Path]], Union[str, Path]],
    read_kwargs: Optional[Dict[str, Any]] = None,
    concat_kwargs: Optional[Dict[str, Any]] = None,
    **kwargs
) -> pd.DataFrame:
    """
    读取多个文件并合并为一个DataFrame
    
    支持读取多个相同或不同格式的文件，并使用pandas.concat进行合并。
    所有文件必须具有相同的列结构（或使用join参数处理列不一致的情况）。
    
    Args:
        file_paths: 文件路径列表或单个文件路径（字符串或Path对象）
        read_kwargs: 传递给read_df函数的参数字典（用于所有文件）
        concat_kwargs: 传递给pd.concat函数的参数字典
        **kwargs: 额外的参数，会合并到read_kwargs中（如果read_kwargs为None则创建新字典）
        
    Returns:
        pd.DataFrame: 合并后的DataFrame
        
    Raises:
        ValueError: 文件路径列表为空
        FileNotFoundError: 文件不存在
        
    Examples:
        >>> # 读取多个CSV文件并合并
        >>> df = read_df_multi(['file1.csv', 'file2.csv', 'file3.csv'])
        
        >>> # 读取多个文件，指定读取参数
        >>> df = read_df_multi(
        ...     ['data1.xlsx', 'data2.xlsx'],
        ...     read_kwargs={'sheet_name': 0}
        ... )
        
        >>> # 读取多个文件，指定合并参数
        >>> df = read_df_multi(
        ...     ['file1.csv', 'file2.csv'],
        ...     concat_kwargs={'ignore_index': True, 'sort': False}
        ... )
        
        >>> # 使用kwargs快捷方式
        >>> df = read_df_multi(
        ...     ['file1.json', 'file2.json'],
        ...     encoding='utf-8',
        ...     concat_kwargs={'ignore_index': True}
        ... )
        
        >>> # 处理列不一致的情况
        >>> df = read_df_multi(
        ...     ['file1.csv', 'file2.csv'],
        ...     concat_kwargs={'join': 'outer'}  # 使用外连接保留所有列
        ... )
    """
    # 处理文件路径参数
    if isinstance(file_paths, (str, Path)):
        file_paths = [file_paths]
    
    if not file_paths:
        raise ValueError("文件路径列表不能为空")
    
    # 合并read_kwargs和kwargs
    if read_kwargs is None:
        read_kwargs = {}
    if kwargs:
        read_kwargs = {**read_kwargs, **kwargs}
    
    # 设置默认的concat_kwargs
    if concat_kwargs is None:
        concat_kwargs = {}
    concat_kwargs.setdefault('ignore_index', True)  # 默认忽略索引，重新生成
    
    # 读取所有文件
    dfs = []
    for file_path in file_paths:
        file_path = Path(file_path)
        logger.info(f"正在读取文件: {file_path}")
        df = read_df(file_path, **read_kwargs)
        dfs.append(df)
        logger.info(f"成功读取文件: {file_path} (形状: {df.shape[0]}行 × {df.shape[1]}列)")
    
    # 合并DataFrame
    if not dfs:
        raise ValueError("没有成功读取任何文件")
    
    logger.info(f"正在合并 {len(dfs)} 个DataFrame...")
    result_df = pd.concat(dfs, **concat_kwargs)
    logger.info(f"成功合并为DataFrame (形状: {result_df.shape[0]}行 × {result_df.shape[1]}列)")
    
    return result_df


def save_df_split(
    df: pd.DataFrame,
    n_parts: int,
    save_path_template: Union[str, Path],
    save_kwargs: Optional[Dict[str, Any]] = None,
    **kwargs
) -> List[Path]:
    """
    将DataFrame切分为指定份数并保存为多个文件
    
    将DataFrame按行切分为n_parts份，每份保存为单独的文件。
    文件名会在模板路径中自动插入序号，例如 'data.csv' 会生成 'data_1.csv', 'data_2.csv' 等。
    
    Args:
        df: 要切分的DataFrame
        n_parts: 切分的份数（必须大于0且小于等于DataFrame行数）
        save_path_template: 保存路径模板，用于生成多个文件的保存路径。
            函数会在文件名（不含扩展名）和扩展名之间插入序号。
            支持以下格式：
            - 简单文件名: 'data.csv' -> 生成 'data_1.csv', 'data_2.csv', ...
            - 相对路径: 'output/data.csv' -> 生成 'output/data_1.csv', 'output/data_2.csv', ...
            - 绝对路径: '/path/to/results.xlsx' -> 生成 '/path/to/results_1.xlsx', ...
            - 带目录的路径: 'results/data.json' -> 生成 'results/data_1.json', ...
            
            文件名生成规则：
            - 提取路径的文件名部分（不含扩展名）作为基础名称
            - 提取扩展名确定文件格式
            - 在基础名称和扩展名之间插入序号：{基础名称}_{序号}{扩展名}
            
            示例转换：
            - 'data.csv' -> 'data_1.csv', 'data_2.csv', 'data_3.csv'
            - 'output.xlsx' -> 'output_1.xlsx', 'output_2.xlsx', 'output_3.xlsx'
            - 'folder/results.json' -> 'folder/results_1.json', 'folder/results_2.json', ...
            - '/absolute/path/file.parquet' -> '/absolute/path/file_1.parquet', ...
        save_kwargs: 传递给save_df函数的参数字典（用于所有文件）
        **kwargs: 额外的参数，会合并到save_kwargs中（如果save_kwargs为None则创建新字典）
        
    Returns:
        List[Path]: 保存的文件路径列表，按切分顺序排列
        
    Raises:
        ValueError: 份数小于等于0，或份数大于DataFrame行数
        
    Examples:
        >>> # 示例1: 基本用法 - 简单文件名
        >>> paths = save_df_split(df, 3, 'data.csv')
        >>> # 生成文件: data_1.csv, data_2.csv, data_3.csv
        >>> # 返回: [Path('data_1.csv'), Path('data_2.csv'), Path('data_3.csv')]
        
        >>> # 示例2: 保存为Excel格式
        >>> paths = save_df_split(df, 5, 'output.xlsx')
        >>> # 生成文件: output_1.xlsx, output_2.xlsx, output_3.xlsx, output_4.xlsx, output_5.xlsx
        
        >>> # 示例3: 保存到指定目录
        >>> paths = save_df_split(df, 4, 'results/data.json')
        >>> # 生成文件: results/data_1.json, results/data_2.json, results/data_3.json, results/data_4.json
        >>> # 注意: 如果results目录不存在，会自动创建
        
        >>> # 示例4: 使用绝对路径
        >>> paths = save_df_split(df, 3, '/home/user/output/data.parquet')
        >>> # 生成文件: /home/user/output/data_1.parquet, /home/user/output/data_2.parquet, ...
        
        >>> # 示例5: 指定保存参数（不保存索引）
        >>> paths = save_df_split(
        ...     df, 3, 'data.csv',
        ...     save_kwargs={'index': False}
        ... )
        
        >>> # 示例6: 使用kwargs快捷方式传递保存参数
        >>> paths = save_df_split(
        ...     df, 4, 'data.json',
        ...     orient='records'  # 直接传递给save_df
        ... )
        
        >>> # 示例7: 保存为JSONL格式
        >>> paths = save_df_split(df, 2, 'output.jsonl')
        >>> # 生成文件: output_1.jsonl, output_2.jsonl
        
        >>> # 示例8: 保存为Parquet格式（带压缩）
        >>> paths = save_df_split(
        ...     df, 3, 'data.parquet',
        ...     save_kwargs={'compression': 'gzip'}
        ... )
    """
    if n_parts <= 0:
        raise ValueError(f"份数必须大于0，当前值: {n_parts}")
    
    if n_parts > len(df):
        raise ValueError(
            f"份数({n_parts})不能大于DataFrame行数({len(df)})，"
            f"请将份数调整为小于等于{len(df)}的值"
        )
    
    # 合并save_kwargs和kwargs
    if save_kwargs is None:
        save_kwargs = {}
    if kwargs:
        save_kwargs = {**save_kwargs, **kwargs}
    
    # 解析保存路径模板
    save_path_template = Path(save_path_template)
    stem = save_path_template.stem  # 文件名（不含扩展名）
    suffix = save_path_template.suffix  # 扩展名
    parent = save_path_template.parent  # 目录
    
    # 切分DataFrame
    logger.info(f"正在将DataFrame (形状: {df.shape[0]}行 × {df.shape[1]}列) 切分为 {n_parts} 份...")
    dfs = np.array_split(df, n_parts)
    
    # 保存每一份
    saved_paths = []
    for i, split_df in enumerate(dfs, start=1):
        # 生成文件名：stem_序号.suffix
        save_path = parent / f"{stem}_{i}{suffix}"
        save_df(split_df, save_path, **save_kwargs)
        saved_paths.append(save_path)
    
    logger.info(f"成功将DataFrame切分为 {n_parts} 份并保存到 {len(saved_paths)} 个文件")
    
    return saved_paths


def merge_df_files(
    file_paths: Union[List[Union[str, Path]], Union[str, Path]],
    output_path: Union[str, Path],
    read_kwargs: Optional[Dict[str, Any]] = None,
    concat_kwargs: Optional[Dict[str, Any]] = None,
    save_kwargs: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Path:
    """
    将多个相同数据格式的文件合并为一个文件
    
    读取多个文件，合并为一个DataFrame，然后保存到指定的输出文件。
    所有输入文件必须具有相同的数据格式（或使用join参数处理列不一致的情况）。
    输出文件格式由output_path的后缀名自动确定。
    
    Args:
        file_paths: 要合并的文件路径列表或单个文件路径（字符串或Path对象）
        output_path: 输出文件路径，文件格式由后缀名确定
        read_kwargs: 传递给read_df函数的参数字典（用于所有输入文件）
        concat_kwargs: 传递给pd.concat函数的参数字典，用于控制合并方式
        save_kwargs: 传递给save_df函数的参数字典，用于控制保存方式
        **kwargs: 额外的参数，会合并到read_kwargs中（如果read_kwargs为None则创建新字典）
        
    Returns:
        Path: 保存的输出文件路径
        
    Raises:
        ValueError: 文件路径列表为空，或不支持的文件格式
        FileNotFoundError: 输入文件不存在
        
    Examples:
        >>> # 示例1: 基本用法 - 合并多个CSV文件
        >>> merge_df_files(
        ...     ['file1.csv', 'file2.csv', 'file3.csv'],
        ...     'merged_output.csv'
        ... )
        
        >>> # 示例2: 合并多个Excel文件
        >>> merge_df_files(
        ...     ['data1.xlsx', 'data2.xlsx', 'data3.xlsx'],
        ...     'merged_data.xlsx',
        ...     read_kwargs={'sheet_name': 0}
        ... )
        
        >>> # 示例3: 合并多个JSON文件
        >>> merge_df_files(
        ...     ['file1.json', 'file2.json'],
        ...     'merged.json',
        ...     save_kwargs={'orient': 'records'}
        ... )
        
        >>> # 示例4: 处理列不一致的情况（使用外连接）
        >>> merge_df_files(
        ...     ['file1.csv', 'file2.csv'],
        ...     'merged.csv',
        ...     concat_kwargs={'join': 'outer'}  # 保留所有列
        ... )
        
        >>> # 示例5: 合并时忽略索引并排序
        >>> merge_df_files(
        ...     ['file1.csv', 'file2.csv'],
        ...     'merged.csv',
        ...     concat_kwargs={'ignore_index': True, 'sort': False}
        ... )
        
        >>> # 示例6: 保存时指定参数（不保存索引）
        >>> merge_df_files(
        ...     ['file1.csv', 'file2.csv'],
        ...     'merged.csv',
        ...     save_kwargs={'index': False}
        ... )
        
        >>> # 示例7: 使用kwargs快捷方式传递读取参数
        >>> merge_df_files(
        ...     ['file1.json', 'file2.json'],
        ...     'merged.json',
        ...     encoding='utf-8',
        ...     concat_kwargs={'ignore_index': True}
        ... )
        
        >>> # 示例8: 合并多个Parquet文件
        >>> merge_df_files(
        ...     ['data1.parquet', 'data2.parquet'],
        ...     'merged.parquet',
        ...     save_kwargs={'compression': 'gzip'}
        ... )
        
        >>> # 示例9: 合并多个JSONL文件
        >>> merge_df_files(
        ...     ['file1.jsonl', 'file2.jsonl'],
        ...     'merged.jsonl'
        ... )
    """
    # 处理文件路径参数
    if isinstance(file_paths, (str, Path)):
        file_paths = [file_paths]
    
    if not file_paths:
        raise ValueError("文件路径列表不能为空")
    
    # 合并read_kwargs和kwargs
    if read_kwargs is None:
        read_kwargs = {}
    if kwargs:
        read_kwargs = {**read_kwargs, **kwargs}
    
    # 设置默认的concat_kwargs
    if concat_kwargs is None:
        concat_kwargs = {}
    concat_kwargs.setdefault('ignore_index', True)  # 默认忽略索引，重新生成
    
    # 读取并合并所有文件
    logger.info(f"开始合并 {len(file_paths)} 个文件到: {output_path}")
    merged_df = read_df_multi(
        file_paths=file_paths,
        read_kwargs=read_kwargs,
        concat_kwargs=concat_kwargs
    )
    
    # 保存合并后的DataFrame
    if save_kwargs is None:
        save_kwargs = {}
    save_df(merged_df, output_path, **save_kwargs)
    
    output_path = Path(output_path)
    logger.info(f"成功将 {len(file_paths)} 个文件合并并保存到: {output_path.resolve()}")
    
    return output_path

