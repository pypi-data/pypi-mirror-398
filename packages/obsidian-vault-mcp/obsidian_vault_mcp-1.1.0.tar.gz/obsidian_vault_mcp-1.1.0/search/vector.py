"""向量语义搜索"""

import logging
from pathlib import Path
from dataclasses import dataclass

import lancedb
from fastembed import TextEmbedding

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """搜索结果"""
    path: str
    score: float
    snippet: str


class VectorSearch:
    """向量搜索引擎"""

    def __init__(self, storage_path: Path, model_name: str = "BAAI/bge-small-zh-v1.5"):
        self.storage_path = storage_path
        self.model_name = model_name
        self.db_path = storage_path / "vector.lance"

        self._model: TextEmbedding | None = None
        self._db: lancedb.DBConnection | None = None
        self._table = None

    def _ensure_model(self):
        """延迟加载 embedding 模型"""
        if self._model is None:
            logger.info(f"加载 embedding 模型: {self.model_name}")
            self._model = TextEmbedding(self.model_name)

    def _ensure_db(self):
        """确保数据库连接"""
        if self._db is None:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._db = lancedb.connect(str(self.db_path))

    def _embed(self, texts: list[str]) -> list[list[float]]:
        """生成 embeddings"""
        self._ensure_model()
        return list(self._model.embed(texts))

    def is_indexed(self) -> bool:
        """检查是否已有索引"""
        self._ensure_db()
        try:
            self._table = self._db.open_table("documents")
            return self._table.count_rows() > 0
        except Exception:
            return False

    def index(self, documents: dict[str, str]):
        """建立向量索引"""
        if not documents:
            return

        self._ensure_db()

        paths = list(documents.keys())
        contents = list(documents.values())

        logger.info(f"生成 {len(paths)} 个文档的向量...")
        vectors = self._embed(contents)

        # 准备数据
        data = [
            {
                "path": path,
                "content": content[:500],  # 只存前 500 字作为 snippet
                "vector": vector,
            }
            for path, content, vector in zip(paths, contents, vectors)
        ]

        # 覆盖写入
        self._table = self._db.create_table("documents", data, mode="overwrite")
        logger.info("向量索引完成")

    def add(self, path: str, content: str):
        """添加单个文档"""
        if self._table is None:
            self.index({path: content})
            return

        vector = self._embed([content])[0]
        self._table.add([{
            "path": path,
            "content": content[:500],
            "vector": vector,
        }])

    def remove(self, path: str):
        """移除文档"""
        if self._table is not None:
            self._table.delete(f'path = "{path}"')

    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        """语义搜索"""
        if self._table is None:
            if not self.is_indexed():
                return []

        query_vector = self._embed([query])[0]

        results = (
            self._table
            .search(query_vector)
            .limit(limit)
            .to_list()
        )

        return [
            SearchResult(
                path=r["path"],
                score=1 - r["_distance"],  # 转换距离为相似度
                snippet=r["content"],
            )
            for r in results
        ]

    def get_stats(self) -> dict:
        """获取统计信息"""
        if self._table is None:
            self._ensure_db()
            try:
                self._table = self._db.open_table("documents")
            except Exception:
                return {"indexed": 0}

        return {"indexed": self._table.count_rows()}
