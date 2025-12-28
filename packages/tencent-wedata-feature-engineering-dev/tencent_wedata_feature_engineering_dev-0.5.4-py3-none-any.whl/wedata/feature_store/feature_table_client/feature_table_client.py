"""
特征表操作相关工具方法
"""
import json
from typing import Union, List, Dict, Optional, Sequence, Any

import tencentcloud.common.exception
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.streaming import StreamingQuery
from pyspark.sql.types import StructType
import os
import datetime
from wedata.feature_store.constants.constants import (
    APPEND, DEFAULT_WRITE_STREAM_TRIGGER, FEATURE_TABLE_KEY,
    FEATURE_TABLE_VALUE, FEATURE_TABLE_PROJECT, FEATURE_TABLE_TIMESTAMP,
    FEATURE_TABLE_BACKUP_PRIMARY_KEY, FEATURE_DLC_TABLE_PRIMARY_KEY)
from wedata.feature_store.constants.engine_types import EngineTypes
from wedata.feature_store.common.log.logger import get_logger
from wedata.feature_store.common.store_config.redis import RedisStoreConfig
from wedata.feature_store.entities.feature_table import FeatureTable
from wedata.feature_store.spark_client.spark_client import SparkClient
from wedata.feature_store.utils import common_utils, env_utils
from wedata.feature_store.feast_client.feast_client import FeastClient
from wedata.feature_store.cloud_sdk_client import models
from wedata.feature_store.cloud_sdk_client.client import FeatureCloudSDK


class FeatureTableClient:
    """特征表操作类"""

    def __init__(
            self,
            spark: SparkSession,
            cloud_secret_id: str = None,
            cloud_secret_key: str = None,
    ):
        self._spark = spark
        self.__cloud_tmp_token = None
        self._feast_client = FeastClient(spark)
        self.__logger = get_logger()
        if cloud_secret_id and cloud_secret_key:
            self.__logger.info(f"FeatureTableClient start init with cloud_secret_id and cloud_secret_key")
            self.__cloud_secret_id = cloud_secret_id
            self.__cloud_secret_key = cloud_secret_key
            self.__logger.info(f"FeatureTableClient cloud_secret_id: {self.__cloud_secret_id}")
            self.__logger.info(f"FeatureTableClient cloud_secret_key: {self.__cloud_secret_key}")
        else:
            self.__logger.info(f"FeatureTableClient start init with env_utils")
            self.__cloud_secret_id, self.__cloud_secret_key = env_utils.get_cloud_secret()
            self.__logger.info(f"FeatureTableClient start init with cloud_secret_id: {self.__cloud_secret_id}")
            self.__logger.info(f"FeatureTableClient start init with cloud_secret_key: {self.__cloud_secret_key}")
            # 获取临时token
            if not self.__cloud_secret_id or not self.__cloud_secret_key:
                self.__logger.info(f"FeatureTableClient start init with temp_secret")
                self.__cloud_secret_id, self.__cloud_secret_key, self.__cloud_tmp_token = env_utils.get_temp_secret()
                self.__logger.info(f"FeatureTableClient start init with cloud_tmp_token: {self.__cloud_tmp_token}")
                self.__logger.info(f"FeatureTableClient start init with cloud_tmp_secret_id: {self.__cloud_secret_id}")
                self.__logger.info(f"FeatureTableClient start init with cloud_tmp_secret_key: {self.__cloud_secret_key}")
        self.__project = env_utils.get_project_id()
        self.__region = env_utils.get_region()

        self.__logger.info(f"FeatureTableClient start init")
        default_online_table = self._get_offline_default_database()
        if default_online_table:
            env_utils.set_default_database(default_online_table.DatabaseName)


    @property
    def cloud_secret_id(self) -> str:
        if not self.__cloud_secret_id:
            raise ValueError("cloud_secret_id is empty. please set it first.")
        return self.__cloud_secret_id

    @cloud_secret_id.setter
    def cloud_secret_id(self, cloud_secret_id: str):
        if not cloud_secret_id:
            raise ValueError("cloud_secret_id cannot be None")
        self.__cloud_secret_id = cloud_secret_id

    @property
    def cloud_secret_key(self) -> str:
        if not self.__cloud_secret_key:
            raise ValueError("cloud_secret_key is empty. please set it first.")
        return self.__cloud_secret_key

    @cloud_secret_key.setter
    def cloud_secret_key(self, cloud_secret_key: str):
        if not cloud_secret_key:
            raise ValueError("cloud_secret_key cannot be None")
        self.__cloud_secret_key = cloud_secret_key

    @property
    def project(self) -> str:
        return self.__project

    @property
    def region(self) -> str:
        return self.__region

    @staticmethod
    def _normalize_params(
            param: Optional[Union[str, Sequence[str]]],
            default_type: type = list
    ) -> list:
        """统一处理参数标准化"""
        if param is None:
            return default_type()
        return list(param) if isinstance(param, Sequence) else [param]

    @staticmethod
    def _validate_schema(df: DataFrame, schema: StructType):
        """校验DataFrame和schema的有效性和一致性"""
        # 检查是否同时为空
        if df is None and schema is None:
            raise ValueError("Either DataFrame or schema must be provided")

        # 检查schema匹配
        if df is not None and schema is not None:
            df_schema = df.schema
            if df_schema != schema:
                diff_fields = set(df_schema.fieldNames()).symmetric_difference(set(schema.fieldNames()))
                raise ValueError(
                    f"DataFrame schema does not match. Differences: "
                    f"{diff_fields if diff_fields else 'field type mismatch'}"
                )

    @staticmethod
    def _validate_key_conflicts(primary_keys: List[str], timestamp_keys: str):
        """校验主键与时间戳键是否冲突"""
        if timestamp_keys in primary_keys:
            raise ValueError(f"Timestamp keys conflict with primary keys: {timestamp_keys}")

    @staticmethod
    def _validate_key_exists(primary_keys: List[str], timestamp_keys: str):
        """校验主键与时间戳键是否存在"""
        if not primary_keys:
            raise ValueError("Primary keys cannot be empty")
        if not timestamp_keys:
            raise ValueError("Timestamp keys cannot be empty")

    @staticmethod
    def _escape_sql_value(value: str) -> str:
        """转义SQL值中的特殊字符"""
        return value.replace("'", "''")

    @staticmethod
    def _check_sequence_element_type(sequence: Sequence[Any], element_type: type) -> bool:
        """检查序列中的元素是否为指定类型"""
        return all(isinstance(element, element_type) for element in sequence)

    def create_table(
            self,
            name: str,
            primary_keys: Union[str, List[str]],
            timestamp_key: str,
            engine_type: EngineTypes,
            data_source_name: str,
            database_name: Optional[str] = None,
            df: Optional[DataFrame] = None,
            *,
            partition_columns: Union[str, List[str], None] = None,
            schema: Optional[StructType] = None,
            description: Optional[str] = None,
            tags: Optional[Dict[str, str]] = None,
            catalog_name: Optional[str] = None
    ) -> FeatureTable:

        """
        创建特征表（支持批流数据写入）

        Args:
            name: 特征表全称（格式：<table>）
            primary_keys: 主键列名（支持复合主键）
            database_name: Optional[str] = None,
            data_source_name: 数据源名称,
            df: 初始数据（可选，用于推断schema）
            timestamp_key: 时间戳键（用于时态特征）
            engine_type: 引擎类型   version:: 1.33
            partition_columns: 分区列（优化存储查询）
            schema: 表结构定义（可选，当不提供df时必需）
            description: 业务描述
            tags: 业务标签
            catalog_name: catalog name
        Returns:
            FeatureTable实例

        Raises:
            ValueError: 当schema与数据不匹配时
        """

        # 参数标准化
        primary_keys = self._normalize_params(primary_keys)
        partition_columns = self._normalize_params(partition_columns)

        assert self._check_sequence_element_type(primary_keys, str), "primary_keys must be a list of strings"
        assert self._check_sequence_element_type(partition_columns, str), "partition_columns must be a list of strings"
        assert isinstance(timestamp_key, str), "timestamp key must be string"

        # 元数据校验
        self._validate_schema(df, schema)
        self._validate_key_exists(primary_keys, timestamp_key)
        self._validate_key_conflicts(primary_keys, timestamp_key)

        # 表名校验
        common_utils.validate_table_name(name)

        common_utils.validate_database(database_name)

        # 校验PrimaryKey是否有重复
        dup_list = common_utils.get_duplicates(primary_keys)
        if dup_list :
            raise ValueError(f"Primary keys have duplicates: {dup_list}")

        # 构建完整表名
        table_name = common_utils.build_full_table_name(name, database_name, catalog_name)

        # 检查表是否存在
        try:
            if self._check_table_exists(table_name):
                raise ValueError(
                    f"Table '{name}' already exists\n"
                    "Solutions:\n"
                    "1. Use a different table name\n"
                    "2. Drop the existing table: spark.sql(f'DROP TABLE {name}')\n"
                )
        except Exception as e:
            raise ValueError(f"Error checking table existence: {str(e)}") from e

        try:
            self._sync_table_info(table_name=name, action_name="create",
                                  database_name=env_utils.get_database_name(database_name),
                                  data_source_name=data_source_name, engine_name=env_utils.get_engine_name(),
                                  is_try=True)
        except tencentcloud.common.exception.TencentCloudSDKException as e:
            raise RuntimeError(f"Table '{name}' is can't create. {str(e)}")

        # 推断表schema
        table_schema = schema or df.schema

        # 构建时间戳键属性

        # 从环境变量获取额外标签
        env_tags = {
            "project_id": os.getenv("WEDATA_PROJECT_ID", ""),  # wedata项目ID
            "engine_name": os.getenv("WEDATA_NOTEBOOK_ENGINE", ""),  # wedata引擎名称
            "user_uin": os.getenv("KERNEL_LOGIN_UIN", "")  # wedata用户UIN
        }
        projectId = os.getenv("WEDATA_PROJECT_ID", "")
        # 构建表属性（通过TBLPROPERTIES）
        tbl_properties = {
            "wedata.feature_table": "true",
            FEATURE_TABLE_BACKUP_PRIMARY_KEY: ",".join(primary_keys),
            "wedata.feature_project_id": f"{json.dumps([projectId])}",
            FEATURE_TABLE_TIMESTAMP: timestamp_key,
            "comment": description or "",
            **{f"{k}": v for k, v in (tags or {}).items()},
            **{f"feature_{k}": v for k, v in (env_tags or {}).items()}
        }
        if engine_type == EngineTypes.ICEBERG_ENGINE:
            if partition_columns:
                tbl_properties.update({
                    'format-version': '2',
                    'write.upsert.enabled': 'true',
                    'write.update.mode': 'merge-on-read',
                    'write.merge.mode': 'merge-on-read',
                    'write.parquet.bloom-filter-enabled.column.id': 'true',
                    'dlc.ao.data.govern.sorted.keys': ",".join(primary_keys),
                    #'write.distribution-mode': 'hash',
                    'write.metadata.delete-after-commit.enabled': 'true',
                    'write.metadata.previous-versions-max': '100',
                    'write.metadata.metrics.default': 'full',
                    'smart-optimizer.inherit': 'default',
                })
            else:
                tbl_properties.update({
                    'format-version': '2',
                    'write.upsert.enabled': 'true',
                    'write.update.mode': 'merge-on-read',
                    'write.merge.mode': 'merge-on-read',
                    'write.parquet.bloom-filter-enabled.column.id': 'true',
                    'dlc.ao.data.govern.sorted.keys': ",".join(primary_keys),
                    #'write.distribution-mode': 'hash',
                    'write.metadata.delete-after-commit.enabled': 'true',
                    'write.metadata.previous-versions-max': '100',
                    'write.metadata.metrics.default': 'full',
                    'smart-optimizer.inherit': 'default',
                })

        # 构建列定义
        columns_ddl = []
        for field in table_schema.fields:
            data_type = field.dataType.simpleString().upper()
            col_def = f"`{field.name}` {data_type}"
            if not field.nullable:
                col_def += " NOT NULL"
            # 添加字段注释(如果metadata中有comment)
            if field.metadata and "comment" in field.metadata:
                comment = self._escape_sql_value(field.metadata["comment"])
                col_def += f" COMMENT '{comment}'"
            columns_ddl.append(col_def)

        # 构建分区表达式
        partition_expr = (
            f"PARTITIONED BY ({', '.join([f'`{c}`' for c in partition_columns])})"
            if partition_columns else ""
        )
        # 本地调试 iceberg --》PARQUET
        # 核心建表语句
        if engine_type == EngineTypes.ICEBERG_ENGINE:
            ddl = f"""
        CREATE TABLE {table_name} (
            {', '.join(columns_ddl)}
        )
        USING iceberg
        {partition_expr}
        TBLPROPERTIES (
            {', '.join(f"'{k}'='{self._escape_sql_value(v)}'" for k, v in tbl_properties.items())}
        )
            """
        elif engine_type == EngineTypes.HIVE_ENGINE:
            ddl = f"""
            CREATE TABLE {table_name} (
        {', '.join(columns_ddl)}
    )
    {partition_expr}
--     STORED AS PARQUET
    TBLPROPERTIES (
        {', '.join(f"'{k}'='{self._escape_sql_value(v)}'" for k, v in tbl_properties.items())}
    )
            """
        else:
            raise ValueError(f"Engine type {engine_type} is not supported")

        # 打印sql
        self.__logger.info(f"create table ddl: {ddl}\n")

        # 执行DDL
        try:
            self._spark.sql(ddl)
            if df is not None:
                df.write.insertInto(table_name)
        except Exception as e:
            raise ValueError(f"Failed to create table: {str(e)}") from e

        self._feast_client.create_table(
            table_name=table_name,
            primary_keys=primary_keys,
            timestamp_key=timestamp_key,
            df=df,
            schema=table_schema,
            tags=tags,
            description=description
        )

        self.__logger.info(f"Table '{name}' created successfully. Starting web synchronization.")

        try:
            self._sync_table_info(table_name=name, action_name="create",
                                  database_name=env_utils.get_database_name(database_name),
                                  data_source_name=data_source_name, engine_name=env_utils.get_engine_name(),
                                  is_try=False)
        except tencentcloud.common.exception.TencentCloudSDKException as e:
            raise RuntimeError(f"Failed to synchronize web data for table '{name}'. "
                               f"Please manually operate on the web page. Error: {str(e)}")

        # 构建并返回FeatureTable对象
        return FeatureTable(
            name=name,
            table_id=table_name,
            description=description or "",
            primary_keys=primary_keys,
            partition_columns=partition_columns or [],
            features=[field.name for field in table_schema.fields],
            timestamp_keys=timestamp_key or [],
            tags=dict(**tags or {}, **env_tags)
        )

    def write_table(
            self,
            name: str,
            df: DataFrame,
            database_name: Optional[str] = None,
            mode: Optional[str] = APPEND,
            checkpoint_location: Optional[str] = None,
            trigger: Optional[Dict[str, Any]] = DEFAULT_WRITE_STREAM_TRIGGER,
            catalog_name: Optional[str] = None
    ) -> Optional[StreamingQuery]:

        """
        写入特征表数据（支持批处理和流式写入）

        Args:
            name: 特征表名称（格式：<table>）
            df: 要写入的数据（DataFrame）
            database_name: 数据库名
            mode: 写入模式（append/overwrite）
            checkpoint_location: 流式写入的检查点位置（仅流式写入需要）
            trigger: 流式写入触发条件（仅流式写入需要）
            catalog_name: 目录名

        Returns:
            如果是流式写入返回StreamingQuery对象，否则返回None

        Raises:
            ValueError: 当参数不合法时抛出
        """

        # 验证写入模式
        valid_modes = ["append", "overwrite"]
        if mode not in valid_modes:
            raise ValueError(f"Invalid write mode '{mode}', valid options: {valid_modes}")

        # 表名校验
        common_utils.validate_table_name(name)

        common_utils.validate_database(database_name)

        # 构建完整表名
        table_name = common_utils.build_full_table_name(name, database_name, catalog_name)

        # 检查表是否存在
        if not self._check_table_exists(table_name):
            raise ValueError(f"table '{name}' not exists")

        # 判断是否是流式DataFrame
        is_streaming = df.isStreaming

        try:
            if is_streaming:
                # 流式写入
                if not checkpoint_location:
                    raise ValueError("Streaming write requires checkpoint_location parameter")

                writer = df.writeStream \
                    .format("parquet") \
                    .outputMode(mode) \
                    .option("checkpointLocation", checkpoint_location) \
                    # .foreachBatch(process_batch)

                if trigger:
                    writer = writer.trigger(**trigger)

                return writer.toTable(table_name)
            else:
                # 批处理写入
                df.write \
                    .mode(mode) \
                    .insertInto(table_name)
                # self._feast_client.client.write_to_offline_store(feature_view_name=table_name, df=df.toPandas(), allow_registry_cache=False,)
                return None

        except Exception as e:
            raise
            # raise ValueError(f"Failed to write to table '{table_name}': {str(e)}") from e

    def register_table(self, name, database_name, timestamp_key: str, engine_type: EngineTypes, data_source_name: str,
                       primary_keys: Union[str, List[str]], catalog_name: Optional[str] = None
                       ):
        """注册表 为特征表
                Args:
                    name: 表名（格式：<table>）
                    database_name: 特征库名称
                    data_source_name: 数据源名称
                    engine_type: 引擎类型
                    timestamp_key: 时间戳键
                    primary_keys: 主键
                    catalog_name: 目录名
                Raises:
                    ValueError: 当表不存在或参数无效时抛出
                    RuntimeError: 当修改操作失败时抛出

                示例:
                    # 修改表属性
                    client.register_table("user_features", "user_database")
                """

        # 表名校验
        common_utils.validate_table_name(name)
        common_utils.validate_database(database_name)

        if primary_keys:
            assert self._check_sequence_element_type(primary_keys, str), "primary_keys must be a list of strings"
        assert isinstance(timestamp_key, str), "timestamp key must be string"

        # 构建完整表名
        table_name = common_utils.build_full_table_name(name, database_name, catalog_name)

        try:
            # 检查表是否存在
            if not self._check_table_exists(table_name):
                raise ValueError(f"table '{name}' not exists")
            tbl_pro = self._spark.sql(f"SHOW TBLPROPERTIES {table_name}")
            props = {row['key']: row['value'] for row in tbl_pro.collect()}

            # 检查Primary Key和Timestamp Key是否为空
            if engine_type == engine_type.ICEBERG_ENGINE and props.get("format-version", "") == "2":
                if not primary_keys:
                    if props.get('dlc.ao.data.govern.sorted.keys', "") == "":
                        raise ValueError(
                            "table dlc.ao.data.govern.sorted.keys is empty. you must set dlc.ao.data.govern.sorted.keys")
                    else:
                        primary_keys = props.get('dlc.ao.data.govern.sorted.keys').split(",")
            elif engine_type == engine_type.HIVE_ENGINE:
                if not primary_keys:
                    raise ValueError("primary_keys cannot be None for HIVE_ENGINE")

            if props.get("wedata.feature_table", "") == "true":
                raise ValueError("table is already a feature table")

            self._validate_key_conflicts(primary_keys, timestamp_key)
            # 检查表是否存在
            dup_list = common_utils.get_duplicates(primary_keys)
            if dup_list:
                raise ValueError(f"primary_keys contains duplicates: {dup_list}")

            s = props.get(FEATURE_TABLE_PROJECT, "")
            if not s:  # 如果s是空字符串
                projectIds = []
            else:
                projectIds = json.loads(s)
            current_project_id = os.getenv("WEDATA_PROJECT_ID")
            # 判断是否包含projectIds（仅是projectIds非空的时候)
            if current_project_id not in projectIds and len(projectIds):
                register_table_project_ids = props.get(FEATURE_TABLE_PROJECT)
            else:
                projectIds.append(current_project_id)
                register_table_project_ids = json.dumps(projectIds)
            tbl_properties = {
                FEATURE_TABLE_KEY: FEATURE_TABLE_VALUE,
                FEATURE_TABLE_PROJECT: register_table_project_ids,
                FEATURE_TABLE_TIMESTAMP: timestamp_key,
                FEATURE_TABLE_BACKUP_PRIMARY_KEY: ",".join(primary_keys),
            }

            env_tags = {
                "project_id": os.getenv("WEDATA_PROJECT_ID", ""),  # wedata项目ID
                "engine_name": os.getenv("WEDATA_NOTEBOOK_ENGINE", ""),  # wedata引擎名称
                "user_uin": os.getenv("KERNEL_LOGIN_UIN", "")  # wedata用户UIN
            }
            for key, val in env_tags.items():
                if not props.get(f"feature_{key}", ""):
                    tbl_properties[f"feature_{key}"] = val

            # 构建属性设置语句
            props_str = ", ".join(
                f"'{k}'='{self._escape_sql_value(v)}'"
                for k, v in tbl_properties.items()
            )


            alter_sql = f"ALTER TABLE {table_name} SET TBLPROPERTIES ({props_str})"

            try:
                self._sync_table_info(table_name=name, action_name="create",
                                  database_name=env_utils.get_database_name(database_name),
                                  data_source_name=data_source_name, engine_name=env_utils.get_engine_name(), is_try=True)
            except tencentcloud.common.exception.TencentCloudSDKException as e:
                raise RuntimeError(f"Table '{name}' is can't create. {str(e)}")

            # 执行修改
            self.__logger.info(f"alter table sql: \n {alter_sql}")
            self._spark.sql(alter_sql)
            self.__logger.debug("Execute sql done, start sync table info to feast")
            self._feast_client.alter_table(full_table_name=table_name, primary_keys=primary_keys,
                                           timestamp_key=timestamp_key)
            self.__logger.info(f"Successfully register table '{table_name}'. Starting web synchronization.")

            try:
                self._sync_table_info(table_name=name, action_name="create",
                                  database_name=env_utils.get_database_name(database_name),
                                  data_source_name=data_source_name, engine_name=env_utils.get_engine_name(), is_try=False)
            except tencentcloud.common.exception.TencentCloudSDKException as e:
                raise RuntimeError(f"Failed to synchronize web data for table '{name}'. "
                                   f"Please manually operate on the web page. Error: {str(e)}")
        except (ValueError, RuntimeError):
            raise
        except Exception as e:
            raise RuntimeError(f"Failed to modify properties for table '{table_name}': {str(e)}") from e

    def read_table(
            self,
            name: str,
            database_name: Optional[str] = None,
            is_online: bool = False,
            online_config: Optional[RedisStoreConfig] = None,
            entity_row: Optional[List[Dict[str, Any]]] = None,
            catalog_name: Optional[str] = None
    ) -> DataFrame:

        """
        从特征表中读取数据

        Args:
            name: 特征表名称（格式：<table>）
            database_name: 特征库名称
            is_online: 是否读取在线表
            online_config: 在线表配置
            entity_row: 实体行(用于过滤在线数据, 仅当在线表为true时有效)
            catalog_name: 目录
        Returns:
            包含表数据的DataFrame

        Raises:
            ValueError: 当表不存在或读取失败时抛出
        """

        # 表名校验
        common_utils.validate_table_name(name)

        common_utils.validate_database(database_name)

        # 构建完整表名
        table_name = common_utils.build_full_table_name(name, database_name, catalog_name)

        try:
            # 检查表是否存在
            if not self._check_table_exists(table_name):
                raise ValueError(f"Table '{name}' does not exist")

            if is_online:
                return self._read_online_table(
                    table_name=name, database_name=database_name,
                    online_config=online_config, entity_row=entity_row, catalog_name=catalog_name)
            # 读取表数据
            return self._spark.read.table(table_name)

        except Exception as e:
            raise

    def drop_table(self, name: str, database_name: Optional[str] = None, catalog_name: Optional[str] = None) -> None:

        """
        删除特征表（表不存在时抛出异常）

        Args:
            name: 特征表名称（格式：<table>）
            database_name: 特征库名称
            catalog_name: 目录
        Raises:
            ValueError: 当表不存在时抛出
            RuntimeError: 当删除操作失败时抛出

        示例:
            # 基本删除
            drop_table("user_features")
        """

        # 表名校验
        common_utils.validate_table_name(name)

        # 构建完整表名
        table_name = common_utils.build_full_table_name(name, database_name, catalog_name)
        try:
            # 检查表是否存在
            if not self._check_table_exists(table_name):
                self.__logger.error(f"Table '{name}' does not exist")
                return

            try:
                feature_view = self._feast_client.get_feature_view(table_name)
            except Exception as e:
                pass
                # self.__logger.warning(f"Table '{name}' is not a feature table, skip delete. {str(e)}")
            else:
                if feature_view.online:
                    raise ValueError(f"Table '{name}' has a online table, please call drop_online_table first")
            try:
                self._sync_table_info(table_name=name, action_name="delete",
                                  database_name=env_utils.get_database_name(database_name),
                                  data_source_name="", engine_name=env_utils.get_engine_name(), is_try=True)
            except tencentcloud.common.exception.TencentCloudSDKException as e:
                raise RuntimeError(f"Table '{name}' is can't delete. {str(e)}")

            # 执行删除
            self._spark.sql(f"DROP TABLE {table_name}")
            self.__logger.info(f"Table '{name}' dropped")
            try:
                self._feast_client.remove_offline_table(table_name=table_name)
            except Exception as e:
                raise
                # raise ValueError(f"Failed to delete table '{name}' in feast: {str(e)}")
            else:
                self.__logger.info(f"Table '{name}' removed from feast")

            try:
                self._sync_table_info(table_name=name, action_name="delete",
                                      database_name=env_utils.get_database_name(database_name),
                                      data_source_name="", engine_name=env_utils.get_engine_name(), is_try=False)
            except tencentcloud.common.exception.TencentCloudSDKException as e:
                print(f"Failed to delete table information on the web interface. You need to delete it manually. Error: {str(e)}")
        except ValueError as e:
            raise  # 直接抛出已知的ValueError
        except Exception as e:
            raise RuntimeError(f"Failed to delete table '{name}': {str(e)}") from e

    def _sync_table_info(self, table_name: str, action_name: str, database_name: str,
                         data_source_name: str, engine_name: str, is_try: bool):
        return _refresh_table(project_id=self.project, secret_id=self.cloud_secret_id, secret_key=self.cloud_secret_key,
                              region=self.region, table_name=table_name,
                              action=action_name, database_name=database_name, data_source_name=data_source_name,
                              engine_name=engine_name, is_try=is_try, data_source_type=env_utils.get_engine_type(),
                              token=self.__cloud_tmp_token)

    def _read_online_table(self,
                           table_name: str, database_name: str, online_config: RedisStoreConfig,
                           entity_row:List[Dict[str,Any]] = None, catalog_name: str = None
                           ):
        full_table_name = common_utils.build_full_table_name(table_name, database_name, catalog_name=catalog_name)
        primary_keys, timestamp_key = self._get_table_primary_keys_and_timestamp_key(full_table_name)
        entity_row_dict = {}
        if isinstance(entity_row, list):
            for row in entity_row:
                if not isinstance(row, dict):
                    raise ValueError("Entity_row row must be a dictionary")
                for key in row.keys():
                    if key not in primary_keys:
                        raise ValueError(f"Entity_row row key '{key}' is not a primary key")
                    entity_row_dict[key] = key
        elif isinstance(entity_row, dict):
            for key in entity_row.keys():
                if key not in primary_keys:
                    raise ValueError(f"Entity_row row key '{key}' is not a primary key")
            entity_row_dict = entity_row
        else:
            raise ValueError(f"Entity_row must be a list of dictionaries or a single dictionary. {type(entity_row)}")

        tmp_schema = self._spark.table(tableName=full_table_name).schema
        columns_name_list = []
        tmp_schema_list = []
        for field in tmp_schema.fields:
            if field.name in primary_keys or field.name == timestamp_key:
                if entity_row_dict.get(field.name):
                    tmp_schema_list.append(field)
                continue
            columns_name_list.append(field.name)
            tmp_schema_list.append(field)

        schema_name_list = [field.name for field in tmp_schema_list]
        schema = StructType(tmp_schema_list)
        for field in schema:
            self.__logger.debug(f"translate {field.name} to feast Type: {field.dataType}")

        feast_client = FeastClient(offline_store=self._spark, online_store_config=online_config)
        # 构建离线表的entity的数据过滤
        if not entity_row:
            tbl_props = self._spark.sql(f"SHOW TBLPROPERTIES {table_name}")
            props = {row['key']: row['value'] for row in tbl_props.collect()}
            primary_key = props.get(FEATURE_TABLE_BACKUP_PRIMARY_KEY)
            query_result = self._spark.sql(f"SELECT {primary_key} FROM {table_name} LIMIT 1")
            result_row = query_result.first()
            if result_row:
                online_view = feast_client.get_online_table_view(
                    full_table_name=full_table_name,
                    columns_name=columns_name_list,
                    entity_rows=[result_row.asDict()])
                self.__logger.debug(f"=====>read online dataframe:\n{online_view[schema_name_list]}")
                return self._spark.createDataFrame(online_view[schema_name_list], schema=schema, verifySchema=False)
            else:
                return self._spark.createDataFrame([])
        else:
            online_view = feast_client.get_online_table_view(
                full_table_name=full_table_name,
                columns_name=columns_name_list,
                entity_rows=entity_row)
            self.__logger.debug(f"=====>read online dataframe:\n{online_view[schema_name_list]}")
            return self._spark.createDataFrame(online_view[schema_name_list], schema=schema, verifySchema=False)

    def get_table(
            self,
            name: str,
            spark_client: SparkClient,
            database_name: Optional[str] = None,
            catalog_name: Optional[str] = None
    ) -> FeatureTable:

        """
        获取特征表元数据信息

        参数:
            name: 特征表名称
            spark_client: Spark客户端
            catalog_name: 目录名称

        返回:
            FeatureTable对象

        异常:
            ValueError: 当表不存在或获取失败时抛出
        """

        # 表名校验
        common_utils.validate_table_name(name)
        common_utils.validate_database(database_name)

        # 构建完整表名
        table_name = common_utils.build_full_table_name(name, database_name, catalog_name)
        if not self._check_table_exists(full_table_name=table_name):
            raise ValueError(f"Table '{name}' does not exist")
        try:
            return spark_client.get_feature_table(table_name)
        except Exception as e:
            raise
            # raise ValueError(f"Failed to get metadata for table '{name}': {str(e)}") from e

    def alter_table_tag(
            self,
            name: str,
            properties: Dict[str, str],
            database_name: Optional[str] = None,
            catalog_name: Optional[str] = None
    ):
        """
        修改表的TBLPROPERTIES属性（有则修改，无则新增）

        Args:
            name: 表名（格式：<table>）
            properties: 要修改/新增的属性字典
            database_name: 特征库名称
            catalog_name: 目录名称

        Raises:
            ValueError: 当表不存在或参数无效时抛出
            RuntimeError: 当修改操作失败时抛出

        示例:
            # 修改表属性
            client.alter_tables_tag("user_features", {
                "comment": "更新后的描述",
                "owner": "data_team"
            })
        """
        # 参数校验
        if not properties:
            raise ValueError("properties must be a non-empty dictionary")

        # 表名校验
        common_utils.validate_table_name(name)
        common_utils.validate_database(database_name)

        # 构建完整表名
        table_name = common_utils.build_full_table_name(name, database_name, catalog_name)

        try:
            # 检查表是否存在
            if not self._check_table_exists(table_name):
                raise ValueError(f"table '{name}' not exists")

            # 构建属性设置语句
            props_str = ", ".join(
                f"'{k}'='{self._escape_sql_value(v)}'"
                for k, v in properties.items()
            )

            alter_sql = f"ALTER TABLE {table_name} SET TBLPROPERTIES ({props_str})"

            # 执行修改
            self._spark.sql(alter_sql)
            self._feast_client.modify_tags(table_name=table_name, tags=properties)
            print(f"Successfully updated properties for table '{name}': {list(properties.keys())}")

        except ValueError as e:
            raise  # 直接抛出已知的ValueError
        except Exception as e:
            raise RuntimeError(f"Failed to modify properties for table '{name}': {str(e)}") from e

    def publish_table(self, table_name: str, data_source_name: str,
                      database_name: Optional[str] = None,
                      is_cycle: bool = False, cycle_obj: models.TaskSchedulerConfiguration = None,
                      is_use_default_online: bool = True, online_config: RedisStoreConfig = None,
                      catalog_name: Optional[str] = None):
        """
        将离线特征表发布为在线特征表
        Args:
            table_name: 离线特征表名称
            data_source_name: 数据源名称
            database_name: 数据库名称
            is_cycle: 是否周期性发布
            cycle_obj: 周期性任务配置
            is_use_default_online: 是否使用默认的在线存储配置
            online_config: 在线存储配置 (仅当is_use_default_online为False时生效)
            catalog_name: 目录名称
        """
        # 构建完整表名
        full_table_name = common_utils.build_full_table_name(table_name, database_name, catalog_name=catalog_name)

        # 检查表是否存在
        if not self._check_table_exists(full_table_name):
            raise ValueError(f"Table '{full_table_name}' does not exist")

        # 检查是否已经发布,查看Redis中是否有值
        try:
        # 获取离线表的列名
            online_data = self._feast_client.get_feature_view(full_table_name)
        except Exception as e:
            print(f"Failed to get online table view for table '{full_table_name}': {str(e)}")
        else:
            if online_data.online:
                raise ValueError(f"Table '{full_table_name}' has already been published")

        # 配置周期性参数
        if is_cycle:
            if not isinstance(cycle_obj, models.TaskSchedulerConfiguration):
                raise ValueError("cycle_obj must be a TaskSchedulerConfiguration object when is_cycle is True")

            cycle_obj.CycleType = "CRONTAB_CYCLE"
        else:
            if isinstance(cycle_obj, models.TaskSchedulerConfiguration):
                cycle_obj.CycleType = "ONEOFF_CYCLE"
            else:
                cycle_obj = models.TaskSchedulerConfiguration()
                cycle_obj.CycleType = "ONEOFF_CYCLE"
                # 设置默认当前时间延后1分钟
                cycle_obj.CrontabExpression = (datetime.datetime.now() + datetime.timedelta(minutes=3)).strftime(
                    "%M %H %d %m %w ? %y")

        if is_use_default_online:
            online_feature_config = models.OnlineFeatureConfiguration()
            online_feature_config.UserDefault = True
        else:
            if not isinstance(online_config, RedisStoreConfig):
                raise ValueError("online_config must be a RedisStoreConfig object when is_use_default_online is False")

            online_feature_config = models.OnlineFeatureConfiguration()
            online_feature_config.UserDefault = False
            online_feature_config.Host = online_config.host
            online_feature_config.Port = online_config.port
            online_feature_config.DB = online_config.db

        offline_feature_config = models.OfflineFeatureConfiguration()
        offline_feature_config.DatabaseName = env_utils.get_database_name(database_name)
        offline_feature_config.TableName = table_name

        offline_feature_config.PrimaryKeys, offline_feature_config.TimestampColumn = self._get_table_primary_keys_and_timestamp_key(
            full_table_name)

        offline_feature_config.DatasourceName = data_source_name
        offline_feature_config.DatasourceType = env_utils.get_engine_type()
        offline_feature_config.EngineName = env_utils.get_engine_name()

        api_requests = models.CreateOnlineFeatureTableRequest()
        api_requests.OfflineFeatureConfiguration = offline_feature_config
        api_requests.OnlineFeatureConfiguration = online_feature_config
        api_requests.TaskSchedulerConfiguration = cycle_obj
        api_requests.ProjectId = env_utils.get_project_id()
        region = env_utils.get_region()
        if not os.environ.get("RESOURCE_GROUP_ID", ""):
            res_group_item = _get_default_resource_group(
                api_requests.ProjectId, self.__cloud_secret_id, self.__cloud_secret_key, region,
                token=self.__cloud_tmp_token)
            api_requests.ResourceGroupId = res_group_item.ExecutorGroupId
        else:
            api_requests.ResourceGroupId = os.environ.get("RESOURCE_GROUP_ID")
        client = FeatureCloudSDK(secret_id=self.__cloud_secret_id, secret_key=self.__cloud_secret_key, region=region,
                                 token=self.__cloud_tmp_token)
        resp = client.CreateOnlineFeatureTable(api_requests)
        if cycle_obj.CycleType == "ONEOFF_CYCLE":
            print(f"publish online task create success. it will be execute after 3 min. {resp.Data.OnlineTableId} {resp.Data.OfflineTableId} ")
        else:
            print(f"publish online task create success. {resp.Data.OnlineTableId} {resp.Data.OfflineTableId} ")

    def drop_online_table(self, table_name: str, online_config: RedisStoreConfig, database_name: Optional[str] = None,
                          catalog_name: Optional[str] = None):
        # 构建完整表名
        full_table_name = common_utils.build_full_table_name(table_name, database_name, catalog_name=catalog_name)
        feast_client = FeastClient(self._spark, online_config)
        try:
            self._sync_table_info(table_name=table_name, database_name=database_name, action_name="delete_online",
                                  data_source_name="", engine_name=env_utils.get_engine_name(), is_try=True)
        except Exception as e:
            raise RuntimeError(f"drop online table failed. table_name: {full_table_name}. {str(e)}")

        feast_client.remove_online_table(full_table_name)
        try:
            self._sync_table_info(table_name=table_name, database_name=database_name, action_name="delete_online",
                                  data_source_name="", engine_name=env_utils.get_engine_name(), is_try=False)
        except Exception as e:
            raise RuntimeError(f"drop online table failed. table_name: {full_table_name}. {str(e)}")
        print(f"drop online table success. table_name: {full_table_name}")

    def _get_table_primary_keys_and_timestamp_key(self, full_table_name: str) -> 'str, str':

        tbl_pro = self._spark.sql(f"SHOW TBLPROPERTIES {full_table_name}")
        props = {row['key']: row['value'] for row in tbl_pro.collect()}

        if props.get(FEATURE_DLC_TABLE_PRIMARY_KEY, ""):
            primary_keys = props.get(FEATURE_DLC_TABLE_PRIMARY_KEY, "")
        else:
            primary_keys = props.get(FEATURE_TABLE_BACKUP_PRIMARY_KEY, "")
        primary_keys = primary_keys.split(",")
        timestamp_key = props.get(FEATURE_TABLE_TIMESTAMP, "")
        return primary_keys, timestamp_key

    def _check_table_exists(self, full_table_name: str) -> bool:
        return common_utils.check_spark_table_exists(self._spark, full_table_name)

    def _get_offline_default_database(self) -> Optional[models.FeatureStoreDatabase]:
        client = FeatureCloudSDK(secret_id=self.__cloud_secret_id, secret_key=self.__cloud_secret_key,
                                 region=self.__region, token=self.__cloud_tmp_token)
        req = models.DescribeFeatureStoreDatabasesRequest()
        req.ProjectId = self.__project
        rsp = client.DescribeFeatureStoreDatabases(req)
        if len(rsp.Data) == 0:
            return None
        for item in rsp.Data:
            if item.OnlineMode == 0 and item.IsDefault == 1:
                return item
        return None


def _get_default_resource_group(project_id: str, secret_id: str, secret_key: str, region: str, token: str):
    client = FeatureCloudSDK(secret_id=secret_id, secret_key=secret_key, region=region, token=token)
    request = models.DescribeNormalSchedulerExecutorGroupsRequest()
    request.ProjectId = project_id
    resp = client.DescribeNormalSchedulerExecutorGroups(request)
    # 默认取第一个健康可用的资源组进行执行
    for item in resp.Data:
        if item.Available:
            return item
    raise ValueError("No available resource group found")


def _refresh_table(project_id: str, secret_id: str, secret_key: str, region: str, table_name: str,
                   action: str, database_name: str, data_source_name: str, data_source_type: str,
                   engine_name: str, is_try: bool, token: str):
    client = FeatureCloudSDK(secret_id=secret_id, secret_key=secret_key, region=region, token=token)
    request = models.RefreshFeatureTableRequest()
    request.ProjectId = project_id
    request.TableName = table_name
    request.DatabaseName = database_name
    request.DatasourceName = data_source_name
    request.DatasourceType = data_source_type
    request.EngineName = engine_name
    request.ActionName = action
    request.IsTry = is_try
    resp = client.RefreshFeatureTable(request)
    return resp