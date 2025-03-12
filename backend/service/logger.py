# -*- coding: utf-8 -*-

import logging
import os
from pathlib import Path

def setup_logging(log_path):
    logger = logging.getLogger('rag_server')
    if not logger.hasHandlers():
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console.setFormatter(formatter)
        logger.addHandler(console)
        handler = logging.FileHandler(log_path)
        handler.setLevel(logging.INFO)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


BASE_DIR = Path(__file__).resolve().parent.parent
LOGGING_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOGGING_DIR, exist_ok=True)
LOGGING_PATH = os.path.join(LOGGING_DIR, 'server.log')
logger = setup_logging(LOGGING_PATH)
