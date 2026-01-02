"""新版本的RedisVectorDB，使用模块化架构"""

from .redis_manager import RedisManager


class RedisOps(RedisManager):
    """
    Redis向量数据库管理类（向后兼容）
    提供向量索引创建、标签过滤查询、KNN相似性搜索、范围搜索等功能
    这个类是对RedisManager的封装，保持与旧版API的兼容性
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