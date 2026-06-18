"""
向量存储服务
使用 ChromaDB 存储和检索记忆向量
"""
import uuid
import logging
from typing import List, Dict, Optional, Any
import chromadb
from chromadb.config import Settings as ChromaSettings

from config import settings

logger = logging.getLogger(__name__)


class VectorStore:
    """向量存储类 - 延迟初始化"""
    
    def __init__(self):
        """初始化（不立即创建 ChromaDB 客户端）"""
        self._client = None
        self._collection = None
        self._initialized = False
    
    def _ensure_init(self):
        """延迟初始化 ChromaDB"""
        if self._initialized:
            return
        
        try:
            self._client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIR,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            self._collection = self._client.get_or_create_collection(
                name="memories",
                metadata={"description": "用户记忆向量存储"}
            )
            
            self._initialized = True
            logger.info("ChromaDB 向量存储初始化成功")
        except Exception as e:
            logger.error(f"ChromaDB 初始化失败: {e}")
            self._initialized = True  # 标记已尝试，不重复初始化
    
    @property
    def is_ready(self) -> bool:
        """检查向量存储是否可用"""
        self._ensure_init()
        return self._collection is not None
    
    def add_memory(
        self,
        user_id: str,
        memory_id: str,
        content: str,
        category: str,
        importance: int
    ) -> bool:
        """
        添加记忆到向量存储
        """
        try:
            self._ensure_init()
            if not self._collection:
                logger.warning("ChromaDB 不可用，跳过添加记忆")
                return False
            
            self._collection.add(
                ids=[f"{user_id}_{memory_id}"],
                documents=[content],
                metadatas=[{
                    "user_id": user_id,
                    "memory_id": memory_id,
                    "category": category,
                    "importance": importance
                }]
            )
            return True
        except Exception as e:
            logger.warning(f"添加记忆失败: {e}")
            return False
    
    def search_memories(
        self,
        user_id: str,
        query: str,
        n_results: int = 5,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索用户记忆
        """
        try:
            self._ensure_init()
            if not self._collection:
                logger.warning("ChromaDB 不可用，跳过记忆检索")
                return []
            
            # 构建查询
            where_filter = {"user_id": user_id}
            if category:
                where_filter["category"] = category
            
            results = self._collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter
            )
            
            # 解析结果
            memories = []
            if results and results["ids"] and results["ids"][0]:
                for i, memory_id in enumerate(results["ids"][0]):
                    memories.append({
                        "memory_id": results["metadatas"][0][i].get("memory_id", ""),
                        "content": results["documents"][0][i],
                        "category": results["metadatas"][0][i].get("category", ""),
                        "importance": results["metadatas"][0][i].get("importance", 5),
                        "distance": results["distances"][0][i] if "distances" in results else 0
                    })
            
            return memories
        except Exception as e:
            logger.warning(f"搜索记忆失败: {e}")
            return []
    
    def get_all_memories(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        获取用户所有记忆
        """
        try:
            self._ensure_init()
            if not self._collection:
                return []
            
            results = self._collection.get(
                where={"user_id": user_id},
                limit=limit
            )
            
            memories = []
            if results and results["ids"]:
                for i, memory_id in enumerate(results["ids"]):
                    memories.append({
                        "memory_id": results["metadatas"][i].get("memory_id", ""),
                        "content": results["documents"][i],
                        "category": results["metadatas"][i].get("category", ""),
                        "importance": results["metadatas"][i].get("importance", 5)
                    })
            
            return memories
        except Exception as e:
            logger.warning(f"获取记忆失败: {e}")
            return []
    
    def delete_memory(self, user_id: str, memory_id: str) -> bool:
        """
        删除记忆
        """
        try:
            self._ensure_init()
            if not self._collection:
                return False
            
            self._collection.delete(ids=[f"{user_id}_{memory_id}"])
            return True
        except Exception as e:
            logger.warning(f"删除记忆失败: {e}")
            return False
    
    def delete_user_memories(self, user_id: str) -> bool:
        """
        删除用户所有记忆
        """
        try:
            self._ensure_init()
            if not self._collection:
                return False
            
            self._collection.delete(where={"user_id": user_id})
            return True
        except Exception as e:
            logger.warning(f"删除用户记忆失败: {e}")
            return False
    
    def count_memories(self, user_id: str) -> int:
        """
        统计用户记忆数量
        """
        try:
            self._ensure_init()
            if not self._collection:
                return 0
            
            results = self._collection.get(
                where={"user_id": user_id},
                limit=1000
            )
            return len(results["ids"]) if results and results["ids"] else 0
        except Exception as e:
            logger.warning(f"统计记忆失败: {e}")
            return 0
    
    def reset(self) -> bool:
        """
        重置向量存储（危险操作）
        """
        try:
            self._ensure_init()
            if not self._client:
                return False
            
            self._client.delete_collection("memories")
            self._collection = self._client.get_or_create_collection(
                name="memories",
                metadata={"description": "用户记忆向量存储"}
            )
            return True
        except Exception as e:
            logger.warning(f"重置向量存储失败: {e}")
            return False


# 全局向量存储实例（延迟初始化，不会因 ChromaDB 问题而崩溃）
vector_store = VectorStore()
