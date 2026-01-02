import redis
from ginkgo_tools.tools_log import *
from .redis_base import RedisBase


class RedisBasic(RedisBase):
    """
    基础Redis操作类
    提供键值对操作、字符串操作、列表操作等基础功能
    """
    
    def __init__(self, host="127.0.0.1", port=6379, db=0, decode_responses=True, encoding="utf-8"):
        """
        初始化Redis连接
        
        Args:
            host (str): Redis服务器地址
            port (int): Redis端口
            db (int): 数据库编号
            decode_responses (bool): 是否解码响应
            encoding (str): 编码格式
        """
        super().__init__(host, port, db, decode_responses, encoding)
    
    
    def delete_key(self, key):
        """
        删除键值对
        
        Args:
            key (str): 要删除的键
        """
        return self.redis_client.delete(key)
    
    def get_keys(self, pattern="*"):
        """
        获取匹配模式的所有键
        
        Args:
            pattern (str): 键名模式，默认为"*"匹配所有键
            
        Returns:
            list: 匹配的键列表
        """
        return self.redis_client.keys(pattern)
    
    def exists(self, key):
        """
        检查键是否存在
        
        Args:
            key (str): 要检查的键
            
        Returns:
            bool: 键是否存在
        """
        return bool(self.redis_client.exists(key))
    
    def get(self, key):
        """
        获取键的值
        
        Args:
            key (str): 要获取的键
            
        Returns:
            str or None: 键的值，如果键不存在返回None
        """
        return self.redis_client.get(key)
    
    def set(self, key, value, ex=None):
        """
        设置键值对
        
        Args:
            key (str): 键名
            value (str): 键值
            ex (int, optional): 过期时间（秒）
        """
        return self.redis_client.set(key, value, ex=ex)
    
    def set_json(self, key, path, value, ex=None):
        """
        设置JSON格式数据到Redis
        
        Args:
            key (str): 键名
            value (any): JSON序列化的值（字典、列表等）
            path (str): JSON路径，默认为'$'（根路径）
            ex (int, optional): 过期时间（秒）
        """
        result = self.redis_client.json().set(key, path, value)
        if ex:
            self.redis_client.expire(key, ex)
        return result
    
    def get_json(self, key, path='$'):
        """
        从Redis获取JSON格式数据
        
        Args:
            key (str): 键名
            path (str): JSON路径，默认为'$'（根路径）
            
        Returns:
            any: JSON数据（字典、列表等），如果键不存在返回None
        """
        return self.redis_client.json().get(key, path)
    
    def delete_json(self, key, path='$'):
        """
        删除Redis JSON数据中的指定路径
        
        Args:
            key (str): 键名
            path (str): JSON路径，默认为'$'（根路径）
            
        Returns:
            int: 删除的元素数量
        """
        return self.redis_client.json().delete(key, path)
    
    
    def mget(self, keys):
        """
        批量获取多个键的值
        
        Args:
            keys (list): 键名列表
            
        Returns:
            list: 对应键的值列表
        """
        return self.redis_client.mget(keys)
    
    def mset(self, mapping):
        """
        批量设置多个键值对
        
        Args:
            mapping (dict): 键值对字典
        """
        return self.redis_client.mset(mapping)
    
    def expire(self, key, time):
        """
        设置键的过期时间
        
        Args:
            key (str): 键名
            time (int): 过期时间（秒）
        """
        return self.redis_client.expire(key, time)
    
    def ttl(self, key):
        """
        获取键的剩余生存时间
        
        Args:
            key (str): 键名
            
        Returns:
            int: 剩余生存时间（秒），-1表示永不过期，-2表示键不存在
        """
        return self.redis_client.ttl(key)
    
    def hget(self, name, key):
        """
        获取哈希表中指定键的值
        
        Args:
            name (str): 哈希表名
            key (str): 哈希表中的键
            
        Returns:
            str: 键对应的值
        """
        return self.redis_client.hget(name, key)
    
    def hset(self, name, key, value):
        """
        设置哈希表中指定键的值
        
        Args:
            name (str): 哈希表名
            key (str): 哈希表中的键
            value (str): 值
        """
        return self.redis_client.hset(name, key, value)
    
    def hgetall(self, name):
        """
        获取哈希表中所有的键值对
        
        Args:
            name (str): 哈希表名
            
        Returns:
            dict: 所有键值对
        """
        return self.redis_client.hgetall(name)