# GINKGO-TOOLS-REDIS

对 Redis 进行再封装的工具库，简化了常规的 Redis 操作和向量操作，便于使用。

## 功能特性

- **Redis 向量数据库操作**：支持向量索引创建、KNN 相似性搜索、范围搜索
- **标签过滤查询**：支持基于标签的查询功能
- **模块化架构**：基于 [RedisManager](file://D:\Python_Project\#工具脚本\GINKGO-TOOLS-REDIS\redis_ops.py#L5-L23) 的封装设计
- **向后兼容**：保持与旧版 API 的兼容性
- **简化操作**：提供简化的 Redis 操作接口

## 安装

```bash
pip install ginkgo-tools-redis
```

## 快速开始

```python
from ginkgo_tools_redis import RedisOps

# 创建 Redis 连接实例
redis_ops = RedisOps(host="127.0.0.1", port=6379, db=0)

# 使用向量数据库功能
# 示例：创建向量索引、执行 KNN 搜索等
```

## API 说明

### RedisOps 类

[RedisOps](file://D:\Python_Project\#工具脚本\GINKGO-TOOLS-REDIS\redis_ops.py#L5-L23) 类继承自 [RedisManager](file://D:\Python_Project\#工具脚本\GINKGO-TOOLS-REDIS\redis_manager.py#L4-L123)，提供以下功能：

- 向量索引创建
- 标签过滤查询
- KNN 相似性搜索
- 范围搜索
- 保持与旧版 API 的兼容性

## 依赖

- `ginkgo-tools>=0.1.4`
- `redis[hiredis]==5.0.1`
- Python >= 3.11

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request 来改进此项目。