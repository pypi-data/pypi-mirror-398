#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ChromaDB 检索器实现
"""

from typing import List, Optional, Union, Literal

from loguru import logger
import chromadb
from chromadb.config import Settings

from ..embedding.base import BaseEmbedding
from .document import Document, SearchResult, Modality, _content_hash


DistanceMetric = Literal["cosine", "l2", "ip"]


class ChromaRetriever:
    """
    基于 ChromaDB 的检索器
    支持文本和图片的向量检索
    """

    def __init__(
        self,
        embedding: BaseEmbedding,
        persist_dir: Optional[str] = None,
        collection_name: str = "default",
        distance_metric: DistanceMetric = "cosine",
    ):
        """
        初始化检索器

        Args:
            embedding: Embedding 实例（TextEmbedding 或 MultiModalEmbedding）
            persist_dir: 持久化目录，None 为内存模式
            collection_name: 集合名称
            distance_metric: 距离度量方式 (cosine/l2/ip)
        """
        self.embedding = embedding
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self.distance_metric = distance_metric

        # 初始化 ChromaDB
        if persist_dir:
            logger.debug(f"Initializing ChromaDB with persist_dir: {persist_dir}")
            self.client = chromadb.PersistentClient(path=persist_dir)
        else:
            logger.debug("Initializing ChromaDB in memory mode")
            self.client = chromadb.Client()

        # 获取或创建集合
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": distance_metric},
        )
        logger.info(f"Collection '{collection_name}' ready, {self.count()} documents")

    def _get_input_type(self, modality: Modality) -> str:
        """获取 embedding 的 input_type 参数"""
        return "image" if modality == "image" else "text"

    def _embed_documents(self, documents: List[Document]) -> List[List[float]]:
        """对文档进行向量化"""
        if not documents:
            return []

        # 检查是否有图片，如果有则需要多模态 embedding
        has_image = any(doc.is_image for doc in documents)
        if has_image and not self.embedding.supports_image:
            raise ValueError(
                f"Embedding 不支持图片，但文档中包含图片。"
                f"请使用 MultiModalEmbedding。"
            )

        # 分组处理：文本和图片分开
        if has_image:
            # 多模态：按顺序处理，保持索引对应
            embeddings = []
            for doc in documents:
                input_type = self._get_input_type(doc.modality)
                vec = self.embedding.embed([doc.content], input_type=input_type)[0]
                embeddings.append(vec)
            return embeddings
        else:
            # 纯文本：批量处理
            contents = [doc.content for doc in documents]
            return self.embedding.embed(contents)

    def _embed_query(
        self,
        query: str,
        query_type: Modality = "text",
    ) -> List[float]:
        """对查询进行向量化"""
        if query_type == "image" and not self.embedding.supports_image:
            raise ValueError("Embedding 不支持图片查询")

        if self.embedding.supports_image:
            input_type = self._get_input_type(query_type)
            return self.embedding.embed([query], input_type=input_type)[0]
        else:
            return self.embedding.embed([query])[0]

    def _embed_queries(
        self,
        queries: List[str],
        query_type: Modality = "text",
    ) -> List[List[float]]:
        """对多个查询进行批量向量化"""
        if not queries:
            return []

        if query_type == "image" and not self.embedding.supports_image:
            raise ValueError("Embedding 不支持图片查询")

        if self.embedding.supports_image:
            input_type = self._get_input_type(query_type)
            return self.embedding.embed(queries, input_type=input_type)
        else:
            return self.embedding.embed(queries)

    # ========== 索引操作 ==========

    def add(
        self,
        documents: Union[Document, List[Document]],
        skip_existing: bool = False,
    ) -> List[str]:
        """
        添加文档

        Args:
            documents: 单个文档或文档列表
            skip_existing: 是否跳过已存在的文档

        Returns:
            添加的文档 ID 列表
        """
        if isinstance(documents, Document):
            documents = [documents]

        if not documents:
            return []

        # 过滤已存在的文档
        if skip_existing:
            existing_ids = self._get_existing_ids([doc.id for doc in documents])
            skipped = len([doc for doc in documents if doc.id in existing_ids])
            documents = [doc for doc in documents if doc.id not in existing_ids]
            if skipped > 0:
                logger.debug(f"Skipped {skipped} existing documents")
            if not documents:
                return []

        # 向量化
        embeddings = self._embed_documents(documents)

        # 准备数据
        ids = [doc.id for doc in documents]
        contents = [doc.content for doc in documents]
        metadatas = [
            {**doc.metadata, "_modality": doc.modality}
            for doc in documents
        ]

        # 添加到集合
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=contents,
            metadatas=metadatas,
        )
        logger.debug(f"Added {len(documents)} documents")

        return ids

    def upsert(
        self,
        documents: Union[Document, List[Document]],
        skip_existing: bool = False,
    ) -> List[str]:
        """
        添加或更新文档

        Args:
            documents: 单个文档或文档列表
            skip_existing: 是否跳过已存在的文档（为 True 时行为与 add 相同）

        Returns:
            upsert 的文档 ID 列表
        """
        if isinstance(documents, Document):
            documents = [documents]

        if not documents:
            return []

        # 过滤已存在的文档
        if skip_existing:
            existing_ids = self._get_existing_ids([doc.id for doc in documents])
            documents = [doc for doc in documents if doc.id not in existing_ids]
            if not documents:
                return []

        # 向量化
        embeddings = self._embed_documents(documents)

        # 准备数据
        ids = [doc.id for doc in documents]
        contents = [doc.content for doc in documents]
        metadatas = [
            {**doc.metadata, "_modality": doc.modality}
            for doc in documents
        ]

        # upsert 到集合
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=contents,
            metadatas=metadatas,
        )
        logger.debug(f"Upserted {len(documents)} documents")

        return ids

    def delete(self, ids: Union[str, List[str]]) -> None:
        """
        删除文档

        Args:
            ids: 单个 ID 或 ID 列表
        """
        if isinstance(ids, str):
            ids = [ids]

        self.collection.delete(ids=ids)
        logger.debug(f"Deleted {len(ids)} documents")

    def delete_by_content(self, contents: Union[str, List[str]]) -> None:
        """
        根据内容删除文档

        Args:
            contents: 单个内容或内容列表
        """
        if isinstance(contents, str):
            contents = [contents]

        ids = [_content_hash(content) for content in contents]
        self.delete(ids)

    # ========== 检索操作 ==========

    def search(
        self,
        query: str,
        top_k: int = 5,
        query_type: Modality = "text",
        where: Optional[dict] = None,
        where_document: Optional[dict] = None,
    ) -> List[SearchResult]:
        """
        检索相似文档

        Args:
            query: 查询内容（文本或图片路径/URL）
            top_k: 返回数量
            query_type: 查询类型 "text" / "image"
            where: 元数据过滤条件
            where_document: 文档内容过滤条件

        Returns:
            SearchResult 列表
        """
        # 向量化查询
        query_embedding = self._embed_query(query, query_type)

        # 检索
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
            where_document=where_document,
        )

        parsed = self._parse_results(results)
        return parsed[0] if parsed else []

    def search_by_vector(
        self,
        vector: List[float],
        top_k: int = 5,
        where: Optional[dict] = None,
    ) -> List[SearchResult]:
        """
        直接使用向量检索

        Args:
            vector: 查询向量
            top_k: 返回数量
            where: 元数据过滤条件

        Returns:
            SearchResult 列表
        """
        results = self.collection.query(
            query_embeddings=[vector],
            n_results=top_k,
            where=where,
        )

        return self._parse_results(results)[0]

    def search_batch(
        self,
        queries: List[str],
        top_k: int = 5,
        query_type: Modality = "text",
        where: Optional[dict] = None,
        where_document: Optional[dict] = None,
    ) -> List[List[SearchResult]]:
        """
        批量检索相似文档

        Args:
            queries: 查询内容列表（文本或图片路径/URL）
            top_k: 每个查询返回的数量
            query_type: 查询类型 "text" / "image"
            where: 元数据过滤条件
            where_document: 文档内容过滤条件

        Returns:
            SearchResult 列表的列表，每个查询对应一个结果列表

        Example:
            >>> results = retriever.search_batch(["query1", "query2"], top_k=5)
            >>> for i, query_results in enumerate(results):
            ...     print(f"Query {i}: {len(query_results)} results")
        """
        if not queries:
            return []

        # 批量向量化查询
        query_embeddings = self._embed_queries(queries, query_type)

        # 批量检索
        results = self.collection.query(
            query_embeddings=query_embeddings,
            n_results=top_k,
            where=where,
            where_document=where_document,
        )

        return self._parse_results(results)

    def search_by_vectors(
        self,
        vectors: List[List[float]],
        top_k: int = 5,
        where: Optional[dict] = None,
    ) -> List[List[SearchResult]]:
        """
        批量使用向量检索

        Args:
            vectors: 查询向量列表
            top_k: 每个查询返回的数量
            where: 元数据过滤条件

        Returns:
            SearchResult 列表的列表，每个向量对应一个结果列表

        Example:
            >>> vectors = [[0.1, 0.2, ...], [0.3, 0.4, ...]]
            >>> results = retriever.search_by_vectors(vectors, top_k=5)
        """
        if not vectors:
            return []

        results = self.collection.query(
            query_embeddings=vectors,
            n_results=top_k,
            where=where,
        )

        return self._parse_results(results)

    def _parse_results(self, results: dict) -> List[List[SearchResult]]:
        """
        解析 ChromaDB 返回结果

        Args:
            results: ChromaDB query 返回的结果字典

        Returns:
            SearchResult 列表的列表，每个查询对应一个结果列表
        """
        if not results or not results.get("ids"):
            return []

        all_results = []
        num_queries = len(results["ids"])

        for query_idx in range(num_queries):
            ids = results["ids"][query_idx]
            if not ids:
                all_results.append([])
                continue

            documents = results.get("documents", [[]] * num_queries)[query_idx]
            metadatas = results.get("metadatas", [[]] * num_queries)[query_idx]
            distances = results.get("distances", [[]] * num_queries)[query_idx]

            query_results = []
            for i, doc_id in enumerate(ids):
                metadata = dict(metadatas[i]) if metadatas and i < len(metadatas) else {}
                modality = metadata.pop("_modality", "text")

                # 距离转相似度 (cosine: 1 - distance)
                distance = distances[i] if distances and i < len(distances) else 0
                if self.distance_metric == "cosine":
                    score = 1 - distance
                else:
                    score = -distance  # l2/ip: 距离越小越好

                query_results.append(SearchResult(
                    id=doc_id,
                    content=documents[i] if documents and i < len(documents) else "",
                    score=score,
                    modality=modality,
                    metadata=metadata,
                ))

            all_results.append(query_results)

        return all_results

    # ========== 管理操作 ==========

    def get(
        self,
        ids: Optional[Union[str, List[str]]] = None,
        where: Optional[dict] = None,
        limit: Optional[int] = None,
    ) -> List[Document]:
        """
        获取文档

        Args:
            ids: 文档 ID 或 ID 列表
            where: 元数据过滤条件
            limit: 返回数量限制

        Returns:
            Document 列表
        """
        if isinstance(ids, str):
            ids = [ids]

        results = self.collection.get(
            ids=ids,
            where=where,
            limit=limit,
        )

        documents = []
        if results and results.get("ids"):
            for i, doc_id in enumerate(results["ids"]):
                metadata = results["metadatas"][i] if results.get("metadatas") else {}
                modality = metadata.pop("_modality", "text")
                content = results["documents"][i] if results.get("documents") else ""

                documents.append(Document(
                    id=doc_id,
                    content=content,
                    modality=modality,
                    metadata=metadata,
                ))

        return documents

    def count(self) -> int:
        """返回文档数量"""
        return self.collection.count()

    def clear(self) -> None:
        """清空集合"""
        logger.info(f"Clearing collection: {self.collection_name}")
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": self.distance_metric},
        )
        logger.info(f"Collection '{self.collection_name}' cleared and recreated")

    # ========== 便利方法 ==========

    def upsert_batch(
        self,
        documents: List[Document],
        batch_size: int = 32,
        skip_existing: bool = False,
        show_progress: bool = True,
    ) -> int:
        """
        批量插入文档（带进度条和增量更新支持）

        Args:
            documents: 文档列表
            batch_size: 批处理大小
            skip_existing: 是否跳过已存在的文档
            show_progress: 是否显示进度条

        Returns:
            实际插入的文档数量

        Example:
            >>> retriever = ChromaRetriever(embedding, persist_dir, collection_name)
            >>> docs = [Document.text(content=text, id=f"doc_{i}") for i, text in enumerate(texts)]
            >>> count = retriever.upsert_batch(docs, batch_size=32, skip_existing=True)
            >>> print(f"插入 {count} 个文档")
        """
        if not documents:
            return 0

        total_docs = len(documents)
        logger.info(f"Starting batch upsert: {total_docs} documents, batch_size={batch_size}")

        # 过滤已存在的文档
        skipped = 0
        if skip_existing:
            existing_ids = self._get_existing_ids([doc.id for doc in documents])
            skipped = len([doc for doc in documents if doc.id in existing_ids])
            documents = [doc for doc in documents if doc.id not in existing_ids]
            if skipped > 0:
                logger.info(f"Skipped {skipped} existing documents")
            if not documents:
                return 0

        # 批量插入
        inserted = 0
        total_batches = (len(documents) + batch_size - 1) // batch_size
        iterator = range(0, len(documents), batch_size)

        if show_progress:
            try:
                from tqdm import tqdm
                iterator = tqdm(
                    iterator,
                    desc="Upserting",
                    total=total_batches,
                    unit="batch",
                )
            except ImportError:
                logger.debug("tqdm not installed, progress bar disabled")

        for i in iterator:
            batch = documents[i:i + batch_size]
            self.upsert(batch)
            inserted += len(batch)

        logger.info(f"Batch upsert completed: {inserted} inserted, {skipped} skipped")
        return inserted

    def _get_existing_ids(self, candidate_ids: List[str]) -> set:
        """获取已存在的文档 ID 集合"""
        existing_ids = set()
        batch_size = 10000

        for i in range(0, len(candidate_ids), batch_size):
            batch_ids = candidate_ids[i:i + batch_size]
            try:
                results = self.collection.get(ids=batch_ids)
                if results and results.get("ids"):
                    existing_ids.update(results["ids"])
            except Exception:
                pass  # ID 不存在时忽略

        return existing_ids

    def get_all_ids(self) -> List[str]:
        """获取所有文档 ID"""
        results = self.collection.get(include=[])
        return results.get("ids", [])

    def __repr__(self) -> str:
        return (
            f"ChromaRetriever("
            f"collection={self.collection_name!r}, "
            f"count={self.count()}, "
            f"embedding={self.embedding.__class__.__name__})"
        )
