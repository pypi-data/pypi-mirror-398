"""Функции для работы с базами данных."""
import logging
import random
import time
import warnings
from typing import Union
from urllib.parse import quote

import pandas as pd
from clickhouse_driver import Client
from pymongo import MongoClient
from sqlalchemy import Engine, create_engine

warnings.filterwarnings("ignore")


def upload_dataframe_to_clickhouse(config: dict, table: str, df: pd.DataFrame) -> None:
    """Функция для загрузки датафрейма в ClickHouse."""
    # подключаемся к Clickhouse
    clickhouse_client = Client(
        host=random.choice(config["CH_HOSTS"].split(",")),
        alt_hosts=config["CH_HOSTS"],
        port="9000",
        database=config["CH_DATABASE"],
        user=config["CH_IMPORT_USERNAME"],
        password=config["CH_IMPORT_PASSWORD"],
        settings={"use_numpy": True},
    )

    clickhouse_client.insert_dataframe(f"INSERT INTO {table} VALUES", df)


def get_clickhouse_connector(config: dict) -> Client:
    """Функция для подключения к ClickHouse."""
    return Client(
        host=random.choice(config["CH_HOSTS"].split(",")),
        alt_hosts=config["CH_HOSTS"],
        port="9000",
        database=config["CH_DATABASE"],
        user=config["CH_USERNAME"],
        password=config["CH_PASSWORD"],
        # settings={'use_numpy': True},
    )


def make_single_query_to_clickhouse(config: dict, query: str) -> pd.DataFrame:
    """Функция для отправки запроса в ClickHouse."""
    # подключаемся к Clickhouse
    clickhouse_client = Client(
        host=random.choice(config["CH_HOSTS"].split(",")),
        alt_hosts=config["CH_HOSTS"],
        port="9000",
        database=config["CH_DATABASE"],
        user=config["CH_USERNAME"],
        password=config["CH_PASSWORD"],
    )

    # получаем ответ на запрос в формате Pandas DataFrame
    result = pd.DataFrame(clickhouse_client.query_dataframe(query))
    return result


def make_query_to_clickhouse(
    logger: logging.Logger, config: dict, query: str, n_attempts: int = 10,
) -> Union[str, pd.DataFrame]:  # noqa: FA100
    """Функция для отправки запроса в ClickHouse с количеством попыток."""
    try:
        return make_single_query_to_clickhouse(config, query)
    except Exception as err:  # noqa: BLE001
        logger.info(f"ClickHouse error: {err}")
        errors = [202, 209, 439]
        caught = False
        for error in errors:
            if str(err).count(f"Code: {error}") != 0:
                caught = True
                break
        if not caught and err != "timed out":
            return "error"
        logger.info("Trying to change the host")
        limit = n_attempts
        while limit != 0:
            try:
                waiting_time = 30 * (n_attempts - limit)
                time.sleep(waiting_time)
                return make_single_query_to_clickhouse(config, query)
            except Exception as e:  # noqa: BLE001, PERF203
                logger.info(f"Clickhouse error again, moving to try number {n_attempts + 1 - limit}: {e}")
                limit -= 1
    return "error"


def get_mysql_connector(config: dict) -> Engine:
    """Функция для получения MYSQL соединения."""
    db_connection_str = (
        f"mysql+pymysql://{config['MYSQL_USERNAME']}:{quote(config['MYSQL_PASSWORD'])}"
        f"@{config['MYSQL_HOSTS']}/{config['MYSQL_MAINDB']}"
    )
    db_connection = create_engine(db_connection_str)
    return db_connection


def make_query_to_mysql(config: dict, query: str) -> pd.DataFrame:
    """Функция для отправки запроса в MYSQL."""
    mysql_connector = get_mysql_connector(config)
    return pd.read_sql(query, con=mysql_connector)


def get_mongo_connector(config: dict) -> MongoClient:
    """Функция для получения соединения с MongoDB."""
    db_connection_str = f"mongodb://{config['MONGO_USERNAME']}:{quote(config['MONGO_PASSWORD'])}@{config['MONGO_HOST']}"
    db_client = MongoClient(host=db_connection_str)
    return db_client
