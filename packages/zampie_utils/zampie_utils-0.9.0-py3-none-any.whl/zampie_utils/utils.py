import os
import time

import random
from functools import wraps

import natsort

from .logger import logger


def makedirs(path):
    """创建目录，如果目录已存在则不会报错"""
    os.makedirs(path, exist_ok=True)


def walk(path, types=None, max_depth=float("inf")):
    """"""
    depth = 0
    for root, dirs, filenames in os.walk(path):
        if depth >= max_depth:
            break
        depth += 1
        for filename in filenames:
            if types:
                type = filename.split(".")[-1]
                if type in types:
                    yield os.path.join(root, filename)
                    continue
            else:
                yield os.path.join(root, filename)


def walk_dirs(path, max_depth=float("inf")):
    """"""
    depth = 0
    yield path  # 返回根目录
    for root, dirs, filenames in os.walk(path):
        if depth >= max_depth:
            break
        depth += 1
        for dir in dirs:
            yield os.path.join(root, dir)


def probability_trigger(prob=0.5):
    """
    Args:
        prob: float, probability of triggering
    """
    if random.random() < prob:
        logger.info(f"probability_trigger: True, prob: {prob}")
        return True
    logger.info(f"probability_trigger: False, prob: {prob}")
    return False


def sample_lines(lines, num, seed=None):
    if seed is not None:
        random.seed(seed)
    # 创建列表副本以避免修改原始列表
    lines_copy = lines.copy()
    # 对副本进行随机打乱
    random.shuffle(lines_copy)
    return lines_copy[:num]


def sample_files(files, num, seed=None):
    files = natsort.natsorted(files)
    files = sample_lines(files, num, seed)
    files = natsort.natsorted(files)
    return files
