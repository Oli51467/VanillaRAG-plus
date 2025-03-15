# -*- coding: utf-8 -*-

import gc
import os
import hashlib
import time
import random
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

import torch
import numpy as np
from tqdm import tqdm
from logging.handlers import RotatingFileHandler


def batch_generator(iterable, batch_size):
    """生成器函数，将可迭代对象分批次返回。"""
    batch = []
    for item in iterable:
        batch.append(item)
        if len(batch) == batch_size:
            yield batch
            batch = []
    if batch:
        yield batch


def calculate_file_hash(file_path):
    """计算文件内容的哈希值（SHA256）。"""
    try:
        with open(file_path, 'rb') as f:
            file_content = f.read()
        file_hash = hashlib.sha256(file_content).hexdigest()
        filename = os.path.basename(file_path)
        doc_name = os.path.basename(os.path.dirname(file_path))
        return filename, doc_name, file_hash
    except Exception as e:
        logging.error(f"计算文件哈希时出错：{file_path}, 错误：{e}")
        return None


def get_current_files(data_dir):
    """获取当前目录中所有的文件及其哈希值，用于与已记录的哈希进行比较"""
    current_files = {}
    futures = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        for root, _, files in os.walk(data_dir):
            if os.path.commonpath([data_dir, root]) != data_dir:
                continue
            doc_name = os.path.basename(os.path.relpath(root, data_dir))
            md_files = [f for f in files if f.endswith('.md')]
            for filename in md_files:
                file_path = os.path.abspath(os.path.join(root, filename))
                futures.append(executor.submit(calculate_file_hash, file_path))

        for future in tqdm(as_completed(futures), total=len(futures), desc="计算文件哈希"):
            result = future.result()
            if result:
                filename, doc_name, file_hash = result
                current_files[filename] = (doc_name, file_hash)

    logging.info(f"当前目录中找到 {len(current_files)} 个文件。")
    return current_files


def delete_removed_files(col, redis_manager, existing_file_hashes, current_files):
    """删除已删除文件对应的 Milvus 记录和 Redis 哈希值。"""
    to_delete = [chunk_file for chunk_file in existing_file_hashes if chunk_file not in current_files]

    if to_delete:
        logging.info(f"将删除 {len(to_delete)} 个文件的记录")
        expr = f'chunk_file in ["' + '","'.join(to_delete) + '"]'
        try:
            col.delete(expr=expr)
            logging.info(f"已删除 {len(to_delete)} 个文件的记录")
            redis_manager.delete_file_hashes(to_delete)
            return len(to_delete)
        except Exception as e:
            logging.error(f"删除文件记录时出错：{e}")
            return 0
    else:
        logging.info("没有找到需要删除的文件记录")
        return 0
    

