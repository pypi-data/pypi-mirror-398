import redis


class RedisBase:
    """
    Redis基础操作基类
    提供通用的Redis连接管理功能
    """
    
    def __init__(self, host="127.0.0.1", port=6379, db=0, decode_responses=True, encoding="utf-8"):
        """
        初始化Redis连接参数
        
        Args:
            host (str): Redis服务器地址
            port (int): Redis端口
            db (int): 数据库编号
            decode_responses (bool): 是否解码响应
            encoding (str): 编码格式
        """
        self.host = host
        self.port = port
        self.db = db
        self.decode_responses = decode_responses
        self.encoding = encoding
        self._redis_client = None
    
    @property
    def redis_client(self):
        """获取Redis客户端连接，如果不存在则创建"""
        if self._redis_client is None:
            self._redis_client = redis.Redis(
                host=self.host, 
                port=self.port, 
                db=self.db, 
                decode_responses=self.decode_responses, 
                encoding=self.encoding
            )
        return self._redis_client