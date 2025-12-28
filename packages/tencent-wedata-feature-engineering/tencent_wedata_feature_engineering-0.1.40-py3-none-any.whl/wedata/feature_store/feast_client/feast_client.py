# -*- coding: utf-8 -*-

__doc__ = """
Feast客户端，用于与Feast服务器交互
"""

import json
import os
import re
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
try:
    # pyspark 3.5.0 以后
    from pyspark.errors import IllegalArgumentException
except ModuleNotFoundError:
    from pyspark.sql.utils import IllegalArgumentException

import pandas
import pytz
from feast import FeatureStore, RepoConfig, FeatureView
from pyspark.sql import DataFrame, SparkSession
from wedata.feature_store.common.store_config.redis import RedisStoreConfig
from wedata.feature_store.utils import env_utils
from feast import Entity, FeatureService
from feast.infra.offline_stores.contrib.spark_offline_store.spark_source import SparkSource
from feast.infra.online_stores.redis import RedisOnlineStore
from feast.errors import FeatureServiceNotFoundException
from feast.types import ValueType
from pyspark.sql.types import (
        TimestampType, DateType, StructType, NullType, ByteType, IntegerType, DecimalType, DoubleType, FloatType,
        BooleanType,
        StringType, ArrayType, LongType
    )

TEMP_FILE_PATH = "/tmp/feast_data/"


class FeastClient:

    def __init__(self, offline_store: SparkSession, online_store_config: RedisStoreConfig = None):
        project_id = env_utils.get_project_id()
        remote_path = env_utils.get_feast_remote_url()
        if offline_store is None or not isinstance(offline_store, SparkSession):
            raise ValueError("offline_store must be provided SparkSession instance")

        # 应用Spark配置
        spark_conf_dict = dict()
        spark_conf = offline_store.sparkContext.getConf().getAll()
        for item in spark_conf:
            spark_conf_dict[item[0]] = item[1]

        config = RepoConfig(
            project=project_id,
            registry={"registry_type": "remote", "path": remote_path},
            provider="local",
            online_store={"type": "redis",
                          "connection_string": online_store_config.connection_string} if online_store_config else None,
            offline_store={"type": "spark", "spark_conf": spark_conf_dict},
            batch_engine={"type": "spark.engine"},
            entity_key_serialization_version=2
        )
        self._client = FeatureStore(config=config)
        self._spark = offline_store
        self._spark.builder.enableHiveSupport()
        # 设置Spark时区为pytz时区，避免后续spark操作toPandas时出现时区问题
        try:
            spark_timezone = self._spark.conf.get("spark.sql.session.timeZone", "")
            if spark_timezone:
                pytz_timezone = _translate_spark_timezone(spark_timezone)
                self._spark.conf.set("spark.sql.session.timeZone", pytz_timezone)
            else:
                self._spark.conf.set("spark.sql.session.timeZone", "Etc/GMT+8")
        except IllegalArgumentException:
            self._spark.conf.set("spark.sql.session.timeZone", "Etc/GMT+8")

    @property
    def client(self):
        return self._client

    def create_table(self,
                     table_name: str,
                     primary_keys: List[str],
                     timestamp_key: str,
                     df: Optional[DataFrame] = None,
                     schema: Optional[StructType] = None,
                     tags: Optional[Dict[str, str]] = None,
                     description: Optional[str] = None):
        if schema is not None and df is None:
            # 创建空的Spark DataFrame
            df = self._spark.createDataFrame([], schema)
        feast_table_name = translate_table_name_to_feast(table_name)
        entities = _get_entity_from_schema(feast_table_name, df.schema, primary_keys)
        feature_view = _create_table_to_feature_view(
            table_name=table_name,
            primary_keys=primary_keys,
            entities=entities,
            timestamp_key=timestamp_key,
            df=df,
            tags=tags,
            description=description
        )
        # 确保feature在增量服务时获取的数据时间范围时正确的。
        self._apply_feature_view(table_name, entities, feature_view)

    def _apply_feature_view(self, table_name, entities, feature_view: FeatureView):
        feast_service_name, old_table_name = split_full_table_for_feast(table_name)
        try:
            feature_service = self._client.get_feature_service(feast_service_name)
        except FeatureServiceNotFoundException:
            feature_service = FeatureService(name=feast_service_name, features=[feature_view])
        else:
            if feature_service.name == "":
                feature_service = FeatureService(name=feast_service_name, features=[feature_view])
            else:
                # 对于已存在的FeatureService，需要更新其中的FeatureView
                update_flag = False
                for index in range(0, len(feature_service.feature_view_projections)):
                    if feature_service.feature_view_projections[index].name == feature_view.name:
                        # update feature_view
                        feature_service.feature_view_projections[index] = feature_view.projection
                        update_flag = True
                        break
                if not update_flag:
                    feature_service.feature_view_projections.append(feature_view.projection)
        self._client.apply(feature_view)
        self._client.apply(entities)
        self._client.apply(feature_service)

    def remove_offline_table(self, table_name: str):
        feast_table_name = translate_table_name_to_feast(table_name)
        feast_service_name, old_table_name = split_full_table_for_feast(table_name)
        self._client.registry.delete_data_source(feast_table_name, self._client.project)
        try:
            feature_view = self.get_feature_view(table_name)
        except Exception as e:
            pass
        else:
            try:
                feature_service = self._client.get_feature_service(feast_service_name)
            except Exception as e:
                print(f"feature_service:{feast_service_name} not found")
            else:
                for index in range(0, len(feature_service.feature_view_projections)):
                    if feature_service.feature_view_projections[index].name == feature_view.name:
                        feature_service.feature_view_projections.pop(index)
                        break
                self._client.apply(feature_service)
            self._client.registry.delete_feature_view(feast_table_name, self._client.project)

    def get_feature_view(self, table_name: str):
        feast_table_name = translate_table_name_to_feast(table_name)
        return self._client.get_feature_view(feast_table_name)

    def remove_online_table(self, table_name: str):
        if not self._client.config.online_store:
            raise ValueError("Online store is not configured")

        feast_table_name = translate_table_name_to_feast(table_name)
        table_view = self._client.get_feature_view(feast_table_name)
        if not table_view:
            raise ValueError(f"Table {table_name} not found in Feast")

        if self._client.config.online_store.type == "redis":
            redis_online_store = RedisOnlineStore()
            redis_online_store.delete_table(self._client.config, table_view)
            table_view.online = False
            table_view.update_materialization_intervals(get_materialization_default_time())
            self._client.apply(table_view)
        else:
            raise ValueError(f"Unsupported online store type: {self._client.config.online_store.type}")

        self._client.refresh_registry()

    def alter_table(self, full_table_name: str, timestamp_key: str, primary_keys: List[str]):
        """
        将已注册的Delta表同步到Feast中作为离线特征数据
        
        Args:
            full_table_name: 表名（格式：<table>）
            timestamp_key: 时间戳列名
            primary_keys: 主键列名列表
        Raises:
            ValueError: 当表不存在或参数无效时抛出
            RuntimeError: 当同步操作失败时抛出
        """
        import logging
        try:

            # 1. 读取Delta表数据和schema
            df = self._spark.table(full_table_name)

            feast_table_name = translate_table_name_to_feast(full_table_name)
            entities = _get_entity_from_schema(feast_table_name, df.schema, primary_keys)
            # 2. 从表属性中获取主键和时间戳列
            tbl_props = self._spark.sql(f"SHOW TBLPROPERTIES {full_table_name}").collect()
            props = {row['key']: row['value'] for row in tbl_props}

            if not primary_keys:
                raise ValueError("Primary keys not found in table properties")
            if not timestamp_key:
                raise ValueError("Timestamp keys not found in table properties")

            logging.info(f"Primary keys: {primary_keys}")
            logging.info(f"Timestamp keys: {timestamp_key}")

            # 3. 创建或更新FeatureView
            feature_view = _create_table_to_feature_view(
                table_name=full_table_name,
                entities=entities,
                primary_keys=primary_keys,
                timestamp_key=timestamp_key,
                df=df,
                tags={"source": "delta_table", **json.loads(props.get("tags", "{}"))},
            )

            self._apply_feature_view(full_table_name, entities, feature_view)
            # 4. 应用到Feast
            logging.info(f"Successfully synced Delta table {full_table_name} to Feast")

        except Exception as e:
            logging.error(f"Failed to sync Delta table to Feast: {str(e)}")
            raise RuntimeError(f"Failed to sync Delta table {full_table_name} to Feast: {str(e)}") from e

    def modify_tags(
            self,
            table_name: str,
            tags: Dict[str, str]
    ) -> None:
        """修改特征表的标签信息

        Args:
            table_name: 特征表名称(格式: <database>.<table>)
            tags: 要更新的标签字典

        Raises:
            ValueError: 当参数无效时抛出
            RuntimeError: 当修改操作失败时抛出
        """
        if not table_name:
            raise ValueError("table_name cannot be empty")
        if not tags:
            raise ValueError("tags cannot be empty")

        feast_table_name = translate_table_name_to_feast(table_name)
        try:
            # 获取现有的FeatureView
            feature_view = self._client.get_feature_view(feast_table_name)
            if not feature_view:
                raise ValueError(f"FeatureView '{table_name}' not found")

            # 更新标签
            current_tags = feature_view.tags or {}
            current_tags.update(tags)
            feature_view.tags = current_tags

            # 应用更新
            self._client.apply([feature_view])
            print(f"Successfully updated tags for table '{table_name}'")

        except Exception as e:
            raise RuntimeError(f"Failed to modify tags for table '{table_name}': {str(e)}") from e

    def get_online_table_view(self, full_table_name: str, columns_name: List[str], entity_rows: List[Dict[str, Any]]) -> pandas.DataFrame:
        """
        获取在线特征表的数据
        args:
            full_table_name: 特征表名称(格式: <database>.<table>)
        return:
            FeatureView实例
        """
        feast_table = translate_table_name_to_feast(full_table_name)
        feature_names = []
        for column_name in columns_name:
            feature_names.append(f"{feast_table}:{column_name}")

        if isinstance(entity_rows, list):
            new_entity_rows = []
            for entity_row in entity_rows:
                temp_entity_row = {}
                for key, value in entity_row.items():
                    temp_entity_row[_get_entity_name(full_table_name, key)] = value
                new_entity_rows.append(temp_entity_row)
        elif isinstance(entity_rows, dict):
            new_entity_rows = {}
            for key, value in entity_rows.items():
                new_entity_rows[_get_entity_name(full_table_name, key)] = value
        else:
            raise TypeError("entity_rows must be a list or dict")

        try:
            self._client.refresh_registry()
            online_stores = self._client.get_online_features(features=feature_names, entity_rows=new_entity_rows)
        except UnboundLocalError as e:
            raise ValueError(f"{full_table_name} table not in feast registry. {str(e)}")

        return online_stores.to_df()

    def read_offline_table(self, table_name: str, database_name: str, columns_df: pandas.DataFrame,
                           full_feature_names=True) -> pandas.DataFrame:
        """
        获取离线特征表的数据（存储到Feast中的数据)
        """
        if not isinstance(columns_df, pandas.DataFrame):
            raise TypeError("columns_df must be a pandas.DataFrame instance")

        full_table_name = f"{database_name}.{table_name}"
        feast_table_name = translate_table_name_to_feast(full_table_name)
        # 批量替换DataFrame列名
        rename_dict = {}
        for column_name in columns_df.columns:
            rename_dict[column_name] = _get_entity_name(feast_table_name, column_name)

        columns_df.rename(columns=rename_dict, inplace=True)
        features = self._client.get_feature_service(database_name, allow_cache=False)
        result = self._client.get_historical_features(
            entity_df=columns_df, features=features, full_feature_names=full_feature_names)
        return result.to_df()


def _create_table_to_feature_view(
        table_name: str,
        entities: List[Entity],
        primary_keys: List[str],
        timestamp_key: str,
        df: Optional[DataFrame],
        tags: Optional[Dict[str, str]] = None,
        description: Optional[str] = None,
):
    """

    Returns:
        FeatureView实例
    """
    if primary_keys is None or len(primary_keys) == 0:
        raise ValueError("primary_keys must not be empty")
    if not timestamp_key:
        raise ValueError("timestamp_keys must not be empty")

    os.makedirs(TEMP_FILE_PATH, exist_ok=True)

    temp_file = os.path.join(TEMP_FILE_PATH, f"{table_name}.parquet")

    df.write.parquet(f"file://{temp_file}", mode="overwrite")
    feast_table_name = translate_table_name_to_feast(table_name)
    resources = SparkSource(
        name=feast_table_name,
        table=table_name,
        # path=f"file://{temp_file}",
        timestamp_field=timestamp_key,
        # query=f"SELECT * FROM {table_name}",
        # file_format="parquet",
        tags=tags,
        description=description,
    )

    # 构建FeatureView的剩余逻辑
    feature_view = FeatureView(
        name=feast_table_name,
        entities=entities,
        tags=tags,
        source=resources,
    )
    feature_view.online = False
    feature_view.update_materialization_intervals([(datetime(1990, 1, 1), datetime(1990, 1, 1))])
    return feature_view


def _translate_spark_timezone(timezone: str) -> str:
    """
    将Spark时区字符串转换为pytz时区字符串
    Args:
        timezone: Spark时区字符串
    Returns:
        Feast时区字符串
    """
    try:
        py_timezone = pytz.timezone(timezone)
    except pytz.exceptions.UnknownTimeZoneError:
        # GMT+08:00 转换为 'Etc/GMT+8'
        result = re.compile(r"GMT([+-])(\d{2}):(\d{2})").match(timezone)
        if result:
            groups = result.groups()
            if len(groups) == 3:
                return f"Etc/GMT{groups[0]}{int(groups[1])}"
        else:
            raise ValueError(f"Invalid timezone string: {timezone}")
    else:
        return str(py_timezone)

    return timezone


def _get_entity_name(table_name: str, field_name: str):
    return field_name
    # return f"{table_name}_{field_name}"


def _get_entity_from_schema(table_name:str, schema: StructType, primary_list: List[str] = None) -> List[Entity]:
    """
    Args:
        table_name: 表名
        schema: Spark DataFrame Schema
        primary_list: 主键列表
    Returns:
        List[Entity]
    """
    entities = list()
    for field in schema.fields:
        if primary_list:
            if field.name not in primary_list:
                continue

        entity_name = _get_entity_name(table_name, field.name)
        if isinstance(field.dataType, (TimestampType, DateType)):
            continue
            # entities.append(Entity(name=entity_name, value_type=ValueType.UNIX_TIMESTAMP))
        elif isinstance(field.dataType, IntegerType):
            entities.append(Entity(name=entity_name, value_type=ValueType.INT32))
        elif isinstance(field.dataType, StringType):
            entities.append(Entity(name=entity_name, value_type=ValueType.STRING))
        elif isinstance(field.dataType, (DecimalType, FloatType)):
            entities.append(Entity(name=entity_name, value_type=ValueType.FLOAT))
        elif isinstance(field.dataType, DoubleType):
            entities.append(Entity(name=entity_name, value_type=ValueType.DOUBLE))
        elif isinstance(field.dataType, BooleanType):
            entities.append(Entity(name=entity_name, value_type=ValueType.BOOL))
        elif isinstance(field.dataType, ByteType):
            entities.append(Entity(name=entity_name, value_type=ValueType.BYTES))
        elif isinstance(field.dataType, LongType):
            entities.append(Entity(name=entity_name, value_type=ValueType.INT64))
        elif isinstance(field.dataType, NullType):
            entities.append(Entity(name=entity_name, value_type=ValueType.NULL))
        elif isinstance(field.dataType, ArrayType):
            if isinstance(field.dataType.elementType, ByteType):
                entities.append(Entity(name=entity_name, value_type=ValueType.BYTES_LIST))
            elif isinstance(field.dataType.elementType, StringType):
                entities.append(Entity(name=entity_name, value_type=ValueType.STRING_LIST))
            elif isinstance(field.dataType.elementType, IntegerType):
                entities.append(Entity(name=entity_name, value_type=ValueType.INT32_LIST))
            elif isinstance(field.dataType.elementType, LongType):
                entities.append(Entity(name=entity_name, value_type=ValueType.INT64_LIST))
            elif isinstance(field.dataType.elementType, DoubleType):
                entities.append(Entity(name=entity_name, value_type=ValueType.DOUBLE_LIST))
            elif isinstance(field.dataType.elementType,  (DecimalType, FloatType)):
                entities.append(Entity(name=entity_name, value_type=ValueType.FLOAT_LIST))
            elif isinstance(field.dataType.elementType, BooleanType):
                entities.append(Entity(name=entity_name, value_type=ValueType.BOOL_LIST))
            elif isinstance(field.dataType.elementType, (TimestampType, DateType)):
                continue
                # entities.append(Entity(name=entity_name, value_type=ValueType.UNIX_TIMESTAMP_LIST))
            else:
                print(f"Unsupported array element type: {field.dataType.elementType}")
        else:
            print(f"Unsupported field type: {field.dataType}")

    return entities


def translate_table_name_to_feast(table_name: str):
    splits = table_name.split(".")
    if len(splits) == 1:
        return table_name
    elif len(splits) >= 2:
        # 将表名 database_name.table_name  -> database_name"_"table_name。 因为feast不支持"."字符。
        return "_".join(splits)
    else:
        raise ValueError(f"Invalid table name: {table_name}")


def split_full_table_for_feast(full_table_name: str) -> [str, str]:
    """
    分割拼接的完整表名信息，获取数据库名和表名。因为EMR为两段表达式， DLC为三段表达式。所以这里要做兼容。
    Returns:
        feast_service_name, table_name
    """
    splits = full_table_name.split(".")
    if len(splits) == 2:
        return splits[0], splits[1]
    elif len(splits) > 2:
        feast_service_name = "_".join(splits[0:-1])
        table_name = splits[-1]
        return feast_service_name, table_name
    else:
        # len(splits) == 0 or len(splits) == 1的情况
        raise ValueError(f"Invalid full_table_name:{full_table_name} split_len:{len(splits)}")


def get_materialization_default_time() -> List[Tuple[datetime, datetime]]:
    return [(datetime(1990, 1, 1), datetime(1990, 1, 1))]


# if __name__ == '__main__':
#     import datetime
#     FeastClient = FeastClient()
#     FeastClient.client.registry.delete_data_source(name="xxxxx")
#     FeastClient.client.registry.delete_entity("xxxxx", )
#     FeastClient.client.registry.delete_feature_view()
#     FeastClient.client.registry.get_feature_view()
#     FeastClient.client.registry.delete_feature_service()
#     FeastClient.client.get_historical_features()
#     feature_view = FeastClient.client.get_feature_view(name="xxxxx")
#     feature_view.source.get_table_query_string()
#     feast_table_name = "xxx"
#     from wedata.feature_store.utils.common_utils import build_full_table_name
#     feast_table_name = translate_table_name_to_feast(build_full_table_name(table_name, database_name))
#     FeastClient.client.materialize(start_date=datetime.datetime(2021,1,1), end_date=datetime.datetime.now(), feature_views=[feast_table_name])