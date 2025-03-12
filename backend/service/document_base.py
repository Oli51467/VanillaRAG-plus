# -*- coding: utf-8 -*-

import gc

import numpy as np
import torch
from pymilvus import Collection, connections
from pymilvus.model.hybrid import BGEM3EmbeddingFunction
from pymilvus.model.reranker import BGERerankFunction
from service.config import Config


class KnowledgeBase:
    def __init__(self, config: Config):
        print("KnowledgeBase init")