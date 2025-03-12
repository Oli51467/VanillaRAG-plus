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


def determine_file_type(filename):
    """根据文件名确定文件类型。"""
    if "chunk" in filename.lower():
        return "chunk"
    elif "metadata" in filename.lower():
        return "metadata"
    elif "toc" in filename.lower():
        return "toc"
    else:
        return "unknown"


def process_documents(data_dir, collection_name, batch_size, ef, col, redis_manager, max_content_length):
    """文档处理，支持动态调整批次大小和累计进度跟踪。"""
    processed_files_count = 0
    updated_redis_count = 0

    added_docs = 0
    updated_docs = 0
    deleted_docs = 0

    col.load()
    existing_file_hashes = redis_manager.get_existing_file_hashes()
    current_files = get_current_files(data_dir)
    deleted_docs += delete_removed_files(col, redis_manager, existing_file_hashes, current_files)
    col.release()

    all_files = []
    for filename, (doc_name, file_hash) in current_files.items():
        file_path = os.path.join(data_dir, doc_name, filename)
        if not os.path.exists(file_path):
            logging.error(f"文件 {file_path} 不存在，跳过处理。")
            continue
        file_type = determine_file_type(filename)
        all_files.append((filename, doc_name, file_path, file_hash, file_type))

        previous_hash = existing_file_hashes.get(filename)
        if previous_hash is None:
            added_docs += 1
        elif file_hash != previous_hash:
            updated_docs += 1

    files_to_process = [file for file in all_files if file[3] != existing_file_hashes.get(file[0])]
    total_files = len(files_to_process)
    progress_bar = tqdm(
        desc="处理文件进度",
        total=total_files,
        unit="个文件"
    )

    for batch_files in batch_generator(files_to_process, batch_size):
        chunk_files = []
        doc_names = []
        chunk_contents = []
        file_hashes = {}
        file_types = []

        for filename, doc_name, file_path, file_hash, file_type in batch_files:
            chunk_file = filename
            previous_hash = existing_file_hashes.get(chunk_file)

            progress_bar.update(1)

            if previous_hash is not None and file_hash == previous_hash:
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    chunk_content = f.read()
            except FileNotFoundError:
                logging.error(f"文件 {file_path} 不存在，跳过处理。")
                continue
            except Exception as e:
                logging.error(f"读取文件 {file_path} 时出错：{e}")
                continue

            content_length = len(chunk_content)
            if content_length > max_content_length:
                chunk_content = chunk_content[:max_content_length]
                logging.warning(
                    f"文件 {chunk_file} 内容过大（{content_length} 字符），已截取前 {max_content_length} 个字符。"
                )

            chunk_files.append(chunk_file)
            doc_names.append(doc_name)
            file_types.append(file_type)
            chunk_contents.append(chunk_content)
            file_hashes[chunk_file] = file_hash

        if not chunk_files:
            tqdm.write("当前批次无需要处理的文件，跳过。")
            continue

        try:
            with torch.no_grad():
                embeddings = ef(chunk_contents)["dense"]
                embeddings = embeddings.cpu().numpy() if isinstance(embeddings, torch.Tensor) else np.array(embeddings)
                embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
                entities = [
                    {
                        "chunk_file": cf,
                        "doc_name": dn,
                        "file_type": ft,
                        "chunk_content": cc,
                        "dense_vector": dv
                    }
                    for cf, dn, ft, cc, dv in zip(chunk_files, doc_names, file_types, chunk_contents, embeddings.tolist())
                ]
                col.insert(entities)
                try:
                    redis_manager.update_existing_file_hashes(file_hashes)
                    updated_redis_count += len(file_hashes)
                except Exception as redis_e:
                    logging.error(f"更新 Redis 失败: {redis_e}. 尝试回滚 Milvus 插入.")
                    rollback_expr = f'chunk_file in ["' + '","'.join(chunk_files) + '"]'
                    try:
                        col.delete(expr=rollback_expr)
                        logging.info(f"已回滚 Milvus 中的 {len(chunk_files)} 条记录。")
                    except Exception as rollback_e:
                        logging.error(f"回滚 Milvus 插入时出错：{rollback_e}")
                    raise redis_e

                existing_file_hashes.update(file_hashes)

            try:
                col.flush()
                logging.info("已刷新数据到 Milvus。")
            except Exception as e:
                logging.error(f"刷新数据到 Milvus 时出错：{e}")

        except RuntimeError as e:
            tqdm.write(f"显存不足或其他错误，尝试减小批次大小: {e}")
            batch_size = max(1, batch_size // 2)
            logging.warning(f"批次大小调整为 {batch_size}")
            continue
        except Exception as e:
            logging.error(f"处理批次时出错：{e}")
            continue

        processed_files_count += len(chunk_files)

        del chunk_files, doc_names, file_types, chunk_contents, embeddings, entities
        gc.collect()

    try:
        col.flush()
        col.load()
    except Exception as e:
        logging.error(f"最终刷新或加载集合时出错：{e}")

    progress_bar.close()

    logging.info(f"{collection_name} 索引完成")
    logging.info(f"新增文档数: {added_docs}")
    logging.info(f"更新文档数: {updated_docs}")
    logging.info(f"删除文档数: {deleted_docs}")