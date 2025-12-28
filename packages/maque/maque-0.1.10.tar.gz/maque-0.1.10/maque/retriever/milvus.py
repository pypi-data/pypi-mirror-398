#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Milvus 向量数据库检索器实现
"""

from typing import List, Optional, Union, Literal, TYPE_CHECKING

from loguru import logger

from ..embedding.base import BaseEmbedding
from .document import Document, SearchResult, Modality, _content_hash

if TYPE_CHECKING:
    from pymilvus import Collection


DistanceMetric = Literal["COSINE", "L2", "IP"]
ScalarType = Literal["VARCHAR", "INT64", "INT32", "INT16", "INT8", "FLOAT", "DOUBLE", "BOOL", "JSON", "ARRAY"]


class MilvusRetriever:
    """
    基于 Milvus 的检索器
    支持文本和图片的向量检索
    """

    # 预设索引配置
    INDEX_PRESETS = {
        "AUTOINDEX": {
            "index_type": "AUTOINDEX",
            "index_params": {},
            "search_params": {},
        },
        "HNSW": {
            "index_type": "HNSW",
            "index_params": {"M": 16, "efConstruction": 256},
            "search_params": {"ef": 128},
        },
        "IVF_FLAT": {
            "index_type": "IVF_FLAT",
            "index_params": {"nlist": 1024},
            "search_params": {"nprobe": 16},
        },
        "FLAT": {
            "index_type": "FLAT",
            "index_params": {},
            "search_params": {},
        },
    }

    # Scalar 类型映射
    SCALAR_TYPE_MAP = {
        "VARCHAR": ("VARCHAR", {"max_length": 256}),
        "INT64": ("INT64", {}),
        "INT32": ("INT32", {}),
        "INT16": ("INT16", {}),
        "INT8": ("INT8", {}),
        "FLOAT": ("FLOAT", {}),
        "DOUBLE": ("DOUBLE", {}),
        "BOOL": ("BOOL", {}),
        "JSON": ("JSON", {}),
        "ARRAY": ("ARRAY", {"element_type": "VARCHAR", "max_capacity": 256, "max_length": 256}),
    }

    def __init__(
        self,
        embedding: BaseEmbedding,
        host: str = "localhost",
        port: int = 19530,
        db_name: str = "default",
        collection_name: str = "default",
        distance_metric: DistanceMetric = "COSINE",
        auto_create: bool = True,
        index_config: Optional[dict] = None,
        scalar_fields: Optional[List[dict]] = None,
        primary_key: str = "id",
        field_mapping: Optional[dict] = None,
    ):
        """
        初始化检索器

        Args:
            embedding: Embedding 实例
            host: Milvus 服务地址
            port: Milvus 服务端口
            db_name: 数据库名称
            collection_name: 集合名称
            distance_metric: 距离度量方式 (COSINE/L2/IP)
            auto_create: 是否自动创建集合
            index_config: 索引配置，可选项：
                - None: 使用默认 HNSW 配置
                - "AUTOINDEX" / "HNSW" / "IVF_FLAT" / "FLAT": 使用预设配置
                - dict: 自定义配置，如：
                    {
                        "index_type": "HNSW",
                        "index_params": {"M": 16, "efConstruction": 256},
                        "search_params": {"ef": 128},
                        "id_max_length": 256,
                        "content_max_length": 65535,
                    }
            scalar_fields: 【创建模式】额外的 scalar 字段定义，用于高效过滤，如：
                [
                    {"name": "category", "dtype": "VARCHAR", "max_length": 64},
                    {"name": "timestamp", "dtype": "INT64"},
                    {"name": "score", "dtype": "FLOAT"},
                    {"name": "tags", "dtype": "ARRAY", "element_type": "VARCHAR", "max_capacity": 64, "max_length": 32},
                ]
                支持的类型: VARCHAR, INT64, INT32, INT16, INT8, FLOAT, DOUBLE, BOOL, JSON, ARRAY
                ARRAY 类型需要额外参数: element_type (元素类型), max_capacity (最大容量)
                字段值从 Document.metadata 中自动提取
                注意：读取已存在的 collection 时不需要此参数，字段类型会从 schema 自动提取
            primary_key: 主键字段名称，默认为 "id"，可自定义如 "user_id"、"content_id" 等
            field_mapping: 【读取模式】字段映射，用于读取已存在的 collection，如：
                {
                    "primary_key": "word_id",   # 主键字段名
                    "content": "word",          # 内容字段名
                    "embedding": "vector",      # 向量字段名
                    "modality": None,           # 模态字段名（可选，None 表示不存在）
                    "metadata": None,           # metadata 字段名（可选）
                }
                其他字段会自动从 schema 提取，类型也会自动识别

        使用模式：
            - 创建模式：使用 scalar_fields 定义额外字段
            - 读取模式：使用 field_mapping 映射核心字段，其他字段和类型自动从 schema 提取
        """
        try:
            from pymilvus import (
                connections,
                Collection,
                FieldSchema,
                CollectionSchema,
                DataType,
                utility,
                db,
            )
        except ImportError:
            raise ImportError(
                "pymilvus is required for MilvusRetriever. "
                "Install it with: pip install pymilvus"
            )

        self.embedding = embedding
        self.host = host
        self.port = port
        self.db_name = db_name
        self.collection_name = collection_name
        self.distance_metric = distance_metric
        self._dimension = embedding.dimension

        # 解析索引配置
        config = self._parse_index_config(index_config)
        self._index_type = config["index_type"]
        self._index_params = config["index_params"]
        self._search_params = config["search_params"]
        self._id_max_length = config.get("id_max_length", 256)
        self._content_max_length = config.get("content_max_length", 65535)

        # 解析字段映射
        self._field_mapping = self._parse_field_mapping(field_mapping, primary_key)
        self._primary_key = self._field_mapping["primary_key"]
        self._use_field_mapping = field_mapping is not None

        # 解析 scalar 字段配置（仅在创建模式下使用）
        self._scalar_fields = self._parse_scalar_fields(scalar_fields or [])

        # 连接 Milvus
        self._connection_alias = f"milvus_{db_name}_{collection_name}"
        logger.debug(f"Connecting to Milvus at {host}:{port}, db={db_name}")
        connections.connect(
            alias=self._connection_alias,
            host=host,
            port=port,
            db_name=db_name,
        )

        # 获取或创建集合
        if utility.has_collection(collection_name, using=self._connection_alias):
            logger.debug(f"Loading existing collection: {collection_name}")
            self.collection = Collection(
                name=collection_name,
                using=self._connection_alias,
            )
            # 从 schema 提取额外字段和类型
            self._extra_fields, self._field_types = self._extract_extra_fields_from_schema()
            # 补充 scalar_fields 中的类型信息（用户可能提供更精确的类型）
            for sf in self._scalar_fields:
                self._field_types[sf["name"]] = sf["dtype"]
            # 加载集合到内存
            self.collection.load()
            logger.info(f"Collection '{collection_name}' loaded, {self.count()} documents")
        elif auto_create:
            # 创建模式：使用 scalar_fields
            logger.debug(f"Creating new collection: {collection_name}")
            self._extra_fields = [sf["name"] for sf in self._scalar_fields]
            self._field_types = {sf["name"]: sf["dtype"] for sf in self._scalar_fields}
            self.collection = self._create_collection()
            logger.info(f"Collection '{collection_name}' created")
        else:
            raise ValueError(f"Collection '{collection_name}' does not exist in database '{db_name}'")

    def _parse_field_mapping(self, field_mapping: Optional[dict], primary_key: str) -> dict:
        """
        解析字段映射配置

        Args:
            field_mapping: 用户提供的字段映射
            primary_key: 默认主键名

        Returns:
            标准化的字段映射
        """
        # 默认映射
        default_mapping = {
            "primary_key": primary_key,
            "content": "content",
            "embedding": "embedding",
            "modality": "modality",
            "metadata": "metadata",
        }

        if not field_mapping:
            return default_mapping

        # 合并用户提供的映射
        result = default_mapping.copy()
        result.update(field_mapping)
        return result

    def _extract_extra_fields_from_schema(self) -> tuple[List[str], dict]:
        """
        从已存在的 collection schema 中提取额外字段名和类型

        Returns:
            (额外字段名列表, 字段类型映射)
        """
        from pymilvus import DataType

        # DataType 到字符串的映射
        dtype_to_str = {
            DataType.VARCHAR: "VARCHAR",
            DataType.INT64: "INT64",
            DataType.INT32: "INT32",
            DataType.INT16: "INT16",
            DataType.INT8: "INT8",
            DataType.FLOAT: "FLOAT",
            DataType.DOUBLE: "DOUBLE",
            DataType.BOOL: "BOOL",
            DataType.JSON: "JSON",
            DataType.ARRAY: "ARRAY",
        }

        # 已映射的字段名
        mapped_fields = {
            self._field_mapping["primary_key"],
            self._field_mapping["content"],
            self._field_mapping["embedding"],
        }
        # 可选的映射字段
        if self._field_mapping.get("modality"):
            mapped_fields.add(self._field_mapping["modality"])
        if self._field_mapping.get("metadata"):
            mapped_fields.add(self._field_mapping["metadata"])

        extra_fields = []
        field_types = {}
        for field in self.collection.schema.fields:
            # 跳过已映射的字段和向量字段
            if field.name in mapped_fields:
                continue
            if field.dtype in (DataType.FLOAT_VECTOR, DataType.BINARY_VECTOR):
                continue
            extra_fields.append(field.name)
            field_types[field.name] = dtype_to_str.get(field.dtype, "JSON")

        return extra_fields, field_types

    def _parse_index_config(self, index_config) -> dict:
        """解析索引配置"""
        # 默认使用 AUTOINDEX
        if index_config is None:
            return self.INDEX_PRESETS["AUTOINDEX"].copy()

        # 字符串预设
        if isinstance(index_config, str):
            if index_config not in self.INDEX_PRESETS:
                raise ValueError(f"Unknown preset: {index_config}, available: {list(self.INDEX_PRESETS.keys())}")
            return self.INDEX_PRESETS[index_config].copy()

        # 自定义 dict
        base = self.INDEX_PRESETS.get(index_config.get("index_type", "AUTOINDEX"), {}).copy()
        base.update(index_config)
        return base

    def _parse_scalar_fields(self, scalar_fields: List[dict]) -> List[dict]:
        """
        解析 scalar 字段配置

        Args:
            scalar_fields: 字段定义列表，如：
                [
                    {"name": "category", "dtype": "VARCHAR", "max_length": 64},
                    {"name": "timestamp", "dtype": "INT64"},
                    {"name": "tags", "dtype": "ARRAY", "element_type": "VARCHAR", "max_capacity": 64, "max_length": 32},
                ]

        Returns:
            标准化的字段配置列表
        """
        reserved_names = {self._primary_key, "content", "modality", "metadata", "embedding"}
        parsed = []

        for field in scalar_fields:
            name = field.get("name")
            dtype = field.get("dtype", "VARCHAR").upper()

            if not name:
                raise ValueError("Scalar field must have 'name'")
            if name in reserved_names:
                raise ValueError(f"Field name '{name}' is reserved")
            if dtype not in self.SCALAR_TYPE_MAP:
                raise ValueError(f"Unknown dtype '{dtype}', available: {list(self.SCALAR_TYPE_MAP.keys())}")

            # 构建标准化配置
            parsed_field = {"name": name, "dtype": dtype}

            # VARCHAR 需要 max_length
            if dtype == "VARCHAR":
                parsed_field["max_length"] = field.get("max_length", 256)
            # ARRAY 需要 element_type, max_capacity, 以及可能的 max_length
            elif dtype == "ARRAY":
                element_type = field.get("element_type", "VARCHAR").upper()
                parsed_field["element_type"] = element_type
                parsed_field["max_capacity"] = field.get("max_capacity", 256)
                # 如果元素类型是 VARCHAR，需要 max_length
                if element_type == "VARCHAR":
                    parsed_field["max_length"] = field.get("max_length", 256)

            parsed.append(parsed_field)

        return parsed

    def _create_collection(self) -> "Collection":
        """创建集合"""
        from pymilvus import (
            Collection,
            FieldSchema,
            CollectionSchema,
            DataType,
        )

        # 基础字段（使用字段映射）
        fm = self._field_mapping
        fields = [
            FieldSchema(name=fm["primary_key"], dtype=DataType.VARCHAR, max_length=self._id_max_length, is_primary=True),
            FieldSchema(name=fm["content"], dtype=DataType.VARCHAR, max_length=self._content_max_length),
            FieldSchema(name=fm["embedding"], dtype=DataType.FLOAT_VECTOR, dim=self._dimension),
        ]

        # 可选字段
        if fm.get("modality"):
            fields.append(FieldSchema(name=fm["modality"], dtype=DataType.VARCHAR, max_length=32))
        if fm.get("metadata"):
            fields.append(FieldSchema(name=fm["metadata"], dtype=DataType.JSON))

        # 添加额外的 scalar 字段
        for sf in self._scalar_fields:
            dtype = getattr(DataType, sf["dtype"])
            if sf["dtype"] == "VARCHAR":
                fields.append(FieldSchema(name=sf["name"], dtype=dtype, max_length=sf["max_length"]))
            elif sf["dtype"] == "ARRAY":
                element_type = getattr(DataType, sf["element_type"])
                if sf["element_type"] == "VARCHAR":
                    fields.append(FieldSchema(
                        name=sf["name"],
                        dtype=dtype,
                        element_type=element_type,
                        max_capacity=sf["max_capacity"],
                        max_length=sf["max_length"],
                    ))
                else:
                    fields.append(FieldSchema(
                        name=sf["name"],
                        dtype=dtype,
                        element_type=element_type,
                        max_capacity=sf["max_capacity"],
                    ))
            else:
                fields.append(FieldSchema(name=sf["name"], dtype=dtype))

        schema = CollectionSchema(
            fields=fields,
            description=f"Collection for {self.collection_name}",
        )

        collection = Collection(
            name=self.collection_name,
            schema=schema,
            using=self._connection_alias,
        )

        # 创建索引
        index_params = {
            "metric_type": self.distance_metric,
            "index_type": self._index_type,
            "params": self._index_params,
        }
        collection.create_index(field_name=fm["embedding"], index_params=index_params)

        # 加载到内存
        collection.load()

        return collection

    def _get_input_type(self, modality: Modality) -> str:
        """获取 embedding 的 input_type 参数"""
        return "image" if modality == "image" else "text"

    def _embed_documents(self, documents: List[Document]) -> List[List[float]]:
        """对文档进行向量化"""
        if not documents:
            return []

        has_image = any(doc.is_image for doc in documents)
        if has_image and not self.embedding.supports_image:
            raise ValueError(
                f"Embedding 不支持图片，但文档中包含图片。"
                f"请使用 MultiModalEmbedding。"
            )

        if has_image:
            embeddings = []
            for doc in documents:
                input_type = self._get_input_type(doc.modality)
                vec = self.embedding.embed([doc.content], input_type=input_type)[0]
                embeddings.append(vec)
            return embeddings
        else:
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

    def _prepare_insert_data(self, documents: List[Document], embeddings: List[List[float]]) -> List[dict]:
        """
        准备插入数据，包含基础字段和额外字段

        Args:
            documents: 文档列表
            embeddings: 向量列表

        Returns:
            行格式的数据列表（每个元素是一个字典，代表一行）
        """
        fm = self._field_mapping

        rows = []
        for i, doc in enumerate(documents):
            row = {
                fm["primary_key"]: doc.id,
                fm["content"]: doc.content,
                fm["embedding"]: embeddings[i],
            }

            # 可选字段
            if fm.get("modality"):
                row[fm["modality"]] = doc.modality
            if fm.get("metadata"):
                row[fm["metadata"]] = doc.metadata

            # 添加所有额外字段值（从 metadata 中提取）
            for field_name in self._extra_fields:
                value = doc.metadata.get(field_name)
                dtype = self._field_types.get(field_name)

                # 如果值为 None，根据类型设置默认值
                if value is None:
                    if dtype == "VARCHAR":
                        value = ""
                    elif dtype in ("INT64", "INT32", "INT16", "INT8"):
                        value = 0
                    elif dtype in ("FLOAT", "DOUBLE"):
                        value = 0.0
                    elif dtype == "BOOL":
                        value = False
                    else:
                        # JSON / ARRAY 等类型默认空列表
                        value = []

                row[field_name] = value

            rows.append(row)

        return rows

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

        # 准备数据（包含 scalar 字段）
        data = self._prepare_insert_data(documents, embeddings)

        # 插入数据
        self.collection.insert(data)
        self.collection.flush()
        logger.debug(f"Added {len(documents)} documents")

        return [doc.id for doc in documents]

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

        # 准备数据（包含 scalar 字段）
        data = self._prepare_insert_data(documents, embeddings)

        # Milvus upsert
        self.collection.upsert(data)
        self.collection.flush()
        logger.debug(f"Upserted {len(documents)} documents")

        return [doc.id for doc in documents]

    def delete(self, ids: Union[str, List[str]]) -> None:
        """
        删除文档

        Args:
            ids: 单个 ID 或 ID 列表
        """
        if isinstance(ids, str):
            ids = [ids]

        # 构建删除表达式
        ids_str = ", ".join([f'"{id}"' for id in ids])
        expr = f"{self._primary_key} in [{ids_str}]"
        self.collection.delete(expr)
        self.collection.flush()
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

    def _get_output_fields(self) -> List[str]:
        """获取查询时需要返回的所有字段"""
        fm = self._field_mapping
        fields = [fm["primary_key"], fm["content"]]

        # 可选字段（可能为 None）
        if fm.get("modality"):
            fields.append(fm["modality"])
        if fm.get("metadata"):
            fields.append(fm["metadata"])

        # 额外字段（统一由 _extra_fields 管理）
        fields.extend(self._extra_fields)

        return fields

    def search(
        self,
        query: str,
        top_k: int = 5,
        query_type: Modality = "text",
        expr: Optional[str] = None,
    ) -> List[SearchResult]:
        """
        检索相似文档

        Args:
            query: 查询内容（文本或图片路径/URL）
            top_k: 返回数量
            query_type: 查询类型 "text" / "image"
            expr: Milvus 过滤表达式 (例如: 'metadata["category"] == "tech"')

        Returns:
            SearchResult 列表
        """
        query_embedding = self._embed_query(query, query_type)

        search_params = {
            "metric_type": self.distance_metric,
            "params": self._search_params,
        }

        results = self.collection.search(
            data=[query_embedding],
            anns_field=self._field_mapping["embedding"],
            param=search_params,
            limit=top_k,
            expr=expr,
            output_fields=self._get_output_fields(),
        )

        parsed = self._parse_results(results)
        return parsed[0] if parsed else []

    def search_by_vector(
        self,
        vector: List[float],
        top_k: int = 5,
        expr: Optional[str] = None,
    ) -> List[SearchResult]:
        """
        直接使用向量检索

        Args:
            vector: 查询向量
            top_k: 返回数量
            expr: Milvus 过滤表达式

        Returns:
            SearchResult 列表
        """
        search_params = {
            "metric_type": self.distance_metric,
            "params": self._search_params,
        }

        results = self.collection.search(
            data=[vector],
            anns_field=self._field_mapping["embedding"],
            param=search_params,
            limit=top_k,
            expr=expr,
            output_fields=self._get_output_fields(),
        )

        parsed = self._parse_results(results)
        return parsed[0] if parsed else []

    def search_batch(
        self,
        queries: List[str],
        top_k: int = 5,
        query_type: Modality = "text",
        expr: Optional[str] = None,
    ) -> List[List[SearchResult]]:
        """
        批量检索相似文档

        Args:
            queries: 查询内容列表（文本或图片路径/URL）
            top_k: 每个查询返回的数量
            query_type: 查询类型 "text" / "image"
            expr: Milvus 过滤表达式

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

        search_params = {
            "metric_type": self.distance_metric,
            "params": self._search_params,
        }

        results = self.collection.search(
            data=query_embeddings,
            anns_field=self._field_mapping["embedding"],
            param=search_params,
            limit=top_k,
            expr=expr,
            output_fields=self._get_output_fields(),
        )

        return self._parse_results(results)

    def search_by_vectors(
        self,
        vectors: List[List[float]],
        top_k: int = 5,
        expr: Optional[str] = None,
    ) -> List[List[SearchResult]]:
        """
        批量使用向量检索

        Args:
            vectors: 查询向量列表
            top_k: 每个查询返回的数量
            expr: Milvus 过滤表达式

        Returns:
            SearchResult 列表的列表，每个向量对应一个结果列表

        Example:
            >>> vectors = [[0.1, 0.2, ...], [0.3, 0.4, ...]]
            >>> results = retriever.search_by_vectors(vectors, top_k=5)
        """
        if not vectors:
            return []

        search_params = {
            "metric_type": self.distance_metric,
            "params": self._search_params,
        }

        results = self.collection.search(
            data=vectors,
            anns_field=self._field_mapping["embedding"],
            param=search_params,
            limit=top_k,
            expr=expr,
            output_fields=self._get_output_fields(),
        )

        return self._parse_results(results)

    def _parse_results(self, results) -> List[List[SearchResult]]:
        """
        解析 Milvus 返回结果

        Args:
            results: Milvus search 返回的结果

        Returns:
            SearchResult 列表的列表，每个查询对应一个结果列表
        """
        if not results or len(results) == 0:
            return []

        fm = self._field_mapping
        all_results = []

        for hits in results:
            query_results = []
            for hit in hits:
                entity = hit.entity

                # 距离转相似度
                distance = hit.distance
                if self.distance_metric == "COSINE":
                    score = distance  # Milvus COSINE 返回的是相似度
                elif self.distance_metric == "IP":
                    score = distance  # IP 内积越大越相似
                else:
                    score = -distance  # L2 距离越小越好

                # 合并 metadata 和额外字段
                # 注意：pymilvus Hit 对象的 `in` 操作符不可靠，需要直接用 get
                metadata_field = fm.get("metadata")
                metadata = dict(entity.get(metadata_field) or {}) if metadata_field else {}

                for name in self._extra_fields:
                    value = entity.get(name)
                    if value is not None:
                        metadata[name] = value

                # 获取 modality（可能不存在）
                modality_field = fm.get("modality")
                modality = entity.get(modality_field, "text") if modality_field else "text"

                query_results.append(SearchResult(
                    id=entity.get(fm["primary_key"], ""),
                    content=entity.get(fm["content"], ""),
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
        expr: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Document]:
        """
        获取文档

        Args:
            ids: 文档 ID 或 ID 列表
            expr: Milvus 过滤表达式
            limit: 返回数量限制

        Returns:
            Document 列表
        """
        if isinstance(ids, str):
            ids = [ids]

        # 构建查询表达式
        pk = self._primary_key
        if ids:
            ids_str = ", ".join([f'"{id}"' for id in ids])
            query_expr = f"{pk} in [{ids_str}]"
            if expr:
                query_expr = f"({query_expr}) and ({expr})"
        else:
            query_expr = expr or ""

        results = self.collection.query(
            expr=query_expr if query_expr else f"{pk} != ''",
            output_fields=self._get_output_fields(),
            limit=limit or 16384,
        )

        fm = self._field_mapping
        documents = []

        for item in results:
            # 合并 metadata 和额外字段
            metadata_field = fm.get("metadata")
            metadata = dict(item.get(metadata_field) or {}) if metadata_field else {}

            for name in self._extra_fields:
                value = item.get(name)
                if value is not None:
                    metadata[name] = value

            # 获取 modality（可能不存在）
            modality_field = fm.get("modality")
            modality = item.get(modality_field, "text") if modality_field else "text"

            documents.append(Document(
                id=item.get(pk, ""),
                content=item.get(fm["content"], ""),
                modality=modality,
                metadata=metadata,
            ))

        return documents

    def count(self) -> int:
        """返回文档数量"""
        return self.collection.num_entities

    def clear(self) -> None:
        """清空集合（删除并重建）"""
        from pymilvus import utility

        logger.info(f"Clearing collection: {self.collection_name}")
        utility.drop_collection(self.collection_name, using=self._connection_alias)
        self.collection = self._create_collection()
        logger.info(f"Collection '{self.collection_name}' cleared and recreated")

    def drop(self) -> None:
        """
        彻底删除集合

        警告：此操作不可逆，会永久删除 collection 及其所有数据。
        删除后 retriever 实例将不可用，需要重新创建。
        """
        from pymilvus import utility

        logger.warning(f"Dropping collection: {self.collection_name}")
        utility.drop_collection(self.collection_name, using=self._connection_alias)
        self.collection = None
        logger.info(f"Collection '{self.collection_name}' dropped")

    # ========== 便利方法 ==========

    def upsert_batch(
        self,
        documents: List[Document],
        batch_size: int = 100,
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
        batch_size = 1000
        pk = self._primary_key

        for i in range(0, len(candidate_ids), batch_size):
            batch_ids = candidate_ids[i:i + batch_size]
            ids_str = ", ".join([f'"{id}"' for id in batch_ids])
            try:
                results = self.collection.query(
                    expr=f"{pk} in [{ids_str}]",
                    output_fields=[pk],
                )
                for item in results:
                    existing_ids.add(item.get(pk))
            except Exception:
                pass

        return existing_ids

    def get_all_ids(self) -> List[str]:
        """获取所有文档 ID"""
        pk = self._primary_key
        results = self.collection.query(
            expr=f"{pk} != ''",
            output_fields=[pk],
            limit=16384,
        )
        return [item.get(pk, "") for item in results]

    def close(self) -> None:
        """关闭连接"""
        from pymilvus import connections
        connections.disconnect(self._connection_alias)

    def __repr__(self) -> str:
        return (
            f"MilvusRetriever("
            f"host={self.host!r}, "
            f"port={self.port}, "
            f"db={self.db_name!r}, "
            f"collection={self.collection_name!r}, "
            f"count={self.count()}, "
            f"embedding={self.embedding.__class__.__name__})"
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
