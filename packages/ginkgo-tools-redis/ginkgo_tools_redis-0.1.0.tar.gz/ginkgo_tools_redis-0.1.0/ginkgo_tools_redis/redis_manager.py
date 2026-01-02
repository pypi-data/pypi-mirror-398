from .redis_basic import RedisBasic
from .redis_advanced import RedisVectorOperations


class RedisManager:
    """
    Redis管理类
    整合基础Redis操作和向量数据库操作，提供统一的接口
    """
    
    def __init__(self, host="127.0.0.1", port=6379, db=0, decode_responses=True, encoding="utf-8"):
        """
        初始化Redis管理器
        
        Args:
            host (str): Redis服务器地址
            port (int): Redis端口
            db (int): 数据库编号
            decode_responses (bool): 是否解码响应
            encoding (str): 编码格式
        """
        self.basic = RedisBasic(host, port, db, decode_responses, encoding)
        self.vector = RedisVectorOperations(host, port, db, decode_responses, encoding)
    
    @property
    def redis_client(self):
        """获取Redis客户端连接（基础操作的连接）"""
        return self.basic.redis_client
    
    # 代理基础Redis操作方法
    def delete_key(self, key):
        """删除键值对"""
        return self.basic.delete_key(key)
    
    def get_keys(self, pattern="*"):
        """获取匹配模式的所有键"""
        return self.basic.get_keys(pattern)
    
    def exists(self, key):
        """检查键是否存在"""
        return self.basic.exists(key)
    
    def get(self, key):
        """获取键的值"""
        return self.basic.get(key)
    
    def set(self, key, value, ex=None):
        """设置键值对"""
        return self.basic.set(key, value, ex)
    
    def mget(self, keys):
        """批量获取多个键的值"""
        return self.basic.mget(keys)
    
    def mset(self, mapping):
        """批量设置多个键值对"""
        return self.basic.mset(mapping)

    # 代理JSON操作方法
    def set_json(self, key, value, path='$', ex=None):
        """设置JSON格式数据到Redis"""
        return self.basic.set_json(key, value, path, ex)

    def get_json(self, key, path='$'):
        """从Redis获取JSON格式数据"""
        return self.basic.get_json(key, path)

    def delete_json(self, key, path='$'):
        """删除Redis JSON数据中的指定路径"""
        return self.basic.delete_json(key, path)
    
    def expire(self, key, time):
        """设置键的过期时间"""
        return self.basic.expire(key, time)
    
    def ttl(self, key):
        """获取键的剩余生存时间"""
        return self.basic.ttl(key)
    
    def hget(self, name, key):
        """获取哈希表中指定键的值"""
        return self.basic.hget(name, key)
    
    def hset(self, name, key, value):
        """设置哈希表中指定键的值"""
        return self.basic.hset(name, key, value)
    
    def hgetall(self, name):
        """获取哈希表中所有的键值对"""
        return self.basic.hgetall(name)

    
    # 代理向量数据库操作方法
    def check_redis_index(self, indexes_name):
        """检查redis对应向量索引的数据量，是否存在异常"""
        return self.vector.check_redis_index(indexes_name)
    
    def check_reinit_index(self, indexes_name, reinit=False):
        """检查是否需要对索引进行重新初始化"""
        return self.vector.check_reinit_index(indexes_name, reinit)
    
    def create_index(self, indexes_name, prefix_list=[], vector_info={}, tag_fields=[], sortable_fields=[], reinit=False):
        """创建多功能Redis索引"""
        return self.vector.create_index(indexes_name, prefix_list, vector_info, tag_fields, sortable_fields, reinit)
    
    def common_match(self, indexes_name, tag_fields=[], sort_fields=[], top_k=10):
        """根据标签过滤和字段排序进行查询"""
        return self.vector.common_match(indexes_name, tag_fields, sort_fields, top_k)
    
    def embedding_match_with_KNN(self, indexes_name, target_embedding, tag_fields=[], top_k=5, extra_params={}):
        """使用向量数据在Redis索引中进行KNN相似性搜索"""
        return self.vector.embedding_match_with_KNN(indexes_name, target_embedding, tag_fields, top_k, extra_params)
    
    def embedding_match_with_range(self, indexes_name, target_embedding, radius=0.2, tag_fields=[], extra_params={}):
        """使用向量数据在Redis索引中进行范围相似性搜索"""
        return self.vector.embedding_match_with_range(indexes_name, target_embedding, radius, tag_fields, extra_params)
    
    def embedding_match_multi(self, indexes_name_list, target_embedding, tag_fields=[], top_k=5, extra_params={}):
        """多索引向量匹配"""
        return self.vector.embedding_match_multi(indexes_name_list, target_embedding, tag_fields, top_k, extra_params)
    
    def embedding_match_multi_embedding(self, index_name, target_embedding_list, tag_fields=[], top_k=5, subtop_k=10, extra_params={}, mode="Union"):
        """多向量匹配"""
        return self.vector.embedding_match_multi_embedding(index_name, target_embedding_list, tag_fields, top_k, subtop_k, extra_params, mode)