import redis
import hashlib
from redis.commands.search.field import VectorField, NumericField, TextField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query
from redis.commands.search.field import TagField

import time
from ginkgo_tools.tools_log import *
from .redis_base import RedisBase


class RedisVectorOperations(RedisBase):
    """
    Redis向量数据库操作类
    专门处理向量索引创建、标签过滤查询、KNN相似性搜索、范围搜索等功能
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
    
    def check_redis_index(self, indexes_name):
        """
        检查redis对应向量索引的数据量，是否存在异常
        
        Args:
            indexes_name (str): 索引名称
            
        Returns:
            bool or int: 存在索引返回True，不存在返回0，异常抛出异常
        """
        try:
            info = self.redis_client.ft(indexes_name).info()
            num_docs = info["num_docs"]
            indexing_failures = info["hash_indexing_failures"]
            console_log_debug(f"{num_docs} documents indexed with {indexing_failures} failures")
            if indexing_failures > 0:
                raise Exception("存在indexing failures")
            else:
                return True
        except redis.exceptions.ResponseError as e:
            if "Unknown index name" in str(e):
                console_log_debug("check_redis_embedding:", "no such index")
                return 0
            else:
                raise e

    def check_reinit_index(self, indexes_name, reinit=False):
        """
        检查是否需要对索引进行重新初始化
        包括索引删除能力，返回值是布尔值，指示调用函数是否要进行索引初始化
        
        Args:
            indexes_name (str): 索引名称
            reinit (bool): 是否重新初始化索引
            
        Returns:
            bool: 是否需要初始化索引
        """
        do_delete = False
        do_init = False
        # 加一个判断，该redis是否已经完成schema和索引的创建
        if self.check_redis_index(indexes_name):
            if reinit:  # 如果参数指定，则删除索引重新初始化
                do_delete = True
                do_init = True
                console_log_debug(f"已存在索引，该索引将被删除重新初始化：{indexes_name}")
            else:
                console_log_debug(f"索引已存在，按参数控制将不再初始化：{indexes_name}")
        else:
            do_init = True

        if do_delete:
            # schema是一个概念，索引删除即可，与该索引相关的Schema配置也会一并删除
            self.redis_client.ft(indexes_name).dropindex(delete_documents=True)  # 参数指定关联文档也删除
        return do_init

    def create_index(self, indexes_name, prefix_list=[], vector_info={}, tag_fields=[], sortable_fields=[], reinit=False):
        """
        创建多功能Redis索引，支持向量字段、标签字段和可排序字段
        需要注意的是！！！！
            唯一写死的东西在于向量路径和别名，路径写死为$.embedding，别名写死为embedding_data

        Args:
            indexes_name (str): 索引名称
            prefix_list (list): 索引前缀匹配列表，如["ImageEmbedding-","VideoEmbedding-"]
            vector_info (dict): 向量字段配置信息，包含以下键值:
                - "DIM_embedding_dimension": 向量维度
                - "embedding_type": 数据类型，如"FLOAT32"
                - "DISTANCE_METRIC": 距离度量方式，如"COSINE"
            tag_fields (list): 标签字段列表，每个元素为包含以下键的字典:
                - "field_path": JSON路径，如"$.classify_name"
                - "field_name": 字段别名，如"classify_name"
            sortable_fields (list): 可排序字段列表，每个元素为包含以下键的字典:
                - "field_path": JSON路径，如"$.face_score_info.quality_score"
                - "field_name": 字段别名，如"quality_score"
                - "field_type": 字段类型，可选"numeric"/"tag"/"text"
            reinit (bool): 是否重新初始化索引，默认False

        Example:
            redis_vector_ops = RedisVectorOperations()
            redis_vector_ops.create_index(
                indexes_name="idx:face_index",
                prefix_list=["FaceEmbedding-"],
                vector_info={
                    "DIM_embedding_dimension": 512,
                    "embedding_type": "FLOAT32",
                    "DISTANCE_METRIC": "COSINE"
                },
                tag_fields=[
                    {"field_path": "$.classify_name", "field_name": "classify_name"}
                ],
                sortable_fields=[
                    {"field_path": "$.face_score_info.quality_score", "field_name": "quality_score", "field_type": "numeric"}
                ]
            )
        """
        do_init = self.check_reinit_index(indexes_name, reinit)
        if not do_init:
            return True

        # 定义向量数据库的 Schema
        # schema可以看成就是一个命令列表，各种类型的部分可以分开丢进去，不分顺序
        schema = []

        # 创建向量字段部分
        if vector_info:
            vectorfield_params = VectorField(
                "$.embedding",  # 数据源，修改为指向JSON中embedding数据的路径
                "FLAT",
                {
                    "TYPE": vector_info["embedding_type"],  # 数据类型
                    "DIM": vector_info["DIM_embedding_dimension"],  # 向量维度
                    "DISTANCE_METRIC": vector_info["DISTANCE_METRIC"],  # 距离度量方式
                },
                as_name="embedding_data",  # 定义字段别名
            )
            schema.append(vectorfield_params)

        # 添加标签字段
        # 这里分隔符使用| 传入的值还是字符串，其中若有|，则认为是不同的tag，如"tag1|tag2"
        for tag_info in tag_fields:
            field_path = tag_info["field_path"]  # 如 $.field_path
            field_name = tag_info["field_name"]  # 如 field_name
            schema.append(TagField(field_path, as_name=field_name, separator="|"))

        # 添加可排序字段
        for field_info in sortable_fields:
            field_path = field_info["field_path"]  # 如 $.field_path
            field_name = field_info["field_name"]  # 如 field_name
            field_type = field_info["field_type"]  # 对于几大类型，包括数字，标签，文本等

            if field_type == "numeric":
                schema.append(NumericField(field_path, as_name=field_name, sortable=True))
            elif field_type == "tag":
                schema.append(TagField(field_path, as_name=field_name, sortable=True))
            elif field_type == "text":
                schema.append(TextField(field_path, as_name=field_name, sortable=True))

        # 定义索引对象
        # 索引采集数据源这里通过正则匹配，匹配特殊开头的key
        # 只要key符合了索引定义的prefix，且类型为json，就会被索引匹配
        definition = IndexDefinition(prefix=prefix_list, index_type=IndexType.JSON)

        # 使用 Redis 客户端实例根据上面的 Schema 和定义创建索引
        res = self.redis_client.ft(indexes_name).create_index(
            fields=schema, definition=definition
        )
        console_log_debug(f"创建索引完成:{indexes_name}", res)
        return res

    def _build_tag_filter(self, tag_fields=[]):
        """
        构建Redis查询的标签过滤条件
        
        Args:
            tag_fields (list): 标签过滤条件列表，每个元素为包含'field_name'和'field_value'键的字典
                              可选的'exclude'键用于指定是否排除该条件
                              例如: [
                                  {"field_name": "classify_name", "field_value": "person1"},
                                  {"field_name": "from_src", "field_value": "exclude_source", "exclude": True}
                              ]
        
        Returns:
            str: 构建好的过滤条件字符串
        """
        if len(tag_fields) == 0:
            return "*"
        else:
            # 构建标签过滤条件
            tag_conditions = []
            for tag_dict in tag_fields:
                field_name = tag_dict["field_name"]
                field_value = tag_dict.get("field_value", "")
                field_values = tag_dict.get("field_values", [])
                exclude = tag_dict.get("exclude", False)

                # 允许对一个tag查询多个值，多个值之间是或关系，多个tag之间是且关系
                # 这里同时支持单个tag和tag列表查询
                if field_value:
                    field_values.append(field_value)
                field_value_fin = " | ".join(field_values)

                # 查询时对输入值要求很高，禁止出现特殊符号
                # 特殊符号需要用\进行转义，如"图片-1.jpg"转义为"图片\-1\.jpg"
                # \ 和 | 特殊，|本来就用作与符号，\自身就是转义符，就忽略了，不然太麻烦
                special_chars = [
                    '-', ',', '.', '!', '@', '#', '$', '%', '^', '&', '*',
                    '(', ')', '+', '=', '{', '}', '[', ']', ':', ';', '"',
                    "'", '<', '>', '?', '/', '~', '`'
                ]
                for char in special_chars:
                    field_value_fin = field_value_fin.replace(char, f"\{char}")

                # 构建标签过滤条件query语句
                if exclude:
                    # 排除条件，使用负号前缀
                    tag_conditions.append(f"-@{field_name}:{{{field_value_fin}}}")
                else:
                    # 包含条件
                    tag_conditions.append(f"@{field_name}:{{{field_value_fin}}}")

            # 使用 AND 连接多个条件
            if len(tag_conditions) == 1:
                query_condition = tag_conditions[0]
            else:
                query_condition = " AND ".join(tag_conditions)
            return query_condition

    def common_match(self, indexes_name, tag_fields=[], sort_fields=[], top_k=10):
        """
        根据标签过滤和字段排序进行查询

        Args:
            indexes_name (str): 索引名称
            tag_fields (list): 标签过滤条件列表，每个元素为包含'field_name'和'field_value'键的字典
                              例如: [{"field_name": "classify_name", "field_value": "person1"}]
            sort_fields (list): 排序字段列表，每个元素为包含'field_name'和'sort_asc'键的字典
                               例如: [{"field_name": "quality_score", "sort_asc": False}]
                               asc = False为降序，True为升序（包括字母a-z）
            top_k (int): 返回结果数量

        Returns:
            list: 查询结果文档列表
        """
        # 构建标签过滤条件
        tag_filter_sql = self._build_tag_filter(tag_fields)

        # 构建查询query语句
        query = Query(tag_filter_sql)

        # 添加字段排序排序
        if sort_fields:
            for sort_dict in sort_fields:
                query = query.sort_by(field=sort_dict.get("field_name"), asc=sort_dict.get("sort_asc", False))

        # 限制返回结果数量
        query = query.paging(0, top_k)

        # 执行查询
        result_docs = self.redis_client.ft(indexes_name).search(query).docs

        return result_docs

    def embedding_match_with_KNN(self, indexes_name, target_embedding, tag_fields=[], top_k=5, extra_params={}):
        """
        使用向量数据在Redis索引中进行KNN相似性搜索

        Args:
            indexes_name (str): 索引名称
            target_embedding (bytes): 目标向量数据（需要是tobytes()处理后的二进制数据）
            tag_fields (list): 标签过滤条件列表，每个元素为包含'field_name'和'field_value'键的字典
                              例如: [{"field_name": "classify_name", "field_value": "person1"}]
            top_k (int): 返回最相似的K个结果
            extra_params (dict): 额外的查询参数

        Returns:
            list: 包含匹配结果的文档列表，每个文档包含以下属性：
                - id: Redis键名
                - match_distance: 余弦距离（越小越相似）
                - json: 完整的JSON文档内容
                - cos_distance: 余弦距离（数值）
                - similarity_cos: 余弦相似度（数值，1-余弦距离）
        """
        start_time = time.time()

        tag_filter_sql = self._build_tag_filter(tag_fields)

        # 定义查询query语句
        # Query(f"(*)=>[KNN {top_k} @embedding_data $query_embedding AS match_distance]") 匹配全部文档
        # Query(f"(@type:{{{type}}})=>[KNN {top_k} @embedding_data $query_embedding AS match_distance]") 匹配指定类型的文档
        query = Query(f"({tag_filter_sql})=>[KNN {top_k} @embedding_data $query_embedding AS match_distance]")

        query.sort_by("match_distance")  # 按距离排序
        query.return_fields("match_distance", "$")  # 指定返回这个距离字段+完整JSON文档
        query.dialect(2)  # 使用查询语法版本2
        query.paging(0, top_k)  # 设置返回结果数量

        # 执行查询
        # 绑定查询向量，query_embedding是查询语句中的占位符，这里把查询向量数据绑定到占位符中
        result_docs = self.redis_client.ft(indexes_name).search(
            query,
            {"query_embedding": target_embedding} | extra_params,
        ).docs

        # 处理返回的文档，添加距离和相似度字段
        for doc in result_docs:
            cos_distance = float(doc['match_distance'])  # 因为是KNN匹配和cos计算，这里的返回值的意义是余弦距离，越小越相似
            similarity = 1 - cos_distance  # 转换为余弦相似度
            # 更新doc的字段
            doc.cos_distance = cos_distance
            doc.similarity_cos = similarity

        return result_docs

    def embedding_match_with_range(self, indexes_name, target_embedding, radius=0.2, tag_fields=[], extra_params={}):
        """
        使用向量数据在Redis索引中进行范围相似性搜索

        Args:
            indexes_name (str): 索引名称
            target_embedding (bytes): 目标向量数据（需要是tobytes()处理后的二进制数据）
            radius (float): 搜索半径（余弦距离），返回此距离内的所有向量
            tag_fields (list): 标签过滤条件列表，每个元素为包含'field_name'和'field_value'键的字典
                              例如: [{"field_name": "classify_name", "field_value": "person1"}]
            extra_params (dict): 额外的查询参数

        Returns:
            list: 包含匹配结果的文档列表，每个文档包含以下属性：
                - id: Redis键名
                - match_distance: 余弦距离（越小越相似）
                - json: 完整的JSON文档内容
                - cos_distance: 余弦距离（数值）
                - similarity_cos: 余弦相似度（数值，1-余弦距离）
        """
        start_time = time.time()

        tag_filter_sql = self._build_tag_filter(tag_fields)

        # 定义范围查询语句
        # 使用VECTOR_RANGE语法进行范围查询
        if tag_fields:
            query = Query(f"({tag_filter_sql}) @embedding_data:[VECTOR_RANGE {radius} $query_embedding]=>{{$YIELD_DISTANCE_AS: match_distance}}")
        else:
            query = Query(f"@embedding_data:[VECTOR_RANGE {radius} $query_embedding]=>{{$YIELD_DISTANCE_AS: match_distance}}")
        query.return_fields("match_distance", "$")  # 指定返回距离字段+完整JSON文档
        query.dialect(2)  # 使用查询语法版本2

        # 执行查询
        result_docs = self.redis_client.ft(indexes_name).search(
            query,
            {"query_embedding": target_embedding} | extra_params,
        ).docs

        # 处理返回的文档，添加距离和相似度字段
        for doc in result_docs:
            cos_distance = float(doc['match_distance'])  # 余弦距离，越小越相似
            similarity = 1 - cos_distance  # 转换为余弦相似度
            # 更新doc的字段
            doc.cos_distance = cos_distance
            doc.similarity_cos = similarity

        return result_docs

    def embedding_match_multi(self, indexes_name_list, target_embedding, tag_fields=[], top_k=5, extra_params={}):
        """
        多索引向量匹配
        
        Args:
            indexes_name_list (list): 索引名称列表
            target_embedding (bytes): 目标向量数据
            tag_fields (list): 标签过滤条件列表
            top_k (int): 返回结果数量
            extra_params (dict): 额外参数
            
        Returns:
            list: 匹配结果
        """
        all_result_docs = []
        fin_results_dict = dict()
        # 调用索引匹配函数
        for index_name in indexes_name_list:
            result_docs = self.embedding_match_with_KNN(
                indexes_name=index_name,
                target_embedding=target_embedding,
                tag_fields=tag_fields,
                top_k=top_k,
                extra_params=extra_params
            )
            all_result_docs.extend(result_docs)
        sorted_results = sorted(
            all_result_docs,
            key=lambda doc: doc.cos_distance,
        )
        for doc in sorted_results:
            if len(fin_results_dict) > top_k:
                break
            if doc.id not in fin_results_dict:
                fin_results_dict[doc.id] = doc

        return list(fin_results_dict.values())

    def embedding_match_multi_embedding(self, index_name, target_embedding_list, tag_fields=[], top_k=5, subtop_k=10, extra_params={}, mode="Union"):
        """
        多向量匹配
        
        Args:
            index_name (str): 索引名称
            target_embedding_list (list): 目标向量列表
            tag_fields (list): 标签过滤条件列表
            top_k (int): 返回结果数量
            subtop_k (int): 子查询返回数量
            extra_params (dict): 额外参数
            mode (str): 匹配模式，"Union"并集或"Intersection"交集
            
        Returns:
            list: 匹配结果
        """
        all_result_docs = []
        fin_results_dict = dict()
        # 调用索引匹配函数
        for target_embedding in target_embedding_list:
            result_docs = self.embedding_match_with_KNN(
                indexes_name=index_name,
                target_embedding=target_embedding,
                tag_fields=tag_fields,
                top_k=subtop_k,
                extra_params=extra_params
            )
            all_result_docs.extend(result_docs)

        # 根据模式处理结果
        if mode.lower() == "union":
            # 并集操作：合并所有结果，去重并取最高分
            for doc in all_result_docs:
                if doc.id not in fin_results_dict:
                    fin_results_dict[doc.id] = doc
                else:
                    # 如果已存在，保留分数更好的结果（余弦距离更小的）
                    if doc.cos_distance < fin_results_dict[doc.id].cos_distance:
                        fin_results_dict[doc.id] = doc
        elif mode.lower() == "intersection":
            # 交集操作：只保留出现在所有查询结果中的文档
            doc_count = {}
            for doc in all_result_docs:
                doc_count[doc.id] = doc_count.get(doc.id, 0) + 1

            required_count = len(target_embedding_list)
            for doc in all_result_docs:
                if doc_count[doc.id] == required_count:
                    # 这里仍然保留最好的分数
                    if doc.id not in fin_results_dict:
                        fin_results_dict[doc.id] = doc
                    else:
                        if doc.cos_distance < fin_results_dict[doc.id].cos_distance:
                            fin_results_dict[doc.id] = doc

        # 按照相似度排序并返回前top_k个结果
        sorted_results = sorted(
            fin_results_dict.values(),
            key=lambda doc: doc.cos_distance,
        )

        # 只返回前top_k个结果
        final_results = sorted_results[:top_k]

        return final_results